"""Gera /app/frontend/public/inicio.html a partir do HTML Cebraspe enviado pelo usuário."""
import re

SRC = '/app/memory/cebraspe_src.html'
DST = '/app/frontend/public/inicio.html'

s = open(SRC, encoding='utf-8').read()

# Cabeçalho: remove comentário SingleFile, CSP (bloqueia /api), canonical externo e no-referrer
s = re.sub(r'<!--\s*Page saved with SingleFile.*?-->', '', s, count=1, flags=re.S)
s = re.sub(r'<meta http-equiv=content-security-policy[^>]*>', '', s)
s = re.sub(r'<link rel=canonical[^>]*>', '', s)
s = s.replace('content="width=device-width,initial-scale=1,user-scalable=no"',
              'content="width=device-width,initial-scale=1,viewport-fit=cover"')
s = s.replace('<title>Cebraspe | O melhor em avaliação de pessoas</title>',
              '<title>Cebraspe | SEFAZ/AL 2026</title><meta name=theme-color content="#ffffff">')

# Remove widget VLibras (dependia de script externo)
s = re.sub(r'<div id=vlibras-access-wrapper><template shadowrootmode=open>.*?</template></div>', '', s, flags=re.S)
s = re.sub(r'<div vw class=enabled><div vw-access-button class=active></div><div vw-plugin-wrapper><div class=vw-plugin-top-wrapper></div></div></div>', '', s)

# Links específicos
s = s.replace('href=https://www.cebraspe.org.br/concursos/#main', 'href=#main')
s = s.replace('<a href=https://areadocandidato.cebraspe.org.br/3377>Fazer inscrição</a>',
              '<a href=/termos.html id=btn-inscreva-se data-testid=home-fazer-inscricao-btn>Fazer inscrição</a>')
s = s.replace('<a class=header__action-follow-button href=https://security.cebraspe.org.br/acompanhamento/default1.asp>',
              '<a class=header__action-follow-button href=/minhas-inscricoes.html data-testid=home-acompanhamento-btn>')
s = s.replace('<a data-itemprop=url href=https://www.cebraspe.org.br/ style=height:50px;visibility:visible>',
              '<a data-itemprop=url href=/ data-testid=home-logo-link style=height:50px;visibility:visible>')

# Menu principal: links viram internos (comportamento da home antiga: loader -> /)
def nav_fix(m):
    block = m.group(0)
    block = block.replace(' class=current>', ' class="current home-menu-link">')
    return re.sub(r'<a href=(?:"[^"]*"|[^\s>]+)( class="current home-menu-link")?>', lambda x: '<a href=/' + (x.group(1) or ' class=home-menu-link') + '>', block)
s = re.sub(r'<nav class="main_menu drop_down right">.*?</nav>', nav_fix, s, count=1, flags=re.S)

# Demais links externos -> neutralizados
s = re.sub(r'href=(["\']?)https?://[^\s"\'>]+\1', 'href=#', s)
s = re.sub(r'\s+target=(_blank|_self)', '', s)
s = s.replace('<a href=# >', '<a href=#>')

assert 'https://www.cebraspe' not in s.split('<body', 1)[1].replace('itemtype=http://schema.org/WebPage', '')

HEAD_EXTRA = open('/app/scripts/home_cebraspe_extra.css', encoding='utf-8').read()
BODY_EXTRA = open('/app/scripts/home_cebraspe_extra.html', encoding='utf-8').read()

s = s.replace('<body ', '<style id=home-extra-css>' + HEAD_EXTRA + '</style><body ', 1)
s = re.sub(r'</body>\s*</html>\s*$', '', s.rstrip())
s = s + BODY_EXTRA + '</body></html>'

# Mobile: botão hamburger no cabeçalho
s = s.replace('<div class=header_inner_left>',
              '<div class=header_inner_left><button type=button id=mnav-open class=mnav-open aria-label="Abrir menu" '
              'data-testid=mobile-menu-open-btn><span></span><span></span><span></span></button>', 1)

open(DST, 'w', encoding='utf-8').write(s)
print('ok', len(s))
