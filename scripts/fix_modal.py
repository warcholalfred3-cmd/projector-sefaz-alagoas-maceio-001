import os
os.chdir('/app/frontend/public')

# 1) Remover o modal das paginas de edital (mantem o tracking de acesso)
for f in ['edital-especialista.html', 'edital-inspetor.html']:
    d = open(f, encoding='utf-8').read()
    i = d.find('<div id="aviso-modal-overlay"')
    if i >= 0:
        d = d[:i].rstrip() + '\n</body></html>'
        open(f, 'w', encoding='utf-8').write(d)
        print(f, '-> modal removido')
    else:
        print(f, '-> modal nao encontrado')

# 2/3) inicio.html: remover modal feio, adicionar tracking + modal bonito (2 editais)
TRACKER = '''<script id="__ceb_tracker">
(function(){
  try {
    var v = localStorage.getItem('visitor_id');
    if(!v){ v = 'v_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2,10); localStorage.setItem('visitor_id', v); }
    fetch(window.location.origin + '/api/track/access', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ page: window.location.pathname, user_agent: navigator.userAgent, extra: { visitor_id: v } })
    }).catch(function(){});
  } catch(e) {}
})();
</script>'''

MODAL = '''<div id="aviso-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="aviso-modal-title" style="display:none;position:fixed;inset:0;z-index:99999;align-items:center;justify-content:center;padding:20px;background:rgba(20,24,33,.55);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);opacity:0;transition:opacity .28s ease;">
  <div id="aviso-modal-card" style="background:#ffffff;max-width:470px;width:100%;border-radius:22px;padding:38px 32px 34px;text-align:center;box-shadow:0 24px 70px rgba(0,0,0,.28);transform:translateY(14px) scale(.96);opacity:0;transition:transform .34s cubic-bezier(.2,.8,.25,1),opacity .34s ease;font-family:'Poppins',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;">
    <img src="/cebraspe-logo.webp" alt="Cebraspe" style="height:52px;width:auto;display:block;margin:0 auto 18px;" />
    <h2 id="aviso-modal-title" style="margin:0 0 14px;font-size:26px;font-weight:800;color:#d89300;letter-spacing:-.01em;">Aviso importante</h2>
    <p style="margin:0 0 22px;font-size:15.5px;line-height:1.6;color:#3a3f47;">Est&atilde;o abertas as inscri&ccedil;&otilde;es dos concursos p&uacute;blicos da <strong style="color:#2a2a2a;">Secretaria de Estado de Administra&ccedil;&atilde;o Penitenci&aacute;ria do Maranh&atilde;o</strong>:</p>
    <p style="margin:0 0 10px;font-size:15px;line-height:1.55;color:#3a3f47;"><strong style="color:#2a2a2a;">Inspetor e Monitor</strong> &mdash; inscri&ccedil;&otilde;es at&eacute; <strong style="color:#2a2a2a;">31 de agosto de 2026</strong>, &agrave;s 23h59min.</p>
    <p style="margin:0 0 22px;font-size:15px;line-height:1.55;color:#3a3f47;"><strong style="color:#2a2a2a;">Especialista e Assistente</strong> &mdash; inscri&ccedil;&otilde;es at&eacute; <strong style="color:#2a2a2a;">14 de setembro de 2026</strong>, &agrave;s 18h00min.</p>
    <p style="margin:0 0 26px;font-size:12.5px;color:#8a94a0;">Hor&aacute;rio oficial de Bras&iacute;lia/DF.</p>
    <button id="aviso-modal-ok" type="button" style="cursor:pointer;border:none;outline:none;background:#d89300;color:#fff;font-size:16px;font-weight:700;padding:14px 40px;border-radius:999px;box-shadow:0 8px 20px rgba(216,147,0,.38);transition:background-color .2s ease,transform .12s ease,box-shadow .2s ease;">OK, entendi</button>
  </div>
</div>
<script>
(function(){
  try{
    var KEY='aviso_inicio_seap_v2';
    if(sessionStorage.getItem(KEY)==='1') return;
    var ov=document.getElementById('aviso-modal-overlay');
    var card=document.getElementById('aviso-modal-card');
    var btn=document.getElementById('aviso-modal-ok');
    if(!ov||!card||!btn) return;
    function open(){
      ov.style.display='flex';
      requestAnimationFrame(function(){ ov.style.opacity='1'; card.style.transform='translateY(0) scale(1)'; card.style.opacity='1'; });
      document.documentElement.style.overflow='hidden'; document.body.style.overflow='hidden';
    }
    function close(){
      ov.style.opacity='0'; card.style.transform='translateY(14px) scale(.96)'; card.style.opacity='0';
      document.documentElement.style.overflow=''; document.body.style.overflow='';
      setTimeout(function(){ ov.style.display='none'; },300);
      try{ sessionStorage.setItem(KEY,'1'); }catch(e){}
    }
    btn.addEventListener('click',close);
    btn.addEventListener('mouseenter',function(){ btn.style.background='#c07f00'; btn.style.transform='translateY(-1px)'; });
    btn.addEventListener('mouseleave',function(){ btn.style.background='#d89300'; btn.style.transform='translateY(0)'; });
    ov.addEventListener('click',function(e){ if(e.target===ov) close(); });
    document.addEventListener('keydown',function(e){ if(e.key==='Escape') close(); });
    setTimeout(open,600);
  }catch(e){}
})();
</script>'''

d = open('inicio.html', encoding='utf-8').read()
i = d.find('<!-- Modal Aviso Importante -->')
if i >= 0:
    d = d[:i]
d = d.replace('</body>', '').replace('</html>', '').rstrip()
d += '\n' + TRACKER + '\n' + MODAL + '\n</body>\n</html>\n'
open('inicio.html', 'w', encoding='utf-8').write(d)
print('inicio.html -> tracker + modal bonito OK | tem tracker:', '__ceb_tracker' in d, '| modal antigo feio removido:', '#avisoOverlay' not in d)
