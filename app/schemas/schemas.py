from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Company_default(BaseModel):
    company_type: int = 0
    name: str
    vat: str
    country_id: int = 31
    phone: str
    email: EmailStr


class Company_return(Company_default):
    company_id: int


# Utilizado no metodo para atualizar alguns campos do modelo de clientes
class contact_update(BaseModel):
    x_studio_certificado: str | None
    x_studio_validade_da_procuracao: date | None


class Opportunity_default(BaseModel):
    name: str
    partner_id: int
    x_studio_tese: str | None
    user_id: int
    team_id: int
    stage_id: int = 10


class Opportunity_return(Opportunity_default):
    opportunity_id: int


class SaleOrderLine(BaseModel):
    product_id: int = Field(..., description="ID do produto")
    product_uom_qty: float = Field(..., description="Quantidade do produto")
    price_unit: float = Field(..., description="Preço unitário do produto")


class SaleOrderCreate(BaseModel):
    partner_id: int = Field(..., description="ID do cliente")
    user_id: int = Field(..., description="ID do vendedor pelo pedido")
    opportunity_id: Optional[int] = Field(None, description="ID da oportunidade (crm.lead) vinculada")
    order_line: List[SaleOrderLine] = Field(..., description="Lista de itens do pedido")
    date_order: Optional[datetime] = Field(
        default_factory=datetime.now,  # Valor padrão: data e hora atuais
        description="Data do pedido (formato: YYYY-MM-DD)"
    )
    client_order_ref: Optional[str] = Field(None, description="Referência do pedido do cliente")
    type_name: str = Field(default="Pedido de venda", description="Tipo do pedido")


class TarefaCreate(BaseModel):
    name: str
    project_id: int
    stage_id: int
    x_studio_tese_2: str | None
    x_studio_segmento: str | None


class TarefaUpdate(BaseModel):
    partner_id: int | None
    x_studio_tese_2: str
    x_studio_segmento: str | None


class PartnerNames(BaseModel):
    names: list[str]


class Config:
    extra = 'allow'


class Message(BaseModel):
    message: str


class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    uptime: float


class PingResponse(BaseModel):
    status: str


# para teste

class OpportunityCreate(BaseModel):
    name: str = Field(..., description="Nome da oportunidade")
    partner_id: int = Field(..., description="ID do cliente/parceiro")
    expected_revenue: float = Field(0.0, description="Receita esperada")
    probability: Optional[float] = Field(None, description="Probabilidade de fechamento (%)")
    date_deadline: Optional[str] = Field(None, description="Data limite (YYYY-MM-DD)")
    user_id: Optional[int] = Field(None, description="Responsável pela oportunidade")
    team_id: Optional[int] = Field(None, description="Equipe de vendas")
    description: Optional[str] = Field(None, description="Descrição da oportunidade")
    priority: Optional[str] = Field(None, description="Prioridade (0=Baixa, 1=Normal, 2=Alta, 3=Muito Alta)")
    tag_ids: Optional[List[int]] = Field(None, description="Lista de IDs das tags")
    company_id: Optional[int] = Field(None, description="ID da empresa relacionada")

    class Config:
        schema_extra = {
            "example": {
                "name": "Oportunidade de Venda - Cliente ABC",
                "partner_id": 42,
                "expected_revenue": 10000.00,
                "probability": 50.0,
                "date_deadline": "2023-12-31",
                "user_id": 5,
                "team_id": 1,
                "description": "Potencial venda de serviços de consultoria",
                "priority": "1",
                "tag_ids": [1, 4, 7],
                "company_id": 1
            }
        }


class OpportunityReturn(BaseModel):
    opportunity_id: int
    name: str
    partner_id: List[int]
    expected_revenue: float
    probability: Optional[float]
    stage_id: List[int]
    company_id: Optional[int]


class AttachmentInfo(BaseModel):
    attachment_id: int
    filename: str


class OpportunityCreateResponse(BaseModel):
    message: str
    opportunity_id: int
    opportunity_details: OpportunityReturn
    attachments: List[AttachmentInfo]
