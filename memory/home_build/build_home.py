import re, shutil
src = open('/app/memory/home_build/unesp.html', encoding='utf-8', errors='ignore').read()
pass

s = src
s = re.sub(r'<link rel=canonical[^>]*>', '', s)
s = re.sub(r'<meta http-equiv=content-security-policy[^>]*>', '', s)
def menu(cat):
    items = ['Próximos','Inscrições Abertas','Em Andamento','Encerrados']
    lis = ''.join('<li><a href=/ class=home-menu-link data-testid="menu-%s-%d">%s</a></li>' % (cat, i, t) for i, t in enumerate(items))
    return '<ul class="filter-search__submenu submenu-pai home-submenu" id=submenu-%s>%s</ul>' % (cat, lis)
for cat in ['concurso','vestibular','avaliacao']:
    s = re.sub(r'<ul class="filter-search__submenu submenu-pai sf-hidden" id=submenu-%s>\s*</ul>' % cat, menu(cat), s)
s = re.sub(r'<iframe[^>]*>.*?</iframe>', '', s, flags=re.S)
s = re.sub(r'<iframe[^>]*>', '', s)
s = re.sub(r'<script[^>]*>\s*</script>', '', s)
s = re.sub(r'<!--\[if lte IE 9\]>.*?<!\[endif\]-->', '', s, flags=re.S)
s = re.sub(r'<!--\s*Page saved with SingleFile.*?-->', '', s, flags=re.S)
s = s.replace('<a class=apply-to-it href=https://www.vunesp.com.br/VNSP2514/Inscricao>',
              '<a class=apply-to-it href=/termos.html id=btn-inscreva-se data-testid=home-inscreva-se-btn>')
s = re.sub(r'href=(["\']?)(?:https?:)?//[^"\'\s>]+\1', 'href=#', s)
s = re.sub(r'data-host=https?://[^\s>]+', '', s)
s = s.replace('<form action=/ method=GET class=form-search>', '<form action=# method=GET class=form-search onsubmit="return false">')
s = s.replace('<meta name=viewport content="width=device-width, initial-scale=1, maximum-scale=5">',
              '<meta name=viewport content="width=device-width, initial-scale=1, maximum-scale=5, viewport-fit=cover">'
              '<meta name=format-detection content="telephone=no"><meta name=theme-color content="#ffffff">'
              '<meta name=apple-mobile-web-app-capable content=yes>')

s = s.replace('<div class=course-description>\n <p>\n A Unesp oferece', '<div class=course-description>\n <p data-testid=home-aviso-importante><strong>AVISO IMPORTANTE | VESTIBULAR UNESP 2027</strong><br>O período de inscrições para o Vestibular Unesp 2027 se encerra em 20 de outubro de 2026, às 23h59.<br>Os candidatos interessados devem realizar a inscrição dentro do prazo estabelecido, evitando imprevistos de última hora.<br><strong>Prazo final:</strong> 20/10/2026, às 23h59.</p>\n <p>\n A Unesp oferece', 1)
import json as _j
_docs = _j.load(open('/app/memory/home_build/docs.json', encoding='utf-8'))
_pdf = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><text x="7" y="18" font-size="6" font-family="Arial" fill="#333" stroke="none">PDF</text></svg>'
_rows = ''.join('<li class=vn-doc data-testid="doc-item-%d"><a class=vn-doc-t href="%s" %s data-testid="doc-title-%d">%s</a><span class=vn-doc-r><a class=vn-doc-d href="%s" %s data-testid="doc-date-%d">%s</a><a class=vn-doc-pdf href="%s" %s data-testid="doc-pdf-%d" title="Abrir PDF">%s</a></span></li>' % (i, (u or '#'), ('target=_blank rel=noopener' if u else ''), i, t, (u or '#'), ('target=_blank rel=noopener' if u else ''), i, d, (u or '#'), ('target=_blank rel=noopener' if u else ''), i, _pdf) for i, (t, d, u) in enumerate(_docs))
s = s.replace('<div class="col-xs-12 col-sm-12 col-md-12 course-tabs-content" id=course-tabs-content-VNSP2514>\n \n </div>', '<div class="col-xs-12 col-sm-12 col-md-12 course-tabs-content" id=course-tabs-content-VNSP2514><ul class=vn-docs id=vn-docs data-testid=docs-list style=display:none>' + _rows + '</ul></div>', 1)
s = s.replace('<a  data-controller=projeto data-tabname=documento', '<a  data-controller=projeto data-tabname=documento id=vn-tab-docs data-testid=tab-editais', 1)
extra = open('/app/memory/home_build/home_extra.html', encoding='utf-8').read()
if '</body>' in s:
    s = s.replace('</body>', extra + '</body>', 1)
else:
    s += extra + '</body></html>'
open('/app/frontend/public/inicio.html', 'w', encoding='utf-8').write(s)
print('ok', len(s), 'external left:', set(re.findall(r'(?:href|src|action)=["\']?(https?://[^"\'\s>]+)', s)))

# termos.html: mesmo cabeçalho/rodapé da home
t = s
a = t.find('<section id=conteudoPrincipal>')
b = t.find('<footer id=rodape>')
end = t.rfind('</div>', a, b)
t = t[:a] + open('/app/memory/home_build/termos_main.html', encoding='utf-8').read() + '\n ' + t[end:]
n0 = t.find('<noscript></noscript>')
t = t[:n0] + '<noscript></noscript>\n ' + t[t.find('<section id=conteudoPrincipal>'):]
t = t.replace('<title>Vestibular Unesp 2027 | Universidade Estadual Paulista - UNESP</title>', '<title>Termos de Inscrição | Vestibular Unesp 2027</title>')
open('/app/frontend/public/termos.html', 'w', encoding='utf-8').write(t)
print('termos ok', len(t))
