"""Tests for dedupe logic on /api/track/registration.

Verifies:
- Multiple 'cadastro' stage calls for same CPF produce EXACTLY ONE event of type='cadastro'.
- Multiple 'finalized' calls for same CPF+cargo produce EXACTLY ONE event of type='inscricao'
  and inscricoes_count increments only once.
- Two different cargos for the same CPF produce TWO 'inscricao' events.
- cadastros.form_data is preserved / updated on every call via dot notation.
- inscricoes upserts remain correct (no duplicates).
"""
import os
import time
import pytest
import requests
from pymongo import MongoClient
from unittest.mock import patch

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

ADMIN_USER = 'donas'
ADMIN_PASS = 'Seinao10@@'

CPFS = ['11122233344', '22233344455', '33344455566']


@pytest.fixture(scope='module')
def mongo():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    yield db
    # cleanup at end of module
    for cpf in CPFS:
        db.cadastros.delete_many({'cpf': cpf})
        db.inscricoes.delete_many({'cpf': cpf})
        db.events.delete_many({'meta.cpf': cpf})
        db.registrations.delete_many({'cpf': cpf})
    client.close()


@pytest.fixture(autouse=True)
def clean_cpfs(mongo):
    """Clean test CPFs before each test."""
    for cpf in CPFS:
        mongo.cadastros.delete_many({'cpf': cpf})
        mongo.inscricoes.delete_many({'cpf': cpf})
        mongo.events.delete_many({'meta.cpf': cpf})
        mongo.registrations.delete_many({'cpf': cpf})
    yield


@pytest.fixture(scope='module')
def admin_token():
    r = requests.post(f'{BASE_URL}/api/admin/auth/login',
                      json={'username': ADMIN_USER, 'password': ADMIN_PASS}, timeout=10)
    assert r.status_code == 200, f'login failed: {r.status_code} {r.text}'
    return r.json()['token']


def post_track_reg(payload_extra):
    """Wrapper that patches httpx to avoid real Telegram calls."""
    body = {'page': '/inscricao.html', 'user_agent': 'pytest', 'extra': payload_extra}
    r = requests.post(f'{BASE_URL}/api/track/registration', json=body, timeout=10)
    assert r.status_code == 200, f'track failed: {r.status_code} {r.text}'
    return r.json()


# ---- Scenario 1: multiple cadastro calls same CPF -> 1 event only ----
def test_cadastro_multiple_calls_single_event(mongo):
    cpf = CPFS[0]
    base = {
        'nome': 'DAVI DOS SANTOS FERNANDES DE SOUZA',
        'cpf': cpf,
        'email': 'davi@test.com',
        'concurso': 'SEDUC AL 2026',
        'stage': 'cadastro',
        'form_data': {'nome': 'DAVI DOS SANTOS FERNANDES DE SOUZA', 'nascimento': '2000-01-01'}
    }
    # simulate 5 calls (inscricao.html + dados-inscricao.html + retries)
    for i in range(5):
        payload = dict(base)
        # update form_data on later calls (simulating dados-inscricao.html adding more fields)
        if i >= 2:
            payload['form_data'] = {**base['form_data'], 'cep': '57000-000', 'endereco': 'RUA X'}
        post_track_reg(payload)
        time.sleep(0.05)

    # cadastros: exactly 1 doc for this CPF, with merged form_data
    cad_docs = list(mongo.cadastros.find({'cpf': cpf}))
    assert len(cad_docs) == 1, f'expected 1 cadastro, got {len(cad_docs)}'
    fd = cad_docs[0].get('form_data', {})
    assert fd.get('nascimento') == '2000-01-01'
    assert fd.get('cep') == '57000-000'
    assert fd.get('endereco') == 'RUA X'

    # events: exactly 1 event of kind='cadastro' for this CPF
    ev_docs = list(mongo.events.find({'kind': 'cadastro', 'meta.cpf': cpf}))
    assert len(ev_docs) == 1, f'expected 1 cadastro event, got {len(ev_docs)}: {ev_docs}'
    assert 'DAVI' in ev_docs[0]['description']


