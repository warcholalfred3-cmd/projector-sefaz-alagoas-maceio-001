# Cebraspe header/footer applied to all public pages + concurso info (SEFAZ/AL 2026)
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
FORM_PAGES = ['inscricao', 'dados-inscricao', 'confirmacao', 'inscricao-realizada', 'pagamento-pix', 'minhas-inscricoes']


def visible_text(html):
    html = re.sub(r'<script\b.*?</script>', ' ', html, flags=re.S | re.I)
    html = re.sub(r'<style\b.*?</style>', ' ', html, flags=re.S | re.I)
    html = re.sub(r'<!--.*?-->', ' ', html, flags=re.S)
    html = html.replace('Vestibular e outros acessos', '')  # legit Cebraspe menu item
    return re.sub(r'<[^>]+>', ' ', html)


# Generated chrome assets
class TestChromeAssets:
    def test_parts_json(self):
        r = requests.get(f"{BASE_URL}/cebraspe/parts.json", timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in ('cls', 'h', 'f'):
            assert k in d and d[k]
        for s in ['header-minhas-inscricoes-desktop-btn', 'header-hamburger-btn', 'mnav', 'Institucional',
                  'Concursos', 'Avaliações', 'Certificações', 'Educação']:
            assert s in d['h'], s
        assert '<footer' in d['f']

    def test_css_assets(self):
        for p in ['/cebraspe/chrome.css', '/cebraspe/fonts.css', '/seduc/seduc-theme.js']:
            r = requests.get(f"{BASE_URL}{p}", timeout=20)
            assert r.status_code == 200 and len(r.text) > 100, p
        assert '00385e' in requests.get(f"{BASE_URL}/cebraspe/chrome.css", timeout=20).text.lower()

    def test_no_external_links_in_parts(self):
        d = requests.get(f"{BASE_URL}/cebraspe/parts.json", timeout=20).json()
        hrefs = re.findall(r'href=("[^"]*"|\'[^\']*\'|[^\s>]+)', d['h'] + d['f'])
        ext = [h for h in hrefs if re.match(r'["\']?(https?:)?//', h)]
        assert ext == [], ext


# Form pages: theme script, titles, concurso texts
class TestFormPages:
    @pytest.mark.parametrize('p', FORM_PAGES)
    def test_page(self, p):
        r = requests.get(f"{BASE_URL}/{p}.html", timeout=30)
        assert r.status_code == 200
        t = r.text
        assert 'seduc-theme.js?v=17' in t
        title = re.search(r'<title>(.*?)</title>', t, re.S).group(1)
        assert title.strip().endswith('| Cebraspe'), title
        vt = visible_text(t)
        bad = re.findall(r'(?i)[^\n]{0,30}(?:vunesp|unesp|vestibular)[^\n]{0,30}', vt)
        assert bad == [], bad

    def test_inscricao_edital_card(self):
        t = requests.get(f"{BASE_URL}/inscricao.html", timeout=30).text
        assert 'SEFAZ/AL 2026' in t and 'Secretaria de Estado da Fazenda de Alagoas' in t
        assert '17/09/2026' in t and '21/10/2026' in t
        assert 'O Cebraspe atende' in t

    def test_dados_option(self):
        t = requests.get(f"{BASE_URL}/dados-inscricao.html", timeout=30).text
        assert 'SEFAZ/AL 2026 - Edital nº 1' in t

    def test_termos(self):
        t = requests.get(f"{BASE_URL}/termos.html", timeout=30).text
        assert 'btn-continuar-termos' in t and 'termos-checkbox' in t
        assert re.search(r'<title>[^<]*\| Cebraspe</title>', t)
        assert 'mobile-menu-open-btn' in t
        bad = re.findall(r'(?i)[^\n]{0,30}(?:vunesp|unesp|vestibular)[^\n]{0,30}', visible_text(t))
        assert bad == [], bad
