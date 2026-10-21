from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Admin/tracking routes
from admin_routes import admin_router, set_db, seed_admin, seed_pix_config
set_db(db)


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


@api_router.get("/")
async def root():
    return {"message": "Painel Administrativo API"}


@api_router.get("/cep/{cep}")
async def buscar_cep(cep: str):
    import httpx, re
    clean = re.sub(r"\D", "", cep or "")
    if len(clean) != 8:
        return {"erro": True, "message": "CEP inválido"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"https://viacep.com.br/ws/{clean}/json/")
            if r.status_code == 200:
                data = r.json()
                if not data.get("erro"):
                    return data
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"https://brasilapi.com.br/api/cep/v1/{clean}")
            if r.status_code == 200:
                d = r.json()
                return {
                    "cep": d.get("cep", clean),
                    "logradouro": d.get("street", ""),
                    "bairro": d.get("neighborhood", ""),
                    "localidade": d.get("city", ""),
                    "uf": d.get("state", ""),
                }
    except Exception:
        pass
    return {"erro": True, "message": "Não foi possível consultar o CEP"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


app.include_router(api_router)
app.include_router(admin_router)


@app.on_event("startup")
async def on_startup():
    await seed_admin()
    # PIX config seeding disabled: chave PIX deve ser cadastrada manualmente
    # pelo painel admin (Configurações). Se precisar re-habilitar seed, descomente:
    # await seed_pix_config()


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
