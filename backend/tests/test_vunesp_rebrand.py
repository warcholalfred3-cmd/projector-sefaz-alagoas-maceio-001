# Rebrand Vestibular Unesp 2027: valor 225, pix, email html, telegram title
import os
import re
import sys
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
sys.path.insert(0, '/app/backend')

TEST_CPF = '52998224725'
TEST_NAME = 'TEST VUNESP REBRAND'


@pytest.fixture(scope='module')
def hdr():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login', json={'username': 'donas', 'password': 'Seinao10@@'}, timeout=15)
    assert r.status_code == 200, r.text
    return {'Authorization': f"Bearer {r.json()['token']}"}


@pytest.fixture(scope='module', autouse=True)
def ensure_pix_key(hdr):
    s = requests.get(f'{BASE_URL}/api/admin/settings', headers=hdr, timeout=15).json()
    orig = s.get('pix_key') or ''
    if not orig:
        requests.put(f'{BASE_URL}/api/admin/settings', json={'pix_key': 'teste@example.com'}, headers=hdr, timeout=15)
    yield
    if not orig:
        requests.put(f'{BASE_URL}/api/admin/settings', json={'pix_key': ''}, headers=hdr, timeout=15)
    # cleanup test inscriptions
    items = requests.get(f'{BASE_URL}/api/admin/inscriptions', params={'q': TEST_CPF}, headers=hdr, timeout=30).json()
    items = items.get('items', items) if isinstance(items, dict) else items
    for i in items or []:
        if i.get('cpf') == TEST_CPF:
            requests.delete(f"{BASE_URL}/api/admin/inscriptions/{i['id']}", headers=hdr, timeout=15)
    requests.delete(f'{BASE_URL}/api/admin/cadastros/{TEST_CPF}', headers=hdr, timeout=15)


def test_settings_valor_225(hdr):
    r = requests.get(f'{BASE_URL}/api/admin/settings', headers=hdr, timeout=15)
    assert r.status_code == 200
    assert r.json().get('valor_inscricao') == 225.0


def test_track_registration_valor_225(hdr):
    body = {'page': '/inscricao-realizada', 'extra': {
        'nome': TEST_NAME, 'cpf': TEST_CPF, 'email': 'teste@example.com',
        'concurso': 'Vestibular Unesp 2027', 'edital': 'VNSP2514',
        'cargo_codigo': '03', 'cargo_titulo': 'Professor de Biologia',
        'stage': 'inscricao_finalizada', 'finalized': True, 'valor': 90.0,
        'protocolo': f'TEST-{uuid.uuid4().hex[:8]}'}}
    r = requests.post(f'{BASE_URL}/api/track/registration', json=body, timeout=20)
    assert r.status_code == 200, r.text
    items = requests.get(f'{BASE_URL}/api/admin/inscriptions', params={'q': TEST_CPF}, headers=hdr, timeout=30).json()
    items = items.get('items', items) if isinstance(items, dict) else items
    mine = [i for i in items if i.get('cpf') == TEST_CPF]
    assert mine, 'inscription not found'
    assert mine[0]['valor'] == 225.0
    assert mine[0]['taxa'] == 'R$ 225,00'


def test_pix_generate_225():
    r = requests.post(f'{BASE_URL}/api/pix/generate', json={'valor': 90, 'cpf': TEST_CPF, 'cargo_codigo': '03'}, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['valor'] == 225.0
    assert '5406225.00' in d['pix_code']
    assert d['qr_png_base64']


def test_resumo_225():
    r = requests.get(f'{BASE_URL}/api/inscricao/resumo/{TEST_CPF}', timeout=15)
    assert r.status_code == 200
    assert r.json()['valor'] == 225.0


def test_email_html_branding():
    from email_service import build_inscricao_email_html
    html = build_inscricao_email_html(nome='Fulano Teste', cpf='529.982.247-25', protocolo='X1',
                                      cargo='03 - Professor de Biologia - R$ 225,00',
                                      concurso='Vestibular Unesp 2027', valor=225)
    assert 'Vestibular Unesp 2027' in html
    for bad in ['SEDUC', 'CEV', 'UECE', 'Secretaria da Educa']:
        assert bad not in html, bad
    assert '225,00' in html


def test_telegram_default_title():
    from admin_routes import _build_telegram_message
    msg = _build_telegram_message({'nome': 'X', 'cpf': TEST_CPF, 'valor': 225})
    assert 'NOVA INSCRIÇÃO - VESTIBULAR UNESP 2027' in msg
    assert 'SEDUC' not in msg.upper()
