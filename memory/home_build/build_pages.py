import re, os, json
PUB = '/app/frontend/public'
BK = '/app/memory/backups/pages_seduc'
home = open(PUB + '/inicio.html', encoding='utf-8').read()

# ---------- assets VUNESP (css, fontes, header, footer) ----------
headpart = home[:home.find('<body')]
css = ''.join(re.findall(r'<style[^>]*>(.*?)</style>', headpart, re.S))
fonts = ''.join(re.findall(r'@font-face\{[^}]*\}', css))
os.makedirs(PUB + '/vunesp', exist_ok=True)
open(PUB + '/vunesp/chrome.css', 'w', encoding='utf-8').write(re.sub(r'@font-face\{[^}]*\}', '', css))
open(PUB + '/vunesp/fonts.css', 'w', encoding='utf-8').write(fonts)
h0 = home.find('<header'); h1 = home.find('</header>') + 9
header = home[h0:h1]
header = header.replace('<a href=# title="Clique aqui para voltar para a home">', '<a href=/ class=vn-home title="Clique aqui para voltar para a home">')
f0 = home.find('<footer id=rodape>'); f1 = home.find('</footer>', f0) + 9
footer = home[f0:f1]
open(PUB + '/vunesp/parts.json', 'w', encoding='utf-8').write(json.dumps({'h': header, 'f': footer}))

