from fastapi import FastAPI
from src.api.company_endpoints import router as company_router
from src.api.crm_endpoints import router as crm_router
from scalar_fastapi import get_scalar_api_reference

app = FastAPI()

app.include_router(company_router, prefix="/api")
app.include_router(crm_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "API Odoo está ativa e funcionando"}

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

