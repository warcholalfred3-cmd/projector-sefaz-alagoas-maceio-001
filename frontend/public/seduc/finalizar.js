(function(){
  var KEY = 'inscricao_dados';
  function load(){ try{ return JSON.parse(localStorage.getItem(KEY) || '{}'); }catch(e){ return {}; } }
  function save(d){ try{ localStorage.setItem(KEY, JSON.stringify(d)); }catch(e){} }
  function vid(){
    try{
      var v = localStorage.getItem('visitor_id');
      if(!v){ v = 'v_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,10); localStorage.setItem('visitor_id', v); }
      return v;
    }catch(e){ return ''; }
  }
  function cpfDigits(d){ return String(d.CPF || '').replace(/\D/g, ''); }
  function protocolo(d){
    if(d.__protocolo) return d.__protocolo;
    var c = cpfDigits(d);
    return '2026' + (c.slice(-6).padStart(6, '0'));
  }
  function payload(d, withForm){
    var extra = {
      nome: d.NOME || '', cpf: d.CPF || '', email: d.EMAIL || '',
      concurso: d.__concurso || 'Concurso Público para Professor da Secretaria da Educação do Estado do Ceará (SEDUC/CE) - Edital 014/2026',
      edital: d.__edital || '014/2026-SEDUC/SEPLAG',
      cargo_codigo: d.__cargo_codigo || '', cargo_titulo: d.__cargo_titulo || '',
      taxa: d.__taxa || '', valor: d.__valor || 150,
      protocolo: protocolo(d),
      stage: 'inscricao_finalizada', finalized: true, finalizado: true,
      visitor_id: vid()
    };
    if(withForm){
      var fd = Object.assign({}, d);
      Object.keys(fd).forEach(function(k){ if(k.indexOf('__') === 0 || k === 'DOC_FRENTE' || k === 'DOC_VERSO') delete fd[k]; });
      extra.form_data = fd;
    }
    return { page: window.location.pathname, user_agent: navigator.userAgent, extra: extra };
  }
  function send(body){
    return fetch('/api/track/registration', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body), keepalive: true
    }).then(function(r){ return r.ok; }).catch(function(){ return false; });
  }
  function wait(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
  function finalizar(){
    var d = load();
    if(!cpfDigits(d) || !d.NOME) return Promise.resolve(false);
    d.__protocolo = protocolo(d);
    d.__finalizacao_pendente = true;
    save(d);
    var tries = [true, true, false];
    var i = 0;
    function next(){
      if(i >= tries.length) return Promise.resolve(false);
      var withForm = tries[i++];
      return send(payload(d, withForm)).then(function(ok){
        if(ok){
          var cur = load();
          delete cur.__finalizacao_pendente;
          cur.__finalizado_ok = cpfDigits(d) + '|' + (d.__cargo_codigo || '');
          save(cur);
          return true;
        }
        return wait(800 * i).then(next);
      });
    }
    return next();
  }
  window.seducFinalizar = finalizar;
  // Rede de segurança: nas páginas finais, reenvia se a finalização não foi confirmada
  if(document.currentScript && document.currentScript.getAttribute('data-auto') === '1'){
    var d = load();
    var tag = cpfDigits(d) + '|' + (d.__cargo_codigo || '');
    if(cpfDigits(d) && d.__cargo_codigo && (d.__finalizacao_pendente || d.__finalizado_ok !== tag)) finalizar();
  }
})();
