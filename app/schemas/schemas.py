from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


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


# ------------ Esquemas de analytic ------------

class DateRangeParams(BaseModel):
    """Modelo para validação de parâmetros de período."""
    start_date: str = Field(
        ...,
        description="Data inicial no formato dd-mm-aaaa"
    )
    end_date: str = Field(
        ...,
        description="Data final no formato dd-mm-aaaa"
    )

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%d-%m-%Y')
        except ValueError:
            raise ValueError('Data deve estar no formato dd-mm-aaaa')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        start_date = info.data.get('start_date')
        if start_date:
            start = datetime.strptime(start_date, '%d-%m-%Y')
            end = datetime.strptime(v, '%d-%m-%Y')
            if end < start:
                raise ValueError('Data final deve ser maior ou igual à data inicial')
        return v


class TeamSalesAnalytics(BaseModel):
    """Modelo para análise de vendas por equipe."""
    id: int
    name: str
    total_contracts: int
    total_amount: float
    expected_revenue_partial: float


class UserSalesAnalytics(BaseModel):
    """Modelo para análise de vendas por vendedor."""
    id: int
    name: str
    team_id: int
    team_name: str
    total_contracts: int
    total_amount: float


class ProductSalesAnalytics(BaseModel):
    """Modelo para análise de vendas por produto/tese."""
    id: Optional[int] = None
    name: str
    total_sales: int
    total_amount: float


class OpportunityDetail(BaseModel):
    """Modelo para detalhes de oportunidade nos relatórios de análise."""
    id: int
    name: str
    client: str
    vat: Optional[str] = None  # Campo VAT (CNPJ/CPF) adicionado
    expected_revenue: float
    date_closed: str
    sales_person: str
    commercial_partner: Optional[str] = None  # Modificado para aceitar explicitamente None
    segment: Optional[str] = None  # Modificado para aceitar explicitamente None
    sales_team: str

    model_config = {
        # Adiciona configuração para ignorar valores extras
        "extra": "ignore"
    }


class SalesAnalyticsResponse(BaseModel):
    """Modelo para resposta completa de análise de vendas."""
    period: dict
    teams: List[TeamSalesAnalytics]
    users: List[UserSalesAnalytics]
    products: List[ProductSalesAnalytics]
    opportunities: List[OpportunityDetail] = []  # Lista de oportunidades com detalhes


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
    stage_id: int


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
    partner_id: Optional[int] = None
    description: Optional[str] = None
    x_studio_numero_da_comunicacao: Optional[str] = None
    x_studio_data_da_primeira_leitura: Optional[str] = None
    date_deadline: Optional[str] = None
    x_studio_principal: Optional[float] = 0.0
    x_studio_multa: Optional[float] = 0.0
    x_studio_juros: Optional[float] = 0.0
    x_studio_credito_em_analise: Optional[float] = 0.0
    x_studio_credito_reconhecido: Optional[float] = 0.0
    x_studio_periodo_de_apuracao: Optional[str] = None
    x_studio_tipo_de_credito: Optional[str] = None
    x_studio_numero_do_perdcomp: Optional[str] = None


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
    # Modelo para atualização de estágio de tarefa.
    stage_id: int = Field(
        ...,
        description="ID do estágio para o qual a tarefa deve ser movida"
    )


class TaskMessageTransfer(BaseModel):
    """Modelo para transferência de mensagens entre tarefas."""
    source_task_id: int = Field(
        ...,
        description="ID da tarefa de origem das mensagens"
    )
    target_task_id: int = Field(
        ...,
        description="ID da tarefa de destino que receberá as mensagens"
    )

# ---------- helpdesk ----------------


# Atualize este modelo no arquivo schemas.py

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class HelpdeskTicketUpdate(BaseModel):
    """Modelo para atualização de estágio e/ou equipe de um chamado de helpdesk."""
    ticket_id: int = Field(
        ...,
        description="ID do chamado a ser atualizado"
    )
    team_id: int = Field(
        ...,
        description="ID da equipe atual do chamado (para validação)"
    )
    new_stage_id: Optional[int] = Field(
        None,
        description="ID do novo estágio para o chamado (opcional)"
    )
    new_team_id: Optional[int] = Field(
        None,
        description="ID da nova equipe para o chamado (opcional)"
    )
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Verifica se pelo menos um dos campos de atualização foi fornecido."""
        if self.new_stage_id is None and self.new_team_id is None:
            raise ValueError('Pelo menos um dos campos new_stage_id ou new_team_id deve ser fornecido')
        return self

# ------------ Outros Esquemas ------------


class PartnerNames(BaseModel):
    """Modelo para busca de parceiros por nomes."""
    names: List[str]


class SelectionFieldValue(BaseModel):
    """Modelo para um único valor de campo de seleção com valor e nome."""
    value: str
    name: str


class SelectionFieldUpdate(BaseModel):
    """Modelo para atualização de campo de seleção com múltiplos valores."""
    model_name: str = Field(
        ...,
        description="Nome do modelo ao qual o campo pertence")
    field_name: str = Field(
        ...,
        description="Nome do campo de seleção a ser atualizado")
    values: List[SelectionFieldValue] = Field(...,
        description="Lista de valores de seleção")
