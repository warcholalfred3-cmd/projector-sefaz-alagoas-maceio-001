#!/usr/bin/env python3
"""Semeia 300 inscrições realistas (SAEB BA / Polícia Civil) espalhadas em ~10 min.
Mistura desktop/mobile, os 3 cargos e 4 comportamentos de funil de PIX."""
import random, time, uuid, json, sys
import urllib.request

BASE = "http://localhost:8001"
TOTAL = 300
SPREAD_SECONDS = 600  # ~10 min
LOG = "/app/seed.log"

FIRST_M = ["João","Pedro","Lucas","Gabriel","Rafael","Matheus","Bruno","Felipe","Rodrigo","Thiago",
           "Carlos","Marcos","Paulo","André","Diego","Vinícius","Gustavo","Leonardo","Fernando","Daniel",
           "Ricardo","Eduardo","Antônio","José","Luiz","Caio","Renato","Fábio","Igor","Wesley"]
FIRST_F = ["Maria","Ana","Juliana","Fernanda","Camila","Larissa","Beatriz","Amanda","Patrícia","Aline",
           "Bruna","Carla","Débora","Gabriela","Isabela","Jéssica","Letícia","Mariana","Natália","Priscila",
           "Rafaela","Sabrina","Tatiane","Vanessa","Vitória","Bianca","Elaine","Simone","Cláudia","Luana"]
SURNAMES = ["Silva","Santos","Oliveira","Souza","Lima","Pereira","Ferreira","Costa","Rodrigues","Almeida",
            "Nascimento","Carvalho","Araújo","Ribeiro","Gomes","Martins","Rocha","Barbosa","Cardoso","Teixeira",
            "Moraes","Freitas","Cavalcante","Dias","Correia","Pinto","Moreira","Cunha","Andrade","Nunes"]

CIDADES_BA = [("Salvador","BA"),("Feira de Santana","BA"),("Vitória da Conquista","BA"),("Camaçari","BA"),
              ("Itabuna","BA"),("Juazeiro","BA"),("Lauro de Freitas","BA"),("Ilhéus","BA"),("Jequié","BA"),
              ("Teixeira de Freitas","BA"),("Barreiras","BA"),("Alagoinhas","BA"),("Porto Seguro","BA"),
              ("Simões Filho","BA"),("Paulo Afonso","BA"),("Eunápolis","BA"),("Santo Antônio de Jesus","BA"),
              ("Valença","BA"),("Candeias","BA"),("Guanambi","BA")]

CARGOS = [
    {"codigo":"DELEGADO","titulo":"Delegado de Polícia Civil","valor":220.00},
    {"codigo":"ESCRIVAO","titulo":"Escrivão de Polícia Civil","valor":190.00},
    {"codigo":"INVESTIGADOR","titulo":"Investigador de Polícia Civil","valor":190.00},
]
BEHAVIORS = ["gera","gera_copia","gera_baixa","gera_baixa_copia"]

UA_MOBILE = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Moto G(60)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
]
UA_DESKTOP = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

def gen_cpf():
    n = [random.randint(0,9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(n)+1-i)*v for i,v in enumerate(n))
        d = (s*10) % 11
        n.append(0 if d==10 else d)
    return "".join(map(str,n))

def fmt_cpf(c):
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

def rand_br_ip():
    prefixes = [177,179,186,187,189,191,200,201]
    return f"{random.choice(prefixes)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def post(path, payload, ua, ip):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE+path, data=data, method="POST")
    req.add_header("Content-Type","application/json")
    req.add_header("User-Agent", ua)
    req.add_header("X-Forwarded-For", ip)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except Exception as e:
        log(f"ERR {path}: {e}")
        return None

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}\n"
    with open(LOG,"a") as f:
        f.write(line)

