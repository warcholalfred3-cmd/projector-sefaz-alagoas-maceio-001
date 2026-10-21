"""Backend tests for /api/track/documents and /api/admin/documentos.
Validates the fix where mobile document uploads now reach the admin panel.
"""
import os
import base64
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
ADMIN_USER = 'donas'
ADMIN_PASS = 'Seinao10@@'


def gen_cpf():
    """Gera CPF válido aleatório."""
    import random
    n = [random.randint(0, 9) for _ in range(9)]
    def dv(digits):
        s = sum(d * w for d, w in zip(digits, range(len(digits) + 1, 1, -1)))
        r = s % 11
        return 0 if r < 2 else 11 - r
    d1 = dv(n)
    d2 = dv(n + [d1])
    return ''.join(map(str, n + [d1, d2]))


TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


@pytest.fixture(scope='module')
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login",
                      json={'username': ADMIN_USER, 'password': ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    tok = r.json().get('token')
    assert tok
    return tok


@pytest.fixture(scope='module')
def test_cpf():
    return gen_cpf()


def test_track_documents_saves_docs(test_cpf):
    """POST /api/track/documents deve salvar frente+verso e retornar ok:true."""
    payload = {
        'cpf': test_cpf,
        'doc_tipo': 'RG',
        'doc_frente': TINY_PNG_B64,
        'doc_verso': TINY_PNG_B64,
    }
    r = requests.post(f"{BASE_URL}/api/track/documents", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get('ok') is True, data


def test_admin_documentos_lists_new_cpf(admin_token, test_cpf):
    """GET /api/admin/documentos deve listar o CPF recém-criado com has_frente e has_verso."""
    h = {'Authorization': f'Bearer {admin_token}'}
    r = requests.get(f"{BASE_URL}/api/admin/documentos", headers=h, params={'q': test_cpf}, timeout=15)
    assert r.status_code == 200, r.text
    items = r.json().get('items', [])
    match = [i for i in items if i.get('cpf') == test_cpf]
    assert match, f"CPF {test_cpf} não encontrado em /admin/documentos. items={items[:3]}"
    it = match[0]
    assert it.get('has_frente') is True
    assert it.get('has_verso') is True
    assert it.get('doc_tipo') == 'RG'


def test_admin_documento_arquivo_returns_image(admin_token, test_cpf):
    """GET /api/admin/documentos/{cpf}/frente deve devolver a imagem base64 salva."""
    r = requests.get(f"{BASE_URL}/api/admin/documentos/{test_cpf}/frente",
                     params={'token': admin_token}, timeout=15)
    assert r.status_code == 200, r.text
    # Endpoint returns image bytes
    assert len(r.content) > 0


def test_track_documents_empty_cpf_fails():
    r = requests.post(f"{BASE_URL}/api/track/documents",
                      json={'cpf': '', 'doc_frente': TINY_PNG_B64}, timeout=15)
    assert r.status_code == 200
    assert r.json().get('ok') is False
