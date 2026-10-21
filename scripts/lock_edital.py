import os
os.chdir('/app/frontend/public')

# 1) Cada pagina de edital grava qual edital foi escolhido
setter = {
    'edital-inspetor.html': '1',
    'edital-especialista.html': '2',
}
for f, E in setter.items():
    d = open(f, encoding='utf-8').read()
    if 'edital_escolhido' in d:
        print(f, '-> ja tem setter'); continue
    snippet = ("<script>try{sessionStorage.setItem('edital_escolhido','%s');}"
               "catch(e){}</script>" % E)
    d = d.replace('</body></html>', snippet + '\n</body></html>')
    open(f, 'w', encoding='utf-8').write(d)
    print(f, '-> setter edital', E, 'adicionado')

# 2) dados-inscricao.html: travar edital escolhido e mostrar so as vagas dele
f = 'dados-inscricao.html'
d = open(f, encoding='utf-8').read()
old = """    tipo.addEventListener('change', function(){ fill(); });
    try{
      var saved=JSON.parse(sessionStorage.getItem('inscricao_dados')||'{}');
      if(saved && saved.VAGA){ tipo.value=(['01','02'].indexOf(saved.VAGA)>=0?'1':'2'); fill(saved.VAGA); }
    }catch(e){}"""
new = """    tipo.addEventListener('change', function(){ fill(); });
    var forced=null;
    try{ forced=sessionStorage.getItem('edital_escolhido'); }catch(e){}
    var done=false;
    try{
      var saved=JSON.parse(sessionStorage.getItem('inscricao_dados')||'{}');
      if(saved && saved.VAGA){ tipo.value=(['01','02'].indexOf(saved.VAGA)>=0?'1':'2'); fill(saved.VAGA); done=true; }
    }catch(e){}
    if(!done && (forced==='1'||forced==='2')){ tipo.value=forced; fill(); }
    // Se veio de um edital especifico, trava o edital (mostra so as vagas dele)
    if(forced==='1'||forced==='2'){
      tipo.value=forced; tipo.disabled=true; tipo.style.background='#f1f3f6'; tipo.style.cursor='not-allowed';
    }"""
if old in d:
    d = d.replace(old, new)
    open(f, 'w', encoding='utf-8').write(d)
    print(f, '-> init travando edital OK')
else:
    print(f, '-> BLOCO init NAO encontrado (verificar manualmente)')
