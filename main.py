from fastapi import FastAPI
from src.api.company_endpoints import router as company_router

app = FastAPI()

# Incluir as rotas da API para as empresas
app.include_router(company_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "API Odoo está ativa e funcionando"}
