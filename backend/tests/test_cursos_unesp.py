# Cursos Unesp (183) on dados-inscricao + course persistence/valor 225 in admin inscriptions
import os
import re
import json
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
TEST_CPF = '11144477735'
CURSOS = [l.strip() for l in open('/app/memory/cursos/cursos.txt', encoding='utf-8') if l.strip()]
LONG = 'Música - Bacharelado - Habilitação em Instrumento: Sopros (Clarineta, Flauta, Instrumento Antigo - Flauta Doce, Oboé) - integral - IA/São Paulo'


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


def _cargos_from_page():
    html = requests.get(f'{BASE_URL}/dados-inscricao.html', timeout=20).text
    m = re.search(r"var CARGOS=\{\s*'1':(\[\[.*?\]\])\s*\};", html, re.S)
    assert m, 'CARGOS block not found'
    return html, json.loads(m.group(1))


def test_cursos_count_order_price():
    html, cargos = _cargos_from_page()
    assert len(CURSOS) == 183
    assert [c[1] for c in cargos] == CURSOS
    assert {c[2] for c in cargos} == {'225.00'}
    assert 'Informe o Curso' in html
    assert not any('Professor' in c[1] for c in cargos)


def test_finalize_long_course_persists(hdr):
    for code, title in (('141', LONG), ('178', 'Treineiro')):
        body = {'page': '/confirmacao.html', 'extra': {
            'nome': 'TEST CURSOS', 'cpf': TEST_CPF, 'email': 'teste@example.com',
            'concurso': 'Vestibular Unesp 2027 - Fundação VUNESP', 'edital': 'VNSP2514',
            'cargo_codigo': code, 'cargo_titulo': title, 'taxa': 'R$ 225,00', 'valor': 225,
            'stage': 'inscricao_finalizada', 'finalized': True, 'protocolo': f'TEST-{uuid.uuid4().hex[:6]}'}}
        r = requests.post(f'{BASE_URL}/api/track/registration', json=body, timeout=20)
        assert r.status_code == 200, r.text
    items = requests.get(f'{BASE_URL}/api/admin/inscriptions', params={'q': TEST_CPF}, headers=hdr, timeout=30).json()
    items = items.get('items', items) if isinstance(items, dict) else items
    mine = {i['cargo_codigo']: i for i in items if i.get('cpf') == TEST_CPF}
    assert mine['141']['cargo_titulo'] == LONG
    assert mine['178']['cargo_titulo'] == 'Treineiro'
    assert all(i['valor'] == 225.0 and i['taxa'] == 'R$ 225,00' for i in mine.values())


def test_pix_generate_225_for_course():
    r = requests.post(f'{BASE_URL}/api/pix/generate', json={'valor': 225, 'cpf': TEST_CPF, 'cargo_codigo': '141'}, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json()['valor'] == 225.0
