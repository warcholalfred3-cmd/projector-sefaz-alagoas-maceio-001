"""Unit tests for inscricao confirmation email HTML (SEDUC/CE restyling)."""
import os
import re
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email_service import build_inscricao_email_html  # noqa: E402


APP_URL = "https://concurso-seduc-ce.preview.emergentagent.com"


def test_build_inscricao_email_html_contains_seduc_branding():
    h = build_inscricao_email_html(
        nome="AMALIA TESTE",
        cpf="087.578.211-60",
        protocolo="2026000123",
        cargo="12 - Professor de Matemática",
        concurso="x",
        valor=150,
    )
    # Logo URL
    assert f'{APP_URL}/seduc/email-logo.png' in h, "logo URL missing"
    # Title & edital
    assert "Concurso Público da Secretaria da Educação do Estado do Ceará (SEDUC/CE)" in h
    assert "Edital nº 014/2026-SEDUC/SEPLAG" in h
    # Greeting (first name, capitalized)
    assert "Olá, Amalia!" in h
    # Cargo label and code-stripped title
    assert "Cargo:" in h
    assert "Professor de Matemática" in h
    # code prefix must be stripped
    assert ">12 - Professor" not in h
    # Valor BRL
    assert "R$ 150,00" in h
    # Prazo
    assert "15/10/2026, às 23h59" in h
    # Button href with digits-only CPF
    assert f'href="{APP_URL}/pagamento-pix.html?cpf=08757821160"' in h
    # No old branding
    for forbidden in ("Amapá", "SESA", "AOCP"):
        assert forbidden not in h, f"unexpected branding leftover: {forbidden}"


def test_email_logo_asset_served():
    r = requests.get(f"{APP_URL}/seduc/email-logo.png", timeout=15)
    assert r.status_code == 200, f"logo HTTP {r.status_code}"
    ct = r.headers.get("content-type", "")
    assert "image/png" in ct.lower(), f"unexpected content-type: {ct}"
    assert len(r.content) > 100, "image body too small"


def test_cargo_prefix_and_suffix_stripping():
    h = build_inscricao_email_html(
        nome="joao da silva",
        cpf="39053344705",
        protocolo="P1",
        cargo="07 - Professor de Biologia - R$ 150,00",
        concurso="x",
        valor=150,
    )
    # Code prefix and trailing valor suffix stripped
    assert "Professor de Biologia" in h
    assert "07 - Professor" not in h
    assert "- R$ 150,00" not in re.sub(r"<[^>]+>", "", h).split("Cargo:")[1].split("Concurso")[0]
    # First name capitalized
    assert "Olá, Joao!" in h
