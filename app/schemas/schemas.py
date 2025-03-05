"""
Esquemas Pydantic para validação de dados da API.

Este módulo contém todos os modelos Pydantic utilizados para validação
de dados de entrada e saída na API de integração com o Odoo.
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# Configuração comum para todos os modelos
class Config:
    """Configuração extra para os modelos."""
    extra = 'allow'


# ------------ Esquemas de Mensagens e Respostas Genéricas ------------

class Message(BaseModel):
    """Modelo para mensagens simples."""
    message: str


class HealthCheck(BaseModel):
    """Modelo para verificação de saúde da aplicação."""
    status: str
    version: str
    timestamp: datetime
    uptime: float


class PingResponse(BaseModel):
    """Modelo para resposta do endpoint de ping."""
    status: str


# ------------ Esquemas de Empresas/Contatos ------------

class CompanyDefault(BaseModel):
    """Modelo base para criação de empresas."""
    company_type: int = 0
    name: str
    vat: str
    country_id: int = 31
    phone: str
    email: EmailStr


class CompanyReturn(CompanyDefault):
    """Modelo de resposta após criação de empresa."""
    company_id: int


class ContactUpdate(BaseModel):
    """Modelo para atualização de campos específicos de clientes."""
    x_studio_certificado: Optional[str] = None
    x_studio_validade_da_procuracao: Optional[date] = None


# ------------ Esquemas de Oportunidades ------------

class OpportunityDefault(BaseModel):
    """Modelo base para criar oportunidades."""
    name: str
    partner_id: int
    x_studio_tese: Optional[str] = None
    user_id: int
    team_id: int
    stage_id: int = 10


class OpportunityReturn(OpportunityDefault):
    """Modelo de resposta após criação de oportunidade."""
    opportunity_id: int


class OpportunityCreate(BaseModel):
    """Modelo detalhado para criação de oportunidades."""
    name: str = Field(
        ...,
        description="Nome da oportunidade"
    )
    partner_id: int = Field(
        ...,
        description="ID do cliente"
    )
    expected_revenue: float = Field(
        0.0,
        description="Receita esperada"
    )
    probability: Optional[float] = Field(
        None,
        description="Probabilidade de fechamento"
    )
    date_deadline: Optional[str] = Field(
        None,
        description="Data limite (YYYY-MM-DD)"
    )
    user_id: Optional[int] = Field(
        None,
        description="Responsável pela oportunidade"
    )
    team_id: Optional[int] = Field(
        None,
        description="Equipe de vendas"
    )
    description: Optional[str] = Field(
        None,
        description="Descrição da oportunidade"
    )
    priority: Optional[str] = Field(
        None,
        description="Prioridade"
    )
    tag_ids: Optional[List[int]] = Field(
        None,
        description="Lista de IDs das tags"
    )
    company_id: Optional[int] = Field(
        None,
        description="ID da empresa relacionada"
    )

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


class OpportunityReturnDetailed(BaseModel):
    """Modelo detalhado de retorno para oportunidades."""
    opportunity_id: int
    name: str
    partner_id: List[int]
    expected_revenue: float
    probability: Optional[float]
    stage_id: List[int]
    company_id: Optional[int]


class AttachmentInfo(BaseModel):
    """Informações sobre anexos."""
    attachment_id: int
    filename: str


class OpportunityCreateResponse(BaseModel):
    """Resposta completa após criação de oportunidade com anexos."""
    message: str
    opportunity_id: int
    opportunity_details: OpportunityReturnDetailed
    attachments: List[AttachmentInfo]


# ------------ Esquemas de Pedidos de Venda ------------

class SaleOrderLine(BaseModel):
    """Modelo para linhas de pedido de venda."""
    product_id: int = Field(
        ...,
        description="ID do produto"
    )
    product_uom_qty: float = Field(
        ...,
        description="Quantidade do produto"
    )
    price_unit: float = Field(
        ...,
        description="Preço unitário do produto"
    )


class SaleOrderCreate(BaseModel):
    """Modelo para criação de pedido de venda."""
    partner_id: int = Field(
        ...,
        description="ID do cliente"
    )
    user_id: int = Field(
        ...,
        description="ID do vendedor pelo pedido"
    )
    opportunity_id: Optional[int] = Field(
        None,
        description="ID da oportunidade"
    )
    order_line: List[SaleOrderLine] = Field(
        ...,
        description="Lista de itens do pedido"
    )
    date_order: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Data do pedido (formato: YYYY-MM-DD)"
    )
    client_order_ref: Optional[str] = Field(
        None,
        description="Referência do pedido do cliente"
    )
    type_name: str = Field(
        default="Pedido de venda",
        description="Tipo do pedido"
    )


class SaleOrderUpdate(BaseModel):
    # Modelo para atualização de campos específicos de pedidos de venda.
    user_id: Optional[int] = Field(
        None,
        description="ID do vendedor responsável pelo pedido"
    )
    type_name: Optional[str] = Field(
        None,
        description="Tipo do pedido"
    )


# ------------ Esquemas de Tarefas de Projeto ------------

class TarefaCreate(BaseModel):
    """Modelo para criação de tarefas."""
    name: str
    project_id: int
    stage_id: int
    x_studio_tese_2: Optional[str] = None
    x_studio_segmento: Optional[str] = None


class TarefaUpdate(BaseModel):
    """Modelo para atualização de tarefas."""
    partner_id: Optional[int] = None
    x_studio_tese_2: str
    x_studio_segmento: Optional[str] = None


class TaskSaleOrderUpdate(BaseModel):
    """Modelo para vincular tarefa a pedido de venda."""
    task_id: int
    sale_order_id: int
    

class TaskStageUpdate(BaseModel):
    #Modelo para atualização de estágio de tarefa.
    stage_id: int = Field(
        ...,
        description="ID do estágio para o qual a tarefa deve ser movida"
    )


# ------------ Outros Esquemas ------------

class PartnerNames(BaseModel):
    """Modelo para busca de parceiros por nomes."""
    names: List[str]
