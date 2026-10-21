# Questionário removed (ESTADO_CIVIL / *_ENSINO_MEDIO): static pages + cadastro persistence + export-full labels
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
CPF = '390.533.447-05'
CPF_DIGITS = '39053344705'
NOME = 'TEST_NOQUEST API'
FD = {'NOME': NOME, 'CPF': CPF, 'EMAIL': 'test_noquest@example.com', 'SEXO': '1',
      'CEP': '01001-000', 'CIDADE': 'São Paulo', 'UF': 'SP', 'CELULAR': '(11) 99999-0000', 'DOC_TIPO': 'RG'}
REMOVED = ('ESTADO_CIVIL', 'TIPO_ENSINO_MEDIO', 'UF_ENSINO_MEDIO', 'ANO_ENSINO_MEDIO')


@pytest.fixture(scope='module')
def admin():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/auth/login", json={'username': 'donas', 'password': 'Seinao10@@'})
    if r.status_code != 200:
        pytest.skip('admin login failed')
    s.headers['Authorization'] = f"Bearer {r.json()['token']}"
    yield s
    for c in (CPF, CPF_DIGITS):
        s.delete(f"{BASE_URL}/api/admin/cadastros/{c}")


# Static pages: questionnaire markup gone
@pytest.mark.parametrize('page', ['inscricao.html', 'confirmacao.html'])
def test_page_has_no_questionario(page):
    r = requests.get(f"{BASE_URL}/{page}")
    assert r.status_code == 200
    html = r.text
    for k in REMOVED:
        assert k not in html, f"{k} still in {page}"
    assert 'questionario-fieldset' not in html
    low = html.lower()
    assert 'estado civil' not in low
    assert 'ensino médio' not in low and 'ensino medio' not in low


def test_track_registration_without_questionario(admin):
    r = requests.post(f"{BASE_URL}/api/track/registration", json={
        'page': '/inscricao.html', 'user_agent': 'pytest',
        'extra': {'nome': NOME, 'cpf': CPF, 'email': FD['EMAIL'], 'stage': 'cadastro',
                  'concurso': 'Vestibular Unesp 2027 - Fundação VUNESP', 'visitor_id': 'v_test_noq', 'form_data': FD}})
    assert r.status_code == 200, r.text
    d = None
    for c in (CPF_DIGITS, CPF):
        rr = admin.get(f"{BASE_URL}/api/admin/cadastros/{c}/details")
        if rr.status_code == 200:
            d = rr.json()
            break
    assert d is not None
    assert NOME in str(d)


def test_export_full_no_removed_labels(admin):
    r = admin.get(f"{BASE_URL}/api/admin/cadastros/export-full.txt", params={'q': NOME})
    assert r.status_code == 200
    txt = r.text
    assert NOME in txt
    for lbl in ('Nome', 'CPF', 'Sexo', 'CEP', 'Cidade', 'E-mail', 'Documento'):
        assert re.search(rf"{lbl}\s*:", txt), f"label {lbl} missing"
    assert 'Feminino' in txt
    for lbl in ('Estado civil', 'Ensino médio', 'Tipo ensino', 'UF ensino', 'Ano ensino'):
        assert lbl.lower() not in txt.lower(), f"removed label {lbl} still in export"


def test_export_full_unfiltered_ok(admin):
    r = admin.get(f"{BASE_URL}/api/admin/cadastros/export-full.txt")
    assert r.status_code == 200
    assert 'CADASTROS COMPLETOS' in r.text


def test_admin_inscriptions_ok(admin):
    r = admin.get(f"{BASE_URL}/api/admin/inscriptions")
    assert r.status_code == 200
