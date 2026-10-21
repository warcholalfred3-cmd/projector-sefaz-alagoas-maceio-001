import os, sys, uuid, random, base64, io, datetime as dt
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path('/app/backend')
load_dotenv(ROOT / '.env')
client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

random.seed(2026)
N = 150

# ---------------- Dados realistas (pt-BR) ----------------
PRIMEIROS_M = ["Lucas","Gabriel","Matheus","Rafael","Bruno","Felipe","Thiago","Gustavo","Vinicius","Leonardo",
    "Daniel","Rodrigo","Eduardo","Marcos","Paulo","Carlos","Fernando","André","Diego","Ricardo",
    "João","Pedro","José","Antônio","Francisco","Luiz","Marcelo","Guilherme","Fábio","Alexandre"]
PRIMEIROS_F = ["Maria","Ana","Juliana","Fernanda","Camila","Beatriz","Larissa","Amanda","Patrícia","Aline",
    "Bruna","Carolina","Vanessa","Letícia","Gabriela","Mariana","Rafaela","Bianca","Débora","Sabrina",
    "Priscila","Renata","Tatiane","Jéssica","Natália","Isabela","Cristiane","Adriana","Luana","Sara"]
SOBRENOMES = ["Silva","Santos","Oliveira","Souza","Lima","Pereira","Costa","Carvalho","Almeida","Ferreira",
    "Rodrigues","Gomes","Martins","Araújo","Barbosa","Ribeiro","Nascimento","Moreira","Cavalcante","Melo",
    "Cardoso","Teixeira","Correia","Dias","Moura","Freitas","Rocha","Mendes","Nunes","Ramos",
    "Vieira","Monteiro","Campos","Cunha","Pinto","Reis","Aragão","Fonseca","Duarte","Machado"]

CIDADES_MA = [("São Luís","MA"),("Imperatriz","MA"),("São José de Ribamar","MA"),("Timon","MA"),
    ("Caxias","MA"),("Codó","MA"),("Paço do Lumiar","MA"),("Açailândia","MA"),("Bacabal","MA"),
    ("Balsas","MA"),("Santa Inês","MA"),("Barra do Corda","MA"),("Pinheiro","MA"),("Chapadinha","MA"),
    ("Buriticupu","MA"),("Coroatá","MA"),("Grajaú","MA"),("Pedreiras","MA"),("Estreito","MA"),("Viana","MA")]

CARGOS = [
    ("01","Inspetor de Polícia Penal",150.00),
    ("02","Monitor de Ressocialização",85.00),
    ("03","Especialidade: Assistência Social",180.00),
    ("04","Especialidade: Direito",180.00),
    ("05","Especialidade: Enfermagem",180.00),
    ("06","Especialidade: Pedagogia",180.00),
    ("07","Especialidade: Psicologia",180.00),
    ("08","Especialidade: Técnico Administrativo",120.00),
    ("09","Especialidade: Técnico de Enfermagem",120.00),
]

UA_DESKTOP = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]
UA_MOBILE = [
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
]

def gen_cpf():
    n = [random.randint(0,9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(n)+1-i)*v for i,v in enumerate(n))
        d = (s*10) % 11
        n.append(0 if d==10 else d)
    return ''.join(map(str,n))

def fmt_cpf(c):
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

# ---------------- Fotos reais (retratos) ----------------
def fetch_portraits():
    import requests
    pool = []
    genders = [("men", i) for i in range(0,60)] + [("women", i) for i in range(0,60)]
    random.shuffle(genders)
    for g,i in genders:
        if len(pool) >= 80:
            break
        url = f"https://randomuser.me/api/portraits/med/{g}/{i}.jpg"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200 and r.content:
                b64 = base64.b64encode(r.content).decode()
                pool.append((g, "data:image/jpeg;base64," + b64))
        except Exception:
            pass
    return pool