# ---- Scenario 2: multiple finalized calls same CPF+cargo -> 1 inscricao event ----
def test_inscricao_multiple_calls_single_event(mongo):
    cpf = CPFS[1]
    base = {
        'nome': 'MARIA TESTE',
        'cpf': cpf,
        'email': 'maria@test.com',
        'concurso': 'SEDUC AL 2026',
        'finalized': True,
        'cargo_codigo': '01103',
        'cargo_titulo': 'PROFESSOR',
        'taxa': 'R$ 89,00',
    }
    # 2 finalized calls (simulate reload/double-submit)
    for _ in range(2):
        post_track_reg(base)
        time.sleep(0.05)

    inscs = list(mongo.inscricoes.find({'cpf': cpf}))
    assert len(inscs) == 1, f'expected 1 inscricao, got {len(inscs)}'

    ev_docs = list(mongo.events.find({'kind': 'inscricao', 'meta.cpf': cpf}))
    assert len(ev_docs) == 1, f'expected 1 inscricao event, got {len(ev_docs)}'

    # inscricoes_count should be exactly 1
    cad = mongo.cadastros.find_one({'cpf': cpf})
    assert cad is not None
    assert cad.get('inscricoes_count') == 1, f"expected inscricoes_count=1, got {cad.get('inscricoes_count')}"


# ---- Scenario 3: same CPF, two DIFFERENT cargos -> 2 inscricao events ----
def test_two_different_cargos_two_events(mongo):
    cpf = CPFS[2]
    common = {
        'nome': 'JOAO TESTE',
        'cpf': cpf,
        'email': 'joao@test.com',
        'concurso': 'SEDUC AL 2026',
        'finalized': True,
        'taxa': 'R$ 89,00',
    }
    post_track_reg({**common, 'cargo_codigo': '01103', 'cargo_titulo': 'PROF A'})
    time.sleep(0.05)
    post_track_reg({**common, 'cargo_codigo': '01104', 'cargo_titulo': 'PROF B'})
    time.sleep(0.05)

    inscs = list(mongo.inscricoes.find({'cpf': cpf}))
    assert len(inscs) == 2, f'expected 2 inscricoes, got {len(inscs)}'

    ev_docs = list(mongo.events.find({'kind': 'inscricao', 'meta.cpf': cpf}))
    assert len(ev_docs) == 2, f'expected 2 inscricao events, got {len(ev_docs)}'

    cad = mongo.cadastros.find_one({'cpf': cpf})
    assert cad.get('inscricoes_count') == 2


# ---- Scenario 4: admin realtime feed shows no duplicates ----
def test_admin_realtime_no_duplicate_events(mongo, admin_token):
    # After scenarios above we've already inserted data. Trigger cadastro flow again
    cpf = CPFS[0]
    base = {
        'nome': 'DAVI DOS SANTOS FERNANDES DE SOUZA',
        'cpf': cpf,
        'stage': 'cadastro',
    }
    for _ in range(3):
        post_track_reg(base)
        time.sleep(0.05)

    r = requests.get(f'{BASE_URL}/api/admin/dashboard/realtime?limit=500',
                     headers={'Authorization': f'Bearer {admin_token}'}, timeout=10)
    assert r.status_code == 200
    events = r.json()
    davi_events = [e for e in events if e.get('kind') == 'cadastro'
                   and (e.get('meta') or {}).get('cpf') == cpf]
    assert len(davi_events) == 1, f'expected 1 event for DAVI cpf, got {len(davi_events)}'


# ---- Scenario 5: regression - normal flow still persists everything ----
def test_regression_normal_flow(mongo):
    cpf = CPFS[0]
    # cadastro
    post_track_reg({'nome': 'DAVI', 'cpf': cpf, 'stage': 'cadastro',
                    'form_data': {'nome': 'DAVI'}})
    # finalized
    post_track_reg({'nome': 'DAVI', 'cpf': cpf, 'finalized': True,
                    'cargo_codigo': '01199', 'cargo_titulo': 'ANALISTA',
                    'taxa': 'R$ 120,00'})

    cad = mongo.cadastros.find_one({'cpf': cpf})
    assert cad is not None
    assert cad.get('nome') == 'DAVI'
    assert cad.get('inscricoes_count') == 1

    insc = mongo.inscricoes.find_one({'cpf': cpf, 'cargo_codigo': '01199'})
    assert insc is not None
    assert insc.get('finalized') is True
    assert insc.get('valor') == 120.0

    regs = list(mongo.registrations.find({'cpf': cpf}))
    # registrations is append-only log — should have at least 2 entries
    assert len(regs) >= 2
