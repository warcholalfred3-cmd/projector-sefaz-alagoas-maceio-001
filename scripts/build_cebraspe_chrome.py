"""Gera cabeçalho/rodapé Cebraspe (shadow DOM) para as páginas internas + termos.html."""
import json
import os
import re

PUB = '/app/frontend/public'
home = open(f'{PUB}/inicio.html', encoding='utf-8').read()
os.makedirs(f'{PUB}/cebraspe', exist_ok=True)

# ---- CSS ----
styles = re.findall(r'<style(?: id=([\w-]+))?>(.*?)</style>', home, re.S)
css_all = '\n'.join(c for sid, c in styles if sid != 'home-extra-css')
fonts = re.findall(r'@font-face\{[^}]*\}', css_all)
css = re.sub(r'@font-face\{[^}]*\}', '', css_all)
css = css.replace(':root{', ':host{')
css = re.sub(r'(?<![\w-])body(?=[\s.#:\[,{>])', '.sfbody', css)
css = re.sub(r'(?<![\w-])html(?=[\s.#:\[,{>])', ':host', css)
extra = open('/app/scripts/cebraspe_chrome_extra.css', encoding='utf-8').read()
open(f'{PUB}/cebraspe/fonts.css', 'w', encoding='utf-8').write('\n'.join(fonts))
open(f'{PUB}/cebraspe/chrome.css', 'w', encoding='utf-8').write(css + '\n' + extra)

# ---- HTML ----
body_cls = re.search(r'<body id=dotNetReactApplication class="([^"]*)"', home).group(1)
header = re.search(r'<header .*?</header>', home, re.S).group(0)
footer = re.search(r'<footer>.*?</footer>', home, re.S).group(0)
drawer = re.search(r'<div id=mnav-backdrop.*?</aside>', home, re.S).group(0)
header = header.replace('data-testid=home-acompanhamento-btn', 'data-testid=header-minhas-inscricoes-desktop-btn')
header = header.replace('data-testid=mobile-menu-open-btn', 'data-testid=header-hamburger-btn')
drawer = drawer.replace('data-testid=mobile-menu-acompanhamento-btn', 'data-testid=header-minhas-inscricoes-btn')
drawer = drawer.replace('class="c1 js-inscricao"', 'class=c1')
parts = {
    'cls': body_cls,
    'h': header + drawer,
    'f': footer,
}
json.dump(parts, open(f'{PUB}/cebraspe/parts.json', 'w', encoding='utf-8'), ensure_ascii=False)

# ---- termos.html (layout Cebraspe completo) ----
termos = open('/app/scripts/termos_content.html', encoding='utf-8').read()
page = re.sub(r'<div id=main class="content_inner no_animation">.*?(?=<footer>)',
              lambda m: '<div id=main class="content_inner no_animation">' + termos + '</div></div>',
              home, count=1, flags=re.S)
page = page.replace('<title>Cebraspe | SEFAZ/AL 2026</title>', '<title>Termos de Inscrição - SEFAZ/AL 2026 | Cebraspe</title>')
page = page.replace('class="current home-menu-link"', 'class="current home-menu-link"')
open(f'{PUB}/termos.html', 'w', encoding='utf-8').write(page)
print('ok', len(css), len(fonts), len(parts['h']), len(parts['f']), len(page))