def pil_fallback(seed_text, gender):
    from PIL import Image, ImageDraw
    random.seed(hash(seed_text) & 0xffffff)
    bg = tuple(random.randint(60,200) for _ in range(3))
    img = Image.new("RGB",(200,200),bg)
    d = ImageDraw.Draw(img)
    initials = ''.join([w[0] for w in seed_text.split()[:2]]).upper()
    d.ellipse((50,40,150,140), fill=(255,255,255))
    d.text((85,80), initials, fill=(40,40,40))
    d.rectangle((40,150,160,175), fill=(255,255,255))
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=70)
    return ("men" if gender=="M" else "women"), "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

print("Baixando retratos reais (randomuser.me)...")
PORTRAITS = fetch_portraits()
print(f"  {len(PORTRAITS)} retratos obtidos.")
use_fallback = len(PORTRAITS) < 10
if use_fallback:
    print("  Poucos retratos: usando fallback PIL para os faltantes.")

CONCURSO = "Concurso Público da Secretaria de Estado de Administração Penitenciária do Maranhão (SEAP_MA_26)"
EDITAL = "001/2026-SEAP-MA"

now = dt.datetime.now(dt.timezone.utc)

def rand_ts():
    # distribui nos últimos 7 dias, mais concentrado nos recentes
    day = int(random.triangular(0,6,0))
    return now - dt.timedelta(days=day, hours=random.randint(0,23), minutes=random.randint(0,59), seconds=random.randint(0,59))

used_cpf = set()
counts = {"desktop":0,"mobile":0}
cargo_counts = {}

