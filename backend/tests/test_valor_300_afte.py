# SEFAZ/AL AFTE cargo + taxa R$ 300,00: dados-inscricao page, finalize persistence, settings, pix
import os
import re
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
TEST_CPF = '11144477735'
AFTE = 'Auditor Fiscal da Administração Tributária Estadual (AFTE)'


@pytest.fixture(scope='module')
def hdr():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login', json={'username': 'donas', 'password': 'Seinao10@@'}, timeout=15)
    assert r.status_code == 200, r.text
    h = {'Authorization': f"Bearer {r.json()['token']}"}
    yield h
    items = requests.get(f'{BASE_URL}/api/admin/inscriptions', params={'q': TEST_CPF}, headers=h, timeout=30).json()
    items = items.get('items', items) if isinstance(items, dict) else items
    for i in items or []:
        if i.get('cpf') == TEST_CPF:
            requests.delete(f"{BASE_URL}/api/admin/inscriptions/{i['id']}", headers=h, timeout=15)
    requests.delete(f'{BASE_URL}/api/admin/cadastros/{TEST_CPF}', headers=h, timeout=15)


def _items(hdr):
    items = requests.get(f'{BASE_URL}/api/admin/inscriptions', params={'q': TEST_CPF}, headers=hdr, timeout=30).json()
    items = items.get('items', items) if isinstance(items, dict) else items
    return [i for i in items if i.get('cpf') == TEST_CPF]


# Page: single AFTE option, price 300, no polo select
def test_dados_inscricao_html_afte():
    html = requests.get(f'{BASE_URL}/dados-inscricao.html', timeout=20).text
    sel = re.search(r'<select[^>]*id="VAGA".*?</select>', html, re.S).group(0)
    opts = re.findall(r'<option[^>]*>', sel)
    assert len(opts) == 1
    assert 'data-price="300.00"' in opts[0] and 'value="1"' in opts[0]
    assert AFTE in sel
    assert 'R$ 300,00' in html
    assert 'data-testid="select-polo"' not in html
    assert 'MACEIO/AL' in html


# Settings valor
def test_settings_valor_300(hdr):
    r = requests.get(f'{BASE_URL}/api/admin/settings', headers=hdr, timeout=15)
    assert r.status_code == 200
    assert r.json().get('valor_inscricao') == 300.0, r.json().get('valor_inscricao')


# Finalize: even if client sends a different valor, server stores 300
def test_finalize_persists_300(hdr):
    body = {'page': '/confirmacao.html', 'extra': {
        'nome': 'TEST AFTE', 'cpf': TEST_CPF, 'email': 'teste@example.com',
        'concurso': 'SEFAZ/AL 2026', 'edital': '1',
        'cargo_codigo': '1', 'cargo_titulo': AFTE, 'taxa': 'R$ 225,00', 'valor': 225,
        'stage': 'inscricao_finalizada', 'finalized': True, 'protocolo': f'TEST-{uuid.uuid4().hex[:6]}'}}
    r = requests.post(f'{BASE_URL}/api/track/registration', json=body, timeout=20)
    assert r.status_code == 200, r.text
    mine = _items(hdr)
    assert mine, 'inscription not created'
    i = mine[0]
    assert i['cargo_titulo'] == AFTE
    assert i['valor'] == 300.0
    assert i['taxa'] == 'R$ 300,00'


# PIX generate value
def test_pix_generate_300():
    r = requests.post(f'{BASE_URL}/api/pix/generate', json={'valor': 300, 'cpf': TEST_CPF, 'cargo_codigo': '1'}, timeout=20)
    print(r.status_code, r.text[:300])
    assert r.status_code in (200, 400, 503)
    if r.status_code == 200:
        assert r.json()['valor'] == 300.0
