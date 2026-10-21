"""
PIX BR Code Generator — implementação rigorosa do padrão EMV/BACEN.

Referências:
- Manual BR Code v3.4 (Banco Central):
  https://www.bcb.gov.br/content/estabilidadefinanceira/pix/Regulamento_Pix/IV-ManualdoBRCode.pdf
- CRC16-CCITT (poly 0x1021, init 0xFFFF) — campo 6304
"""
import base64
import io
import re
import unicodedata
from typing import Dict, Optional

import qrcode


# ----------------------- Helpers EMV -----------------------

def _emv(tag: str, value: str) -> str:
    """Formata um campo EMV: ID(2) + tamanho(2) + valor."""
    v = "" if value is None else str(value)
    return f"{tag}{len(v):02d}{v}"


def _ascii(s: str) -> str:
    """Sanitiza string conforme spec BR Code (sem acento, sem cedilha, ASCII printable)."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    only_ascii = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^\x20-\x7E]", "", only_ascii)
    return cleaned.strip()


def _crc16_ccitt(payload: str) -> str:
    """CRC16-CCITT/FALSE — poly 0x1021, init 0xFFFF, sem reflexão."""
    crc = 0xFFFF
    for ch in payload:
        crc ^= (ord(ch) << 8) & 0xFFFF
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


# ----------------------- PIX Builder -----------------------

def _normalize_pix_key(key: str) -> str:
    """Normaliza a chave PIX:
       - CPF/CNPJ: só dígitos
       - Telefone: começa com +55 e só dígitos
       - Email: minúsculas
       - EVP (UUID): mantém como vem
    """
    if not key:
        return ""
    k = key.strip()
    # Email
    if "@" in k:
        return k.lower()
    # EVP (UUID com hifens)
    if re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", k):
        return k.lower()
    # Telefone: começa com +
    if k.startswith("+"):
        digits = re.sub(r"\D", "", k)
        return "+" + digits
    # CPF/CNPJ ou número de telefone sem +: só dígitos
    digits = re.sub(r"\D", "", k)
    if len(digits) == 11 or len(digits) == 14:
        # CPF (11) ou CNPJ (14) → só dígitos
        return digits
    if len(digits) >= 10 and len(digits) <= 13:
        # Telefone sem código de país — assume Brasil
        if not digits.startswith("55"):
            digits = "55" + digits
        return "+" + digits
    return digits or k


def build_brcode(
    pix_key: str,
    valor: float,
    nome_beneficiario: str,
    cidade_beneficiario: str,
    txid: str = "***",
) -> str:
    """Constrói o payload BR Code estático com valor fixo.

    Args:
        pix_key: chave PIX (CPF, CNPJ, email, telefone com +55, ou EVP)
        valor: valor em reais (float, ex: 150.00)
        nome_beneficiario: nome (máx 25 chars ASCII)
        cidade_beneficiario: cidade (máx 15 chars ASCII)
        txid: identificador da transação (máx 25 chars alfanuméricos) ou "***"

    Returns:
        String do payload PIX (BR Code copia e cola)
    """
    key = _normalize_pix_key(pix_key)
    if not key:
        raise ValueError("Chave PIX vazia ou inválida")

    nome = _ascii(nome_beneficiario or "BENEFICIARIO")[:25]
    cidade = _ascii(cidade_beneficiario or "BRASIL")[:15]
    if not nome:
        nome = "BENEFICIARIO"
    if not cidade:
        cidade = "BRASIL"

    # TXID: alfanumérico (a-z, A-Z, 0-9) max 25 chars, mínimo 1.
    # "***" é especial, indica TXID não definido (válido para QR estático).
    if txid and txid != "***":
        txid_clean = re.sub(r"[^A-Za-z0-9]", "", txid)[:25] or "***"
    else:
        txid_clean = "***"

    valor_str = f"{float(valor or 0):.2f}"

    # === Campo 26 — Merchant Account Information (PIX) ===
    # 00: GUI = "br.gov.bcb.pix"
    # 01: chave PIX
    # Atenção: descrição (subtag 02) costuma causar rejeição em alguns bancos —
    # por isso NÃO incluímos aqui. Identificação extra fica no campo 62.05 (txid).
    mai = _emv("00", "br.gov.bcb.pix") + _emv("01", key)
    p26 = _emv("26", mai)

    # === Additional Data Field (campo 62) com TXID (sub-tag 05) ===
    p62 = _emv("62", _emv("05", txid_clean))

    # === Payload completo ===
    payload = (
        _emv("00", "01")    # Payload Format Indicator
        + _emv("01", "11")  # Point of Initiation Method: 11 = estático
        + p26
        + _emv("52", "0000")  # MCC (sem categoria)
        + _emv("53", "986")   # Moeda: 986 = BRL
        + _emv("54", valor_str)  # Valor da transação
        + _emv("58", "BR")    # País
        + _emv("59", nome)    # Nome do beneficiário
        + _emv("60", cidade)  # Cidade do beneficiário
        + p62
    )

    # CRC16 — campo 63, tamanho fixo "04", calculado sobre payload + "6304"
    payload += "6304"
    payload += _crc16_ccitt(payload)
    return payload


def build_qr_png_base64(brcode: str, box_size: int = 8, border: int = 2) -> str:
    """Gera o QR code do BR Code como PNG base64 (pronto para embed em <img>)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(brcode)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#003556", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
