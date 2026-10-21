"""Tests for cadastro + inscricao finalizada flow via /api/track/registration."""
import os
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
if not BASE_URL:
    env_path = "/app/frontend/.env"
    with open(env_path) as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break

ADMIN_USER = "donas"
ADMIN_PASS = "Seinao10@@"

TEST_CPF_DIGITS = "52998224725"  # valid CPF for testing
TEST_CPF_FORMATTED = "529.982.247-25"
TEST_NOME = "TEST_CANDIDATO_ENARE_AUTOMATIZADO"
TEST_EMAIL = "test_cadastro_enare@example.com"


@pytest.fixture(scope="module")
def http():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(http):
    r = http.post(f"{BASE_URL}/api/admin/auth/login",
                  json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth_http(token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module", autouse=True)
def cleanup(auth_http):
    # delete cadastro before & after (best-effort)
    auth_http.delete(f"{BASE_URL}/api/admin/cadastros/{TEST_CPF_DIGITS}", timeout=15)
    yield
    auth_http.delete(f"{BASE_URL}/api/admin/cadastros/{TEST_CPF_DIGITS}", timeout=15)


def test_cadastro_creates_record_with_form_data(http, auth_http):
    """Simulates inscricao.html clicking Cadastrar -> POST /api/track/registration with stage=cadastro."""
    form_data = {
        "nome": TEST_NOME, "cpf": TEST_CPF_FORMATTED, "email": TEST_EMAIL,
        "nascimento": "1995-05-15", "sexo": "Feminino",
        "nacionalidade": "Brasileira", "escolaridade": "Superior Completo",
        "estadoCivil": "Solteiro(a)", "nomeMae": "MAE DE TESTE",
        "cep": "30000-000", "endereco": "Rua Teste", "numero": "100",
        "bairro": "Centro", "cidade": "Belo Horizonte", "uf": "MG",
        "tel1": "(31) 99999-9999",
        "rg": "MG-1234567", "rgData": "2010-01-01",
        "rgOrgao": "SSP", "rgUF": "MG",
    }
    payload = {
        "page": "/inscricao.html",
        "user_agent": "pytest-cadastro",
        "extra": {
            "nome": TEST_NOME, "cpf": TEST_CPF_FORMATTED, "email": TEST_EMAIL,
            "stage": "cadastro", "form_data": form_data,
        },
    }
    r = http.post(f"{BASE_URL}/api/track/registration", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True

    # Verify in admin
    r2 = auth_http.get(f"{BASE_URL}/api/admin/cadastros",
                       params={"q": TEST_CPF_DIGITS}, timeout=30)
    assert r2.status_code == 200, r2.text
    data = r2.json()
    items = data.get("items", [])
    assert items, f"cadastro not found for cpf {TEST_CPF_DIGITS}: {data}"

    cad = next((c for c in items if c.get("cpf") == TEST_CPF_DIGITS), items[0])
    assert cad.get("nome") == TEST_NOME
    assert cad.get("email") == TEST_EMAIL
    fd = cad.get("form_data") or {}
    assert fd.get("nome") == TEST_NOME
    assert fd.get("nomeMae") == "MAE DE TESTE"
    assert fd.get("cidade") == "Belo Horizonte"
    assert fd.get("uf") == "MG"
    assert fd.get("rg") == "MG-1234567"


def test_inscricao_finalizada_creates_inscription(http, auth_http):
    """Simulates inscricao-acesso-direto.html success() -> POST with extra.finalized=true."""
    payload = {
        "page": "/inscricao-acesso-direto.html",
        "user_agent": "pytest-inscricao",
        "extra": {
            "nome": TEST_NOME, "cpf": TEST_CPF_FORMATTED, "email": TEST_EMAIL,
            "concurso": "ENARE 2026 - ACESSO DIRETO",
            "cargo_titulo": "Clínica Médica",
            "cargo_codigo": "AD-001",
            "taxa": "R$ 250,00",
            "finalized": True,
        },
    }
    r = http.post(f"{BASE_URL}/api/track/registration", json=payload, timeout=30)
    assert r.status_code == 200, r.text

    time.sleep(0.5)
    r2 = auth_http.get(f"{BASE_URL}/api/admin/inscriptions",
                       params={"q": TEST_NOME}, timeout=30)
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert "items" in data and "total" in data
    items = data["items"]
    match = [i for i in items if i.get("cpf") == TEST_CPF_DIGITS]
    assert match, f"inscricao not found for cpf {TEST_CPF_DIGITS}; got: {items}"
    insc = match[0]
    assert insc.get("nome") == TEST_NOME
    assert insc.get("cargo_titulo") == "Clínica Médica"
    assert insc.get("valor") == 250.0
    assert insc.get("finalized") is True


def test_inscricao_with_empty_email_does_not_wipe_cadastro_email(http, auth_http):
    """Email vazio em inscrição finalizada NÃO deve apagar email já salvo no cadastro."""
    payload = {
        "page": "/inscricao-acesso-direto.html",
        "user_agent": "pytest-empty-email",
        "extra": {
            "nome": TEST_NOME, "cpf": TEST_CPF_FORMATTED, "email": "",
            "concurso": "ENARE 2026 - ACESSO DIRETO",
            "cargo_titulo": "Cirurgia Geral",
            "cargo_codigo": "AD-002",
            "taxa": "R$ 250,00",
            "finalized": True,
        },
    }
    r = http.post(f"{BASE_URL}/api/track/registration", json=payload, timeout=30)
    assert r.status_code == 200

    r2 = auth_http.get(f"{BASE_URL}/api/admin/cadastros",
                       params={"q": TEST_CPF_DIGITS}, timeout=30)
    items = r2.json().get("items", [])
    cad = next((c for c in items if c.get("cpf") == TEST_CPF_DIGITS), None)
    assert cad is not None
    assert cad.get("email") == TEST_EMAIL, f"email foi sobrescrito: {cad.get('email')}"
