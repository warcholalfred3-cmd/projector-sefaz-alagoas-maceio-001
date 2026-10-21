# Regression: inscricoes.email fallback from form_data.EMAIL + lembrete resumo backfill
import os, time, pytest, requests
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
CPF = '99988877766'


def _db():
    env = dict(l.strip().split('=', 1) for l in open('/app/backend/.env') if '=' in l)
    c = MongoClient(env['MONGO_URL'].strip('"'))
    return c[env['DB_NAME'].strip('"')]


@pytest.fixture(scope='module')
def db():
    d = _db()
    for col in ('inscricoes', 'cadastros', 'registrations'):
        d[col].delete_many({'cpf': CPF})
    yield d
    for col in ('inscricoes', 'cadastros', 'registrations'):
        d[col].delete_many({'cpf': CPF})


@pytest.fixture(scope='module')
def token():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login', json={'username': 'donas', 'password': 'Seinao10@@'})
    assert r.status_code == 200, r.text
    return r.json().get('token') or r.json().get('access_token')


def test_resumo_total(token):
    r = requests.get(f'{BASE_URL}/api/admin/inscricoes/lembrete-pagamento/resumo', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200, r.text
    d = r.json()
    print(d)
    assert d['total'] >= 1


def test_registration_email_fallback(db):
    r1 = requests.post(f'{BASE_URL}/api/track/registration', json={'page': '/seduc/cadastro', 'extra': {
        'cpf': '999.888.777-66', 'nome': 'TEST_Email Fallback', 'stage': 'cadastro',
        'form_data': {'EMAIL': 'delivered@resend.dev', 'NOME': 'TEST_Email Fallback'}}})
    assert r1.status_code == 200, r1.text
    r2 = requests.post(f'{BASE_URL}/api/track/registration', json={'page': '/seduc/finalizar', 'extra': {
        'cpf': '99988877766', 'nome': 'TEST_Email Fallback', 'finalized': True,
        'cargo_codigo': 'TEST01', 'cargo_titulo': 'TEST Cargo'}})
    assert r2.status_code == 200, r2.text
    time.sleep(1)
    ins = db.inscricoes.find_one({'cpf': CPF})
    assert ins is not None
    assert ins['email'] == 'delivered@resend.dev'
    assert db.cadastros.find_one({'cpf': CPF})['email'] == 'delivered@resend.dev'


def test_backfill_empty_email(db, token):
    db.inscricoes.update_many({'cpf': CPF}, {'$set': {'email': ''}})
    r = requests.get(f'{BASE_URL}/api/admin/inscricoes/lembrete-pagamento/resumo', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert db.inscricoes.find_one({'cpf': CPF})['email'] == 'delivered@resend.dev'
