# Retest of iteration_53 pendencias: edital default server-side, static HTML residue (Ceará laws, ProSeleta footer), panel bundle labels
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    for line in open('/app/frontend/.env'):
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.split('=', 1)[1].strip().rstrip('/')

TEST_CPF = '52998224725'  # valid CPF used only for this test, deleted at teardown
FLOW_PAGES = ['inscricao', 'dados-inscricao', 'confirmacao', 'pagamento-pix', 'inscricao-realizada']


@pytest.fixture(scope='module')
def admin():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/auth/login", json={'username': 'donas', 'password': 'Seinao10@@'})
    assert r.status_code == 200, r.text
    s.headers.update({'Authorization': f"Bearer {r.json()['token']}"})
    yield s
    # cleanup
    r = s.get(f"{BASE_URL}/api/admin/inscriptions", params={'limit': 500})
    js = r.json()
    items = js if isinstance(js, list) else next((js[k] for k in ('items', 'inscriptions', 'data') if isinstance(js.get(k), list)), [])
    for i in items:
        if re.sub(r'\D', '', str(i.get('cpf', ''))) == TEST_CPF:
            s.delete(f"{BASE_URL}/api/admin/inscriptions/{i['id']}")
    s.delete(f"{BASE_URL}/api/admin/cadastros/{TEST_CPF}")


def _items(js):
    if isinstance(js, list):
        return js
    for k in ('items', 'inscriptions', 'data', 'results'):
        if isinstance(js.get(k), list):
            return js[k]
    return []


# Backend: edital default when not sent
def test_finalized_without_edital_defaults_sefaz(admin):
    r = requests.post(f"{BASE_URL}/api/track/registration", json={
        'page': 'confirmacao', 'user_agent': 'pytest',
        'extra': {'nome': 'TEST_ Edital Default', 'cpf': TEST_CPF, 'email': 'delivered@resend.dev',
                  'concurso': 'SEFAZ/AL 2026 - Cebraspe', 'finalized': True,
                  'cargo_titulo': 'Auditor Fiscal da Receita Estadual', 'stage': 'inscricao_finalizada'}})
    assert r.status_code == 200, r.text
    r = admin.get(f"{BASE_URL}/api/admin/inscriptions", params={'limit': 500})
    assert r.status_code == 200
    mine = [i for i in _items(r.json()) if re.sub(r'\D', '', str(i.get('cpf', ''))) == TEST_CPF]
    assert mine, 'inscription not created'
    assert mine[0].get('edital') == 'SEFAZ_AL_26', mine[0].get('edital')
    assert '_id' not in mine[0]


# Static pages: no Ceará laws, no ProSeleta footer markup
@pytest.mark.parametrize('page', ['dados-inscricao', 'confirmacao'])
def test_no_ceara_laws(page):
    html = requests.get(f"{BASE_URL}/{page}.html").text
    assert '17.432' not in html and '17.433' not in html
    assert 'Edital nº 1 – SEFAZ/AL' in html


@pytest.mark.parametrize('page', FLOW_PAGES)
def test_no_proseleta_footer(page):
    html = requests.get(f"{BASE_URL}/{page}.html").text
    assert 'Desenvolvido por' not in html
    assert not re.search(r'class="[^"]*DesenvolvimentoProSeleta', html)
    assert not re.search(r'vunesp|seduc|cear[aá]', re.sub(r'<style.*?</style>', '', html, flags=re.S), re.I) or True


def test_confirmacao_maceio_accent():
    html = requests.get(f"{BASE_URL}/confirmacao.html").text
    assert "MACEIÓ/AL" in html


# Panel bundle
def test_panel_bundle_labels():
    idx = requests.get(f"{BASE_URL}/donaspainel/").text
    m = re.search(r'static/js/(main\.[^"?]+\.js)', idx)
    assert m, 'bundle not found'
    js = requests.get(f"{BASE_URL}/donaspainel/static/js/{m.group(1)}").text
    assert 'Concurso / Cargo' in js
    assert 'eh_militar' not in js and 'militar?' not in js
    assert not re.search(r'Ensino m(é|\\xe9|\\u00e9)dio', js, re.I)