def main():
    open(LOG,"w").write("")
    log(f"START seeding {TOTAL} inscrições em ~{SPREAD_SECONDS}s")
    counts = {"mobile":0,"desktop":0,"gera":0,"gera_copia":0,"gera_baixa":0,"gera_baixa_copia":0}
    per = SPREAD_SECONDS/float(TOTAL)
    for i in range(1, TOTAL+1):
        is_female = random.random() < 0.5
        first = random.choice(FIRST_F if is_female else FIRST_M)
        nome = f"{first} {random.choice(SURNAMES)} {random.choice(SURNAMES)}"
        cpf = gen_cpf()
        email = f"{first.lower()}.{random.randint(100,9999)}@{random.choice(['gmail.com','hotmail.com','outlook.com','yahoo.com.br'])}"
        cidade, uf = random.choice(CIDADES_BA)
        mobile = random.random() < 0.55
        ua = random.choice(UA_MOBILE if mobile else UA_DESKTOP)
        ip = rand_br_ip()
        cargo = random.choice(CARGOS)
        behavior = random.choice(BEHAVIORS)
        taxa_str = f"R$ {cargo['valor']:.2f}".replace(".",",")
        protocolo = f"{random.randint(2026000000,2026999999)}"
        telefone = f"(71) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        nasc = f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{random.randint(1975,2004)}"
        cep = f"{random.randint(40000,48999)}-{random.randint(100,999)}"
        rg = f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}"

        form_data = {
            "nome": nome, "cpf": fmt_cpf(cpf), "email": email, "telefone": telefone,
            "nascimento": nasc, "sexo": "FEMININO" if is_female else "MASCULINO",
            "rg": rg, "orgao_expedidor": "SSP/BA", "nome_mae": f"{random.choice(FIRST_F)} {random.choice(SURNAMES)}",
            "cep": cep, "endereco": f"Rua {random.choice(SURNAMES)}", "numero": str(random.randint(1,2000)),
            "bairro": random.choice(["Centro","Barra","Pituba","Itapuã","Brotas","Liberdade","Cabula"]),
            "cidade": cidade, "uf": uf, "doc_tipo": "RG",
        }
        extra_base = {
            "nome": nome, "cpf": fmt_cpf(cpf), "email": email,
            "concurso": "Concurso Público da Polícia Civil do Estado da Bahia",
            "edital": "EDITAL 002/2026",
            "cargo_codigo": cargo["codigo"], "cargo_titulo": cargo["titulo"],
            "codigo": cargo["codigo"], "titulo": cargo["titulo"],
            "secretaria": "SAEB - Secretaria de Administração do Estado da Bahia",
            "valor": cargo["valor"], "taxa": taxa_str,
            "protocolo": protocolo, "localidade": "SALVADOR/BA",
        }

        # 1) acesso
        post("/api/track/access", {"page":"/inicio.html","extra":{"visitor_id":str(uuid.uuid4()),"city":cidade,"uf":uf}}, ua, ip)
        time.sleep(0.15)
        # 2) inscrição finalizada
        reg = dict(extra_base); reg["stage"]="inscricao_finalizada"; reg["finalized"]=True; reg["form_data"]=form_data
        post("/api/track/registration", {"page":"/confirmacao.html","user_agent":ua,"extra":reg}, ua, ip)
        time.sleep(0.15)
        # 3) PIX gerado (todos)
        post("/api/track/pix-generated", {"page":"/pagamento-pix.html","user_agent":ua,"extra":extra_base}, ua, ip)
        time.sleep(0.1)
        # 4) comportamentos
        if behavior in ("gera_copia","gera_baixa_copia"):
            post("/api/track/pix-copied", {"page":"/pagamento-pix.html","user_agent":ua,"extra":extra_base}, ua, ip)
            time.sleep(0.1)
        if behavior in ("gera_baixa","gera_baixa_copia"):
            post("/api/track/pix-downloaded", {"page":"/pagamento-pix.html","user_agent":ua,"extra":extra_base}, ua, ip)
            time.sleep(0.1)

        counts["mobile" if mobile else "desktop"] += 1
        counts[behavior] = counts.get(behavior,0) + 1
        if i % 20 == 0:
            log(f"{i}/{TOTAL} | {counts}")
        time.sleep(max(0.0, per - 0.6))
    log(f"DONE {TOTAL} | {counts}")

if __name__ == "__main__":
    main()