# limpa dados de seed anteriores? Não — apenas adiciona. (Para evitar duplicar em re-run, marcamos seeded=True)
inserted = 0
for idx in range(N):
    gender = random.choice(["M","F"])
    nome = f"{random.choice(PRIMEIROS_M if gender=='M' else PRIMEIROS_F)} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"
    cpf = gen_cpf()
    while cpf in used_cpf:
        cpf = gen_cpf()
    used_cpf.add(cpf)
    first = nome.split()[0].lower()
    email = f"{first}.{cpf[:4]}@{random.choice(['gmail.com','hotmail.com','outlook.com','yahoo.com.br'])}"
    cidade, uf = random.choice(CIDADES_MA)
    device = "mobile" if idx % 2 == 0 else "desktop"
    counts[device]+=1
    ua = random.choice(UA_MOBILE if device=="mobile" else UA_DESKTOP)
    cod, titulo, valor = random.choice(CARGOS)
    cargo_counts[titulo] = cargo_counts.get(titulo,0)+1
    taxa = "R$ " + f"{valor:,.2f}".replace(",","_").replace(".",",").replace("_",".")
    protocolo = "2026" + str(random.randint(100000,999999))
    nasc = f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{random.randint(1975,2004)}"
    cep = f"{random.randint(65000,65999):05d}-{random.randint(0,999):03d}"
    ts = rand_ts()

    # fotos
    if PORTRAITS:
        g, frente = random.choice(PORTRAITS)
        _, verso = random.choice(PORTRAITS)
    else:
        _, frente = pil_fallback(nome, gender)
        _, verso = pil_fallback(nome+" v", gender)
    doc_tipo = random.choice(["RG","CNH"])

    # ---- cadastro ----
    form_data = {
        "NOME": nome, "CPF": fmt_cpf(cpf), "EMAIL": email,
        "DATA_NASCIMENTO": nasc, "SEXO": "0" if gender=="M" else "1",
        "CEP": cep, "LOGRADOURO": f"Rua {random.choice(SOBRENOMES)}", "NUMERO": str(random.randint(1,999)),
        "BAIRRO": random.choice(["Centro","Cohama","Turu","Renascença","Angelim","Cohatrac","Vinhais","Calhau"]),
        "MUNICIPIO": cidade, "UF": uf,
        "VAGA": cod, "UF_PROVA":"MA", "MUNICIPIO_PROVA":"São Luís / MA",
        "doc_tipo": doc_tipo, "doc_frente": frente, "doc_verso": verso,
        "DOC_FRENTE_NAME": f"{doc_tipo.lower()}_frente.jpg", "DOC_VERSO_NAME": f"{doc_tipo.lower()}_verso.jpg",
    }
    db.cadastros.update_one(
        {"cpf": cpf},
        {"$set": {"nome":nome,"cpf":cpf,"email":email,"last_concurso":CONCURSO,"last_at":ts,
                  "seeded":True, **{f"form_data.{k}":v for k,v in form_data.items()}},
         "$setOnInsert": {"created_at":ts,"inscricoes_count":1}},
        upsert=True,
    )

    # ---- inscricao ----
    insc = {
        "id": str(uuid.uuid4()), "nome":nome, "cpf":cpf, "email":email,
        "concurso":CONCURSO, "edital":EDITAL,
        "cargo_codigo":cod, "cargo_titulo":titulo, "jornada":"", "secretaria":"SEAP-MA",
        "valor":valor, "taxa":taxa, "protocolo":protocolo, "localidade":f"{cidade}/{uf}",
        "finalized":True, "finalized_at":ts, "created_at":ts,
        "pix_status":"Aguardando pagamento", "pix_status_at":ts,
        "user_agent":ua, "device":device, "city":cidade, "uf":uf, "region_name":"Maranhão",
        "seeded":True,
    }
    db.inscricoes.update_one({"cpf":cpf,"cargo_codigo":cod},
        {"$set":{k:v for k,v in insc.items() if k not in ("id","created_at")},
         "$setOnInsert":{"id":insc["id"],"created_at":ts}}, upsert=True)

    # ---- feed event ----
    db.events.insert_one({"kind":"inscricao","description":f"Inscrição realizada - {nome}",
        "meta":{"nome":nome,"cpf":cpf,"device":device,"location":f"{cidade}/{uf}"},
        "created_at":ts,"seeded":True})

    # ---- registrations (compat p/ gráfico de atividade) ----
    db.registrations.insert_one({"nome":nome,"cpf":cpf,"concurso":CONCURSO,"stage":"inscricao_finalizada",
        "created_at":ts,"seeded":True})

    # ---- access do próprio inscrito ----
    db.accesses.insert_one({"page":"/","user_agent":ua,"ip":f"177.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "visitor_id":str(uuid.uuid4()),"city":cidade,"uf":uf,"region_name":"Maranhão","country":"Brazil",
        "country_code":"BR","lat":None,"lon":None,"device":device,"created_at":ts,"seeded":True})
    inserted += 1

# ---- acessos extras (visitantes que não converteram) p/ funil realista ----
extra = 220
for _ in range(extra):
    cidade, uf = random.choice(CIDADES_MA)
    device = random.choice(["mobile","desktop"])
    ua = random.choice(UA_MOBILE if device=="mobile" else UA_DESKTOP)
    ts = rand_ts()
    db.accesses.insert_one({"page":"/","user_agent":ua,"ip":f"179.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "visitor_id":str(uuid.uuid4()),"city":cidade,"uf":uf,"region_name":"Maranhão","country":"Brazil",
        "country_code":"BR","lat":None,"lon":None,"device":device,"created_at":ts,"seeded":True})

print("\n=== SEED CONCLUÍDO ===")
print(f"Inscrições criadas: {inserted}")
print(f"Split dispositivo: {counts}")
print(f"Acessos extras: {extra}")
print("Distribuição por cargo:")
for k,v in sorted(cargo_counts.items(), key=lambda x:-x[1]):
    print(f"  {v:3d}  {k}")
print(f"Total inscricoes finalizadas no banco: {db.inscricoes.count_documents({'finalized':True})}")
print(f"Total cadastros: {db.cadastros.count_documents({})}")
print(f"Total accesses: {db.accesses.count_documents({})}")
