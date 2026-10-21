# SEFAZ/AL residue cleanup regression: admin login, inscription edital/concurso/valor, track/registration fallback
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    for line in open('/app/frontend/.env'):
        if line.startswith('REACT_APP_BACKEND_URL='):
            BASE_URL = line.split('=', 1)[1].strip().rstrip('/')
UI_CPF = os.environ.get('UI_CPF', '01303708515')
BAD = re.compile(r'vunesp|seduc|vestibular|014/2026|cear[aá]', re.I)


@pytest.fixture(scope='module')
def admin():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/auth/login", json={'username': 'donas', 'password': 'Seinao10@@'})
    assert r.status_code == 200, r.text
    tok = r.json()['token']
    s.headers.update({'Authorization': f'Bearer {tok}'})
    return s


def _items(js):
    if isinstance(js, list):
        return js
    for k in ('items', 'inscriptions', 'data', 'results'):
        if isinstance(js.get(k), list):
            return js[k]
    return []


# Admin auth
def test_login_invalid():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login", json={'username': 'donas', 'password': 'x'})
    assert r.status_code in (400, 401)


def test_me(admin):
    r = admin.get(f"{BASE_URL}/api/admin/auth/me")
    assert r.status_code == 200
    assert 'donas' in r.text


# Inscription created by UI flow
def test_ui_inscription_has_sefaz_fields(admin):
    r = admin.get(f"{BASE_URL}/api/admin/inscriptions", params={'limit': 200})
    assert r.status_code == 200
    items = _items(r.json())
    mine = [i for i in items if re.sub(r'\D', '', str(i.get('cpf', ''))) == UI_CPF]
    assert mine, f'UI inscription {UI_CPF} not found'
    i = mine[0]
    print(i)
    assert 'SEFAZ/AL' in str(i.get('concurso', ''))
    assert i.get('edital') == 'SEFAZ_AL_26'
    assert float(i.get('valor') or 0) == 300


def test_no_seduc_edital_in_any_inscription(admin):
    r = admin.get(f"{BASE_URL}/api/admin/inscriptions", params={'limit': 500})
    items = _items(r.json())
    bad = [(i.get('cpf'), i.get('edital'), i.get('concurso')) for i in items
           if BAD.search(str(i.get('edital', '')) + str(i.get('concurso', '')))]
    assert not bad, bad


def test_cadastro_details(admin):
    r = admin.get(f"{BASE_URL}/api/admin/cadastros/{UI_CPF}/details")
    assert r.status_code == 200, r.text
    assert not BAD.search(r.text), BAD.findall(r.text)


def test_resumo_public():
    r = requests.get(f"{BASE_URL}/api/inscricao/resumo/{UI_CPF}")
    assert r.status_code == 200, r.text
    assert not BAD.search(r.text)