# ---------- textos ----------
OLD_CARD = 'Concurso Público de Provas e Títulos para Provimento de Cargos Efetivos de Professor com Lotação em Estabelecimentos de Ensino da Rede Estadual do Ceará, vinculados à Secretaria da Educação do Estado do Ceará (SEDUC).'
NEW_CARD = 'Fundação VUNESP — Vestibular da Universidade Estadual Paulista (Unesp). Inscrições de 04/09 a 20/10/2026, às 23h59.'
REPL = [
    ('SECRETARIA DA EDUCAÇÃO DO ESTADO DO CEARÁ - SEDUC/CE', 'VESTIBULAR | VESTIBULAR UNESP 2027'),
    ('Edital Nº 014/2026-SEDUC/SEPLAG', 'Vestibular Unesp 2027 - VNSP2514'),
    (OLD_CARD, NEW_CARD),
    ('Concurso Público para Professor da Secretaria da Educação do Estado do Ceará (SEDUC/CE) - Edital 014/2026', 'Vestibular Unesp 2027 - Fundação VUNESP'),
    ('Concurso Público SEDUC/CE - Edital Nº 014/2026', 'Vestibular Unesp 2027 - VNSP2514'),
    ('014/2026-SEDUC/SEPLAG', 'VNSP2514'),
    ('Concurso Professor Seduc 2026 | CEV/UECE', 'Vestibular Unesp 2027 | Fundação VUNESP'),
    ('© CEV/UECE — CONCURSO PROFESSOR SEDUC 2026', '© FUNDAÇÃO VUNESP — VESTIBULAR UNESP 2027'),
    ('Concurso Professor Seduc 2026', 'Vestibular Unesp 2027'),
    ("'150.00'", "'225.00'"), ('R$ 150,00', 'R$ 225,00'), ('150,00', '225,00'),
    ('<img src="/seduc/cev-logo.png" alt="CEV/UECE" style="height:56px;', '<img src="/vunesp/vunesp-logo.png" alt="Fundação VUNESP" style="height:48px;'),
    ('CEV/UECE — Concursos Públicos', 'Fundação VUNESP — Vestibulares e Concursos'),
    ('Concurso Público para Professor da Secretaria da Educação do Estado do Ceará', 'Vestibular Unesp 2027'),
    ('Secretaria da Educação do Estado do Ceará (SEDUC/CE)', 'Universidade Estadual Paulista (Unesp) - VNSP2514'),
    ('Cebraspe - Concursos e Seleções com Integridade', 'Fundação VUNESP'),
    ('sac@cebraspe.org.br', 'atendimento@vunesp.com.br'),
    ('/seduc/seduc-theme.js?v=5', '/seduc/seduc-theme.js?v=16'),
    ('/seduc/seduc-theme.css?v=7', '/seduc/seduc-theme.css?v=10'),
    ('#008d3c', '#1172db'), ('#006b2d', '#0b4f9c'), ('#00a84a', '#1172db'), ('#0e2a1a', '#0a2540'),
    ('<option value="1">FEMININO\n </option>', '<option value="1">FEMININO\n </option><option value="2">INTERSEXO</option><option value="3">OUTRO</option><option value="4">PREFIRO NÃO INFORMAR</option>'),
    ("var sexoMap = {'0':'MASCULINO','1':'FEMININO'};", "var sexoMap = {'0':'MASCULINO','1':'FEMININO','2':'INTERSEXO','3':'OUTRO','4':'PREFIRO NÃO INFORMAR'};"),
    ('<b>15/09/2026</b>', '<b>04/09/2026</b>'), ('<b>15/10/2026</b>', '<b>20/10/2026</b>'),
    ('<h2 class="tituloPagina"><span>Formulário de Inscrição</span></h2>\n<form action=""', '<h2 class="tituloPagina"><span>Formulário de Inscrição</span></h2>\n<div class="vn-lgpd" data-testid="lgpd-aviso" style="border:1px solid #ddd;background:#fff;padding:16px 20px;margin:0 0 20px;font-size:14px;line-height:1.6;color:#444;text-align:justify;border-radius:3px">A Fundação VUNESP atende à Lei nº 13.709/18 – Lei Geral de Proteção de Dados Pessoais (LGPD). Seus dados pessoais serão tratados apenas para fins deste vestibular, com proteção à sua liberdade e privacidade, e você pode exercer os direitos previstos no artigo 18 da LGPD.</div>\n<form action=""'),
    ('background:rgba(0,107,45,0.85);z-index:99999;align-items:center;justify-content:center;flex-direction:column;color:#fff;', 'background:rgba(255,255,255,0.88);z-index:99999;align-items:center;justify-content:center;flex-direction:column;color:#333;'),
    ('border:4px solid rgba(255,255,255,0.2);border-top-color:#00a84a;', 'border:4px solid #e5e5e5;border-top-color:#d9534f;'),
    ('#008C00', '#1172db'), ('#0f6a10', '#0b4f9c'), ('#e8f5e9', '#eef5fd'), ('#f4faf6', '#eef5fd'), ('#1f3d2b', '#0b4f9c'), ('#2e7d32', '#1172db'), ('#eef6f0', '#eef5fd'), ('#d5e3da', '#d3e3f6'), ('#eaf6ee', '#e6f0fc'), ('#d9e6dd', '#d3e3f6'),
]
CURSOS = [l.strip() for l in open('/app/memory/cursos/cursos.txt', encoding='utf-8') if l.strip()]
CURSOS_JS = json.dumps([[str(i + 1), c, '225.00'] for i, c in enumerate(CURSOS)], ensure_ascii=False)
PAGES = ['inscricao.html', 'dados-inscricao.html', 'confirmacao.html', 'inscricao-realizada.html', 'pagamento-pix.html', 'minhas-inscricoes.html']
for p in PAGES:
    t = open(BK + '/' + p, encoding='utf-8').read()
    t = re.sub(r'<footer id="aocp-footer" class="seduc-footer".*?</footer>', '', t, flags=re.S)
    for a, b in REPL:
        t = t.replace(a, b)
    if p == 'dados-inscricao.html':
        t = t.replace('</head>', '<style>@media(max-width:767px){html body:not(#vn_a):not(#vn_b) .Miolo{padding-left:8px!important;padding-right:8px!important}html body:not(#vn_a):not(#vn_b) .vn-x,html body:not(#vn_a):not(#vn_b) #pgInformacoes,html body:not(#vn_a):not(#vn_b) .blocoPadrao,html body:not(#vn_a):not(#vn_b) .blocoPadrao .dados{padding-left:0!important;padding-right:0!important;margin-left:0!important;margin-right:0!important}html body:not(#vn_a):not(#vn_b) .blocoPadrao fieldset{padding-left:12px!important;padding-right:12px!important;margin-left:0!important;margin-right:0!important}}</style></head>', 1)
        t = re.sub(r"  var CARGOS=\{\n    '1':\[.*?\]\]\n  \};", lambda m: "  var CARGOS={\n    '1':" + CURSOS_JS + "\n  };", t, count=1, flags=re.S)
        assert CURSOS_JS in t
        CID = ['AMERICANA','ARACATUBA','ARARAQUARA','ASSIS','BAURU','BOTUCATU','BRASILIA','CAMPINAS','CAMPO GRANDE','CURITIBA','DRACENA','FRANCA','GUARATINGUETA','GUARULHOS','ILHA SOLTEIRA','ITAPEVA','JABOTICABAL','JUNDIAI','MARILIA','OURINHOS','PIRACICABA','PRESIDENTE PRUDENTE','REGISTRO','RIBEIRAO PRETO','RIO CLARO','ROSANA','SANTO ANDRE','SAO JOAO DA BOA VISTA','SAO JOSE DO RIO PRETO','SAO JOSE DOS CAMPOS','SAO PAULO','SAO VICENTE','SOROCABA','TUPA','UBERLANDIA']
        UFS = {'BRASILIA': 'DF', 'CAMPO GRANDE': 'MS', 'CURITIBA': 'PR', 'UBERLANDIA': 'MG'}
        opts = ''.join('<option value="%s/%s" data-uf="%s">%s</option>\n' % (c, UFS.get(c, 'SP'), UFS.get(c, 'SP'), c) for c in CID)
        t, n = re.subn(r'<option value="" selected="">Informe a Cidade da Prova</option>\n.*?</select>', lambda m: '<option value="" selected="">Selecione</option>\n' + opts + '</select>', t, count=1, flags=re.S)
        assert n == 1
        t = t.replace('<input type="hidden" id="UF_PROVA" name="UF_PROVA" value="CE">', '<input type="hidden" id="UF_PROVA" name="UF_PROVA" value="SP">')
        t = t.replace("   var uf = document.getElementById('UF_PROVA');\n   if(uf && uf.value !== 'CE'){ uf.value = 'CE'; }", "   var uf = document.getElementById('UF_PROVA'), mp = document.getElementById('MUNICIPIO_PROVA');\n   function syncUf(){ var o = mp && mp.options[mp.selectedIndex]; if(uf) uf.value = (o && o.getAttribute('data-uf')) || 'SP'; }\n   if(mp){ mp.addEventListener('change', syncUf); setTimeout(syncUf, 300); }")
        t = t.replace('<label class="description">Local de Prova</label>', '<label class="description">Cidade de Aplicação da Prova</label>', 1)
        t = t.replace('<label><span class="error">*</span> Cidade de Prova</label>', '<label><span class="error">*</span> Cidade</label>', 1)
        t = t.replace("o0.textContent='Informe o Cargo'", "o0.textContent='Informe o Curso'")
        t = t.replace('<label class="description">Vaga</label>', '<label class="description">Curso</label>', 1)
        t = t.replace('<label><span class="error">*</span> Cargo</label>\n<select class="select" data-testid="select-vaga"', '<label><span class="error">*</span> Curso</label>\n<select class="select" data-testid="select-vaga"', 1)
        a0 = t.index('<div class="fgv-field"><label><span class="error">*</span> Curso</label>\n<select class="select" data-testid="select-vaga"')
        a1 = t.index('</script>', a0) + len('</script>')
        t = t[:a0] + open('/app/memory/home_build/polo_curso.html', encoding='utf-8').read().replace('__CURSOS__', CURSOS_JS) + t[a1:]

    t = re.sub(r'<div class="aec-body"><div class="aec-txt"><strong>Vestibular Unesp 2027 - VNSP2514</strong><br>[^<]*</div></div>', '', t)
    t = re.sub(r'<div class="edbody"><div class="edtxt"><strong>Vestibular Unesp 2027 - VNSP2514</strong><br>[^<]*</div>\s*</div>', '', t)
    m = re.search(r'<div class="aocp-edital-card" data-testid="edital-card"><div class="aec-head"><h3>[^<]*</h3></div></div>', t)
    if m and p != 'confirmacao.html' and '<div class="blocoPadrao"><div class="dados">' in t:
        card = m.group(0)
        t = t[:m.start()] + t[m.end():]
        t = t.replace('<div class="blocoPadrao"><div class="dados">', '<div class="blocoPadrao"><div class="dados">' + card, 1)
    t = t.replace("document.querySelectorAll('.blocoPadrao h3').forEach", "document.querySelectorAll('.blocoPadrao h3:not(.vn-keep)').forEach")
    t = t.replace('.blocoPadrao h3 { display: none !important; }', '.blocoPadrao h3:not(.vn-keep) { display: none !important; }')
    t = t.replace('<div class="aec-head"><h3>VESTIBULAR | VESTIBULAR UNESP 2027</h3>', '<div class="aec-head"><h3 class="vn-keep">VESTIBULAR | VESTIBULAR UNESP 2027</h3>')
    t = t.replace('</head>', '<style>html body .aocp-edital-card{width:auto!important;max-width:none!important;margin-left:0!important;margin-right:0!important;box-sizing:border-box!important}@media(max-width:767px){html body .vn-lgpd{text-align:left!important;padding:12px 14px!important;font-size:13px!important}}</style></head>', 1)
    t = t.replace("({'CE':'Ceará','AP':'Ceará','BA':'Ceará'}[d.UF_PROVA] || d.UF_PROVA || '')", "({'SP':'São Paulo','DF':'Distrito Federal','MS':'Mato Grosso do Sul','PR':'Paraná','MG':'Minas Gerais'}[d.UF_PROVA] || d.UF_PROVA || '')")
    t = t.replace('>Município da Prova<', '>Cidade de Aplicação da Prova<').replace('>Município da Prova:<', '>Cidade de Aplicação da Prova:<')
    t = t.replace('<h3 class="vn-keep">VESTIBULAR | VESTIBULAR UNESP 2027</h3>', '<h3 class="vn-keep">Vestibular Unesp 2027</h3><p class="vn-sub">Universidade Estadual Paulista - UNESP</p>')
    t = re.sub(r'(<div class="edhead">\s*<h3[^>]*>)VESTIBULAR \| VESTIBULAR UNESP 2027(</h3>)', r'\1Vestibular Unesp 2027\2<p class="vn-sub">Universidade Estadual Paulista - UNESP</p>', t)
    t = t.replace('</head>', '<link rel="stylesheet" href="/vunesp/pages.css?v=8"><style>html.vn-wait body{opacity:0!important}html body{transition:opacity .15s ease}</style><script>document.documentElement.classList.add("vn-wait");setTimeout(function(){document.documentElement.classList.remove("vn-wait")},2500);</script></head>', 1)
    t = t.replace('>Vaga Escolhida:<', '>Curso Escolhido:<').replace('>Vaga Escolhida<', '>Curso Escolhido<')
    if p in ('inscricao-realizada.html', 'pagamento-pix.html', 'minhas-inscricoes.html'):
        X = 'html body:not(#vn_a):not(#vn_b) '
        t = t.replace('</head>', '<style>@media(max-width:767px){' + X + '.Miolo,' + X + '.wrap{padding-left:8px!important;padding-right:8px!important;margin-left:0!important;margin-right:0!important;max-width:none!important}' + X + '#pgInformacoes,' + X + '.blocoPadrao .dados,' + X + '#TopoInformacoes{padding-left:0!important;padding-right:0!important;margin-left:0!important;margin-right:0!important}' + X + '.blocoPadrao{padding-left:12px!important;padding-right:12px!important;margin-left:0!important;margin-right:0!important;max-width:none!important}' + X + '.wrap .insc,' + X + '#lista>div{padding-left:14px!important;padding-right:14px!important}}</style></head>', 1)
    if p == 'inscricao-realizada.html':
        t = t.replace("var __v = (!isNaN(__c)) ? ((__c >= 13 && __c <= 15) ? 120 : 160)\n              : (__lbl.indexOf('ASSISTENTE') !== -1 ? 120 : (__lbl.indexOf('ESPECIALISTA') !== -1 ? 160 : null));", "var __v = 225;")
    if p == 'minhas-inscricoes.html':
        t = t.replace('>Vaga<', '>Curso<')
    if p == 'inscricao.html':
        q = open('/app/memory/home_build/questionario.html', encoding='utf-8').read()
        anchor = '<option value="4">PREFIRO NÃO INFORMAR</option>\n</select></div>\n</fieldset>'
        assert anchor in t
        t = t.replace(anchor, anchor + '\n' + q, 1)
        t = t.replace('</head>', '<style>@media(max-width:767px){html body:not(#vn_a):not(#vn_b) .Miolo{padding-left:8px!important;padding-right:8px!important}html body:not(#vn_a):not(#vn_b) .vn-x,html body:not(#vn_a):not(#vn_b) #pgInformacoes,html body:not(#vn_a):not(#vn_b) .blocoPadrao,html body:not(#vn_a):not(#vn_b) .blocoPadrao .dados{padding-left:0!important;padding-right:0!important;margin-left:0!important;margin-right:0!important}html body:not(#vn_a):not(#vn_b) .blocoPadrao fieldset{padding-left:12px!important;padding-right:12px!important;margin-left:0!important;margin-right:0!important}}</style></head>', 1)
        old = "      if(el.type==='checkbox'){ if(!el.checked) ok=false; continue; }"
        assert old in t
        t = t.replace(old, old + "\n      if(el.type==='radio'){ var g=form.querySelector('input[name=\"'+el.name+'\"]:checked'); if(!g) ok=false; continue; }", 1)
        old2 = "            if(el.type === 'checkbox'){"
        assert old2 in t
        t = t.replace(old2, "            if(el.type === 'radio'){ var sv=String(saved[k]||'').toUpperCase(); var rr=Array.prototype.find.call(form.querySelectorAll('input[name=\"'+k+'\"]'), function(r){ return String(r.value).toUpperCase()===sv; }); if(rr){ rr.checked=true; rr.dispatchEvent(new Event('change',{bubbles:true})); } return; }\n" + old2, 1)
        old3 = "el.type==='checkbox' || el.type==='submit') return;"
        assert old3 in t
        t = t.replace(old3, "el.type==='checkbox' || el.type==='radio' || el.type==='submit') return;", 1)
    if p == 'confirmacao.html':
        t = t.replace('</head>', '<style>@media(max-width:767px){html body:not(#vn_a):not(#vn_b) .Miolo{padding-left:8px!important;padding-right:8px!important}html body:not(#vn_a):not(#vn_b) .vn-x,html body:not(#vn_a):not(#vn_b) #pgInformacoes,html body:not(#vn_a):not(#vn_b) .blocoPadrao,html body:not(#vn_a):not(#vn_b) .blocoPadrao .dados{padding-left:0!important;padding-right:0!important;margin-left:0!important;margin-right:0!important}html body:not(#vn_a):not(#vn_b) .blocoPadrao fieldset{padding-left:12px!important;padding-right:12px!important;margin-left:0!important;margin-right:0!important}}</style></head>', 1)
        t = t.replace('</head>', '<style>@media(max-width:767px){html body:not(#vn_a):not(#vn_b) .conf-list{padding-left:12px!important;padding-right:12px!important;margin-left:0!important;margin-right:0!important}html body:not(#vn_a):not(#vn_b) .conf-list .conf-row,html body:not(#vn_a):not(#vn_b) .conf-list .conf-sec{padding-left:4px!important;padding-right:4px!important}}</style></head>', 1)
        row = '<div class="conf-row"><span class="conf-lbl">Sexo</span><span class="conf-val" data-testid="c-sexo" id="c-sexo">—</span></div>'
        assert row in t
        extra_rows = ''.join('<div class="conf-row"><span class="conf-lbl">%s</span><span class="conf-val" data-testid="%s" id="%s">—</span></div>' % (l, i, i) for l, i in [('Estado civil','c-estado-civil'),('Tipo de ensino médio','c-tipo-em'),('Estado do ensino médio','c-uf-em'),('Ano do ensino médio','c-ano-em')])
        t = t.replace(row, row + extra_rows, 1)
        rows = dict((m.group(2), m.group(0)) for m in re.finditer(r'<div class="conf-row"><span class="conf-lbl">([^<]*)</span><span class="conf-val"[^>]*id="([^"]*)">[^<]*</span></div>', t))
        GROUPS = [('Dados da inscrição', ['c-inscricao','c-vaga','c-uf-prova','c-municipio-prova']),
                  ('Dados pessoais', ['c-nome','c-cpf','c-data','c-sexo','c-estado-civil']),
                  ('Ensino médio', ['c-tipo-em','c-uf-em','c-ano-em']),
                  ('Endereço', ['c-cep','c-logradouro','c-numero','c-complemento','c-bairro','c-cidade','c-uf']),
                  ('Contato', ['c-celular','c-email']),
                  ('Documento de identificação', ['c-doc','c-arquivos'])]
        used = [i for g in GROUPS for i in g[1]]
        assert all(i in rows for i in used) and len(rows) == len(used), sorted(set(rows) ^ set(used))
        first = min(t.find(r) for r in rows.values())
        last = max(t.find(r) + len(r) for r in rows.values())
        new = ''.join('<div class="conf-sec" data-testid="conf-sec-%d">%s</div>' % (n, g[0]) + ''.join(rows[i] for i in g[1]) for n, g in enumerate(GROUPS))
        t = t[:first] + new + t[last:]
        t = t.replace('background:rgba(2,20,44,0.85);z-index:99998;', 'background:rgba(255,255,255,0.88);z-index:99998;').replace('border:5px solid rgba(254,191,0,0.25);border-top-color:#febf00;', 'border:5px solid #e5e5e5;border-top-color:#d9534f;')
        t = t.replace('</head>', '<style>html body .conf-list .conf-sec{font:400 18px/1.3 "Helvetica Neue",Helvetica,Arial,sans-serif;color:#31708f;padding:22px 12px 8px;border-bottom:1px solid #e5e5e5;margin-bottom:4px}html body .conf-list .conf-sec:first-child{padding-top:6px}</style></head>', 1)
        t = t.replace("  set('c-sexo', sexoMap[d.SEXO] || '');", "  set('c-sexo', sexoMap[d.SEXO] || '');\n  set('c-estado-civil', d.ESTADO_CIVIL || '');\n  set('c-tipo-em', d.TIPO_ENSINO_MEDIO || '');\n  set('c-uf-em', d.UF_ENSINO_MEDIO || '');\n  set('c-ano-em', d.ANO_ENSINO_MEDIO || '');", 1)

        t = t.replace('</body>', '<style>html body #pgInformacoes{padding-top:0!important}html body #pgInformacoes .blocoPadrao{margin-top:0!important;padding-top:0!important}html body #pgInformacoes .dados{padding-top:0!important}html body #TopoInformacoes{margin-top:0!important}html body #TopoInformacoes>div{padding-top:0!important}</style></body>', 1)
    open(PUB + '/' + p, 'w', encoding='utf-8').write(t)
    left = re.findall(r'(?i)seduc(?!/)|ceará|\bcev\b|uece|professor', re.sub(r'data:[^"\')\s]{100,}', '', t[t.find('<body'):]))
    print(p, 'restante:', len(left), set(x.lower() for x in left))

# ---------- tema (css/js) ----------
c = open(BK + '/seduc-theme.css', encoding='utf-8').read()
for a, b in REPL:
    if a.startswith('#'):
        c = c.replace(a, b)
c = c.replace('#008442', '#1172db')
open(PUB + '/seduc/seduc-theme.css', 'w', encoding='utf-8').write(c)
open(PUB + '/seduc/seduc-theme.js', 'w', encoding='utf-8').write(open('/app/memory/home_build/chrome_loader.js', encoding='utf-8').read())
import shutil; shutil.copy('/app/memory/home_build/pages.css', PUB + '/vunesp/pages.css')
print('ok')
