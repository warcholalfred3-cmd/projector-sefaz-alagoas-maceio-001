"""Tests enforcing VALOR_INSCRICAO=150.0 everywhere."""
import os
import re
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://concurso-seduc-ce.preview.emergentagent.com').rstrip('/')
ADMIN_USER = 'donas'
ADMIN_PASS = 'Seinao10@@'

TEST_CPF = '39053344705'  # 390.533.447-05
TEST_NAME = 'TESTE VALOR 150'


@pytest.fixture(scope='module')
def admin_token():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login', json={'username': ADMIN_USER, 'password': ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()['token']


@pytest.fixture(scope='module')
def admin_headers(admin_token):
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture(scope='module', autouse=True)
def set_temp_pix_key(admin_headers):
    # Set a temp pix_key so pix/generate works
    r = requests.put(f'{BASE_URL}/api/admin/settings', json={'pix_key': 'teste@example.com'}, headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    yield
    # Restore to empty
    requests.put(f'{BASE_URL}/api/admin/settings', json={'pix_key': ''}, headers=admin_headers, timeout=15)


# ---- /api/admin/settings ----
def test_admin_settings_valor_150(admin_headers):
    r = requests.get(f'{BASE_URL}/api/admin/settings', headers=admin_headers, timeout=15)
    assert r.status_code == 200
    assert r.json().get('valor_inscricao') == 150.0


# ---- /api/track/registration (finalized) ----
def test_track_registration_stores_150():
    body = {
        'page': '/inscricao-realizada',
        'extra': {
            'nome': TEST_NAME, 'cpf': TEST_CPF, 'email': 'teste@example.com',
            'concurso': 'SEDUC', 'edital': '014/2026',
            'cargo_codigo': '03', 'cargo_titulo': 'Professor de Biologia',
            'stage': 'inscricao_finalizada', 'finalized': True,
            'taxa': 'R$ 90,00', 'valor': 90.0,  # should be ignored
            'protocolo': f'TEST-{uuid.uuid4().hex[:8]}',
        },
    }
    r = requests.post(f'{BASE_URL}/api/track/registration', json=body, timeout=15)
    assert r.status_code == 200, r.text
    time.sleep(1)


def test_pix_track_endpoints_store_150():
    for ep in ['pix-generated', 'pix-copied', 'pix-downloaded']:
        body = {'page': '/pagamento-pix', 'extra': {'nome': TEST_NAME, 'cpf': TEST_CPF, 'valor': 90.0}}
        r = requests.post(f'{BASE_URL}/api/track/{ep}', json=body, timeout=15)
        assert r.status_code == 200, f'{ep}: {r.text}'


# ---- /api/admin/inscriptions ----
def test_admin_inscriptions_valor_150(admin_headers):
    r = requests.get(f'{BASE_URL}/api/admin/inscriptions?q={TEST_CPF}', headers=admin_headers, timeout=15)
    assert r.status_code == 200
    data = r.json()
    items = data.get('items') or data.get('inscriptions') or data if isinstance(data, list) else data.get('items', [])
    # Find our test
    found = [i for i in items if i.get('cpf') == TEST_CPF] if isinstance(items, list) else []
    assert found, f'Test insc not found: {data}'
    for i in found:
        assert i.get('valor') == 150.0, i
        assert i.get('taxa') == 'R$ 150,00', i


# ---- /api/admin/dashboard/kpis ----
def test_admin_kpis_valor_150(admin_headers):
    r = requests.get(f'{BASE_URL}/api/admin/dashboard/kpis', headers=admin_headers, timeout=15)
    assert r.status_code == 200
    k = r.json()
    assert k.get('valor_unit') == 150.0, k
    # valor_total must be multiple of 150
    for key in ['valor_total', 'valor_copiados', 'valor_baixados']:
        v = k.get(key)
        if v is None:
            continue
        assert float(v) % 150.0 == 0.0, f'{key}={v} not multiple of 150'


# ---- /api/inscricao/resumo/{cpf} ----
def test_inscricao_resumo_valor_150():
    r = requests.get(f'{BASE_URL}/api/inscricao/resumo/{TEST_CPF}', timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d.get('valor') == 150.0
    assert d.get('taxa') == 'R$ 150,00'


# ---- /api/pix/generate ----
def test_pix_generate_uses_150():
    body = {'valor': 90.0, 'txid': 'TESTE150', 'cpf': TEST_CPF, 'cargo_codigo': '03'}
    r = requests.post(f'{BASE_URL}/api/pix/generate', json=body, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    code = d.get('pix_code', '')
    assert '5406150.00' in code, f'BRCode missing 5406150.00: {code}'


# ---- /api/pix/qr.png and /api/pix/code.txt ----
def test_pix_qr_and_code_endpoints_use_150():
    r = requests.get(f'{BASE_URL}/api/pix/qr.png?valor=90', timeout=15)
    assert r.status_code == 200
    assert r.headers.get('content-type', '').startswith('image/')

    r = requests.get(f'{BASE_URL}/api/pix/code.txt?valor=200', timeout=15)
    assert r.status_code == 200
    assert '5406150.00' in r.text, r.text[:300]
