"""
Regression tests for the PIX valor bug fix (R$120 -> R$180).
Verifies that /api/pix/generate always uses the inscription's real valor
as source of truth, regardless of what the client sends in the payload.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

ADMIN_USER = 'donas'
ADMIN_PASS = 'Seinao10@@'
EXISTING_CPF = '23079653785'   # Value in DB: R$ 180,00
EXPECTED_VALOR = 180.0


@pytest.fixture(scope='module')
def admin_token():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login',
                      json={'username': ADMIN_USER, 'password': ADMIN_PASS}, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()['token']


# ---------- Health ----------
def test_api_root():
    r = requests.get(f'{BASE_URL}/api/', timeout=10)
    assert r.status_code == 200


# ---------- Admin auth ----------
def test_admin_login_ok(admin_token):
    assert isinstance(admin_token, str) and len(admin_token) > 20


def test_admin_login_bad_credentials():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login',
                      json={'username': ADMIN_USER, 'password': 'wrong'}, timeout=10)
    assert r.status_code == 401


# ---------- PIX valor fix (the main bug) ----------
def test_pix_generate_forces_correct_valor_when_client_sends_120():
    """Client sends valor=120 for an inscription that actually costs 180.
    Backend MUST return valor=180 and pix_code must contain '5406180.00'."""
    payload = {'cpf': EXISTING_CPF, 'valor': 120, 'txid': 'TEST120'}
    r = requests.post(f'{BASE_URL}/api/pix/generate', json=payload, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'pix_code' in data
    assert 'qr_png_base64' in data
    assert data.get('valor') == EXPECTED_VALOR, f"backend valor: {data.get('valor')}"
    assert '5406180.00' in data['pix_code'], f"pix_code EMV 54 wrong: {data['pix_code']}"
    assert '5406120.00' not in data['pix_code']


def test_pix_generate_with_correct_valor_180():
    payload = {'cpf': EXISTING_CPF, 'valor': 180, 'txid': 'TEST180'}
    r = requests.post(f'{BASE_URL}/api/pix/generate', json=payload, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert '5406180.00' in data['pix_code']
    assert data.get('valor') == EXPECTED_VALOR


def test_pix_generate_no_valor_defaults_from_inscription():
    """If client omits valor, backend must still use inscription's real valor."""
    payload = {'cpf': EXISTING_CPF, 'txid': 'TESTNULL'}
    r = requests.post(f'{BASE_URL}/api/pix/generate', json=payload, timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert '5406180.00' in data['pix_code']


# ---------- Admin panel reflects correct valor ----------
def test_admin_inscriptions_shows_valor_180(admin_token):
    r = requests.get(f'{BASE_URL}/api/admin/inscriptions',
                     headers={'Authorization': f'Bearer {admin_token}'}, timeout=10)
    assert r.status_code == 200
    body = r.json()
    items = body if isinstance(body, list) else (body.get('items') or body.get('data') or [])
    assert len(items) >= 1
    target = next((i for i in items if str(i.get('cpf')) == EXISTING_CPF), items[0])
    assert float(target.get('valor')) == EXPECTED_VALOR


def test_admin_dashboard_kpis_valor_total_reflects_180(admin_token):
    r = requests.get(f'{BASE_URL}/api/admin/dashboard/kpis',
                     headers={'Authorization': f'Bearer {admin_token}'}, timeout=10)
    assert r.status_code == 200
    kpis = r.json()
    assert 'valor_total' in kpis
    # valor_total must be a multiple of 180 (single inscription for now)
    assert kpis['valor_total'] >= EXPECTED_VALOR
    assert (kpis['valor_total'] % EXPECTED_VALOR) == 0, f"valor_total={kpis['valor_total']} not multiple of 180"
