from datetime import date, datetime
from typing import Any, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


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
        ..., description='Data inicial no formato dd-mm-aaaa'
    )
    end_date: str = Field(..., description='Data final no formato dd-mm-aaaa')

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
                raise ValueError(
                    'Data final deve ser maior ou igual à data inicial'
                )
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
    commercial_partner: Optional[str] = (
        None  # Modificado para aceitar explicitamente None
    )
    segment: Optional[str] = (
        None  # Modificado para aceitar explicitamente None
    )
    sales_team: str

    model_config = {
        # Adiciona configuração para ignorar valores extras
        'extra': 'ignore'
    }


class SalesAnalyticsResponse(BaseModel):
    """Modelo para resposta completa de análise de vendas."""

    period: dict
    teams: List[TeamSalesAnalytics]
    users: List[UserSalesAnalytics]
    products: List[ProductSalesAnalytics]
    opportunities: List[
        OpportunityDetail
    ] = []  # Lista de oportunidades com detalhes


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

    name: str = Field(..., description='Nome da oportunidade')
    partner_id: int = Field(..., description='ID do cliente')
    expected_revenue: float = Field(0.0, description='Receita esperada')
    probability: Optional[float] = Field(
        None, description='Probabilidade de fechamento'
    )
    date_deadline: Optional[str] = Field(
        None, description='Data limite (YYYY-MM-DD)'
    )
    user_id: Optional[int] = Field(
        None, description='Responsável pela oportunidade'
    )
    team_id: Optional[int] = Field(None, description='Equipe de vendas')
    description: Optional[str] = Field(
        None, description='Descrição da oportunidade'
    )
    priority: Optional[str] = Field(None, description='Prioridade')
    tag_ids: Optional[List[int]] = Field(
        None, description='Lista de IDs das tags'
    )
    company_id: Optional[int] = Field(
        None, description='ID da empresa relacionada'
    )

    class Config:
        schema_extra = {
            'example': {
                'name': 'Oportunidade de Venda - Cliente ABC',
                'partner_id': 42,
                'expected_revenue': 10000.00,
                'probability': 50.0,
                'date_deadline': '2023-12-31',
                'user_id': 5,
                'team_id': 1,
                'description': 'Potencial venda de serviços de consultoria',
                'priority': '1',
                'tag_ids': [1, 4, 7],
                'company_id': 1,
            }
        }


class OpportunityCreateIntelligent(BaseModel):
    name: str = Field(..., description="Nome da oportunidade")
    user_id: int = Field(..., description="ID do vendedor responsável")
    company_name: str = Field(..., description="Nome da empresa/cliente")
    company_vat: str = Field(..., description="CNPJ da empresa/cliente. Serão considerados apenas os dígitos.")

    team_id: Optional[int] = Field(None, description="ID da equipe de vendas (opcional, Odoo pode usar um padrão)")
    stage_id: Optional[int] = Field(None, description="ID do estágio inicial da oportunidade (opcional, Odoo pode usar um padrão)")
    x_studio_tese: Optional[str] = Field(None, description="Tese da oportunidade (campo customizado)")
    expected_revenue: Optional[float] = Field(None, description="Receita esperada")

    class Config:
        extra = 'allow'
        schema_extra = {
            "example": {
                "name": "L G M - COMERCIO DE ALUMINIOS LTDA | 07.383.820/0001-59",  # Seu exemplo
                "user_id": 75,  # Seu exemplo
                "company_name": "L G M - COMERCIO DE ALUMINIOS LTDA",  # Seu exemplo
                "company_vat": "07.383.820/0001-59",  # Seu exemplo
                # team_id e stage_id agora podem ser omitidos na requisição
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

    product_id: int = Field(..., description='ID do produto')
    product_uom_qty: float = Field(..., description='Quantidade do produto')
    price_unit: float = Field(..., description='Preço unitário do produto')


class SaleOrderCreate(BaseModel):
    """Modelo para criação de pedido de venda."""

    partner_id: int = Field(..., description='ID do cliente')
    user_id: int = Field(..., description='ID do vendedor pelo pedido')
    opportunity_id: Optional[int] = Field(
        None, description='ID da oportunidade'
    )
    order_line: List[SaleOrderLine] = Field(
        ..., description='Lista de itens do pedido'
    )
    date_order: Optional[datetime] = Field(
        default_factory=datetime.now,
        description='Data do pedido (formato: YYYY-MM-DD)',
    )
    client_order_ref: Optional[str] = Field(
        None, description='Referência do pedido do cliente'
    )
    type_name: str = Field(
        default='Pedido de venda', description='Tipo do pedido'
    )


class SaleOrderUpdate(BaseModel):
    # Modelo para atualização de campos específicos de pedidos de venda.
    user_id: Optional[int] = Field(
        None, description='ID do vendedor responsável pelo pedido'
    )
    type_name: Optional[str] = Field(None, description='Tipo do pedido')


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
        ..., description='ID do estágio para o qual a tarefa deve ser movida'
    )


class TaskMessageTransfer(BaseModel):
    """Modelo para transferência de mensagens entre tarefas."""

    source_task_id: int = Field(
        ..., description='ID da tarefa de origem das mensagens'
    )
    target_task_id: int = Field(
        ..., description='ID da tarefa de destino que receberá as mensagens'
    )


class TaskByVatInfo(BaseModel):
    """Modelo para informações de tarefa na busca por CNPJ."""

    id: int
    name: str
    partner_name: str
    stage_name: str
    project_name: str
    x_studio_numero_do_perdcomp: str
    date_last_stage_update: str
    write_date: str


class TasksByVatResponse(BaseModel):
    """Modelo de resposta para busca de tarefas por CNPJ."""

    vat: str = Field(..., description='CNPJ pesquisado')
    projects_searched: List[int] = Field(
        ..., description='IDs dos projetos pesquisados'
    )
    total_tasks: int = Field(..., description='Total de tarefas encontradas')
    tasks: List[TaskByVatInfo] = Field(
        ..., description='Lista de tarefas encontradas'
    )


# ---------- helpdesk ----------------


class HelpdeskTicketUpdate(BaseModel):
    """Modelo para atualização de estágio e/ou equipe de um chamado de helpdesk."""

    ticket_id: int = Field(..., description='ID do chamado a ser atualizado')
    team_id: int = Field(
        ..., description='ID da equipe atual do chamado (para validação)'
    )
    new_stage_id: Optional[int] = Field(
        None, description='ID do novo estágio para o chamado (opcional)'
    )
    new_team_id: Optional[int] = Field(
        None, description='ID da nova equipe para o chamado (opcional)'
    )

    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Verifica se pelo menos um dos campos de atualização foi fornecido."""
        if self.new_stage_id is None and self.new_team_id is None:
            raise ValueError(
                'Pelo menos um dos campos new_stage_id ou new_team_id deve ser fornecido'
            )
        return self


class HelpdeskTicketByVat(BaseModel):
    """Modelo para chamado de helpdesk retornado pela busca por VAT."""

    id: int
    name: Optional[str] = None
    client_name: Optional[str] = None
    stage_name: Optional[str] = None
    responsible_names: Optional[List] = None
    write_date: Optional[datetime] = None
    date_last_stage_update: Optional[datetime] = None
    model_config = ConfigDict(extra='ignore')


class HelpdeskTicketsByVatResponse(BaseModel):
    """Modelo de resposta para lista de chamados de helpdesk por VAT."""

    chamados: List[HelpdeskTicketByVat]


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
        ..., description='Nome do modelo ao qual o campo pertence'
    )
    field_name: str = Field(
        ..., description='Nome do campo de seleção a ser atualizado'
    )
    values: List[SelectionFieldValue] = Field(
        ..., description='Lista de valores de seleção'
    )


class OpportunityPowerBIData(BaseModel):
    """Modelo para dados de oportunidades para PowerBI."""
    
    model_config = ConfigDict(extra='allow')
    
    id: Optional[int] = None
    create_date: Optional[Any] = None
    name: Optional[Any] = None
    x_studio_tese: Optional[Any] = None
    partner_id: Optional[Any] = None
    state_id: Optional[Any] = None
    user_id: Optional[Any] = None
    team_id: Optional[Any] = None
    activity_ids: Optional[Any] = None
    expected_revenue: Optional[Any] = None
    stage_id: Optional[Any] = None
    x_studio_categoria_economica: Optional[Any] = None
    active: Optional[Any] = None
    won_status: Optional[Any] = None
    lost_reason_id: Optional[Any] = None
    x_studio_previsao_inss: Optional[Any] = None
    x_studio_previsao_ipi: Optional[Any] = None
    x_studio_previsao_irpj_e_csll: Optional[Any] = None
    x_studio_previsao_pis_e_cofins: Optional[Any] = None
    x_studio_debitos: Optional[Any] = None
    x_studio_ultima_atualizacao_de_estagio: Optional[Any] = None
    x_studio_ticket_de_1_anlise: Optional[Any] = None
    x_studio_ticket_de_2_analise: Optional[Any] = None
    x_studio_probabilidade: Optional[Any] = None
    x_studio_receita_bruta_esperada: Optional[Any] = None
    x_studio_faturamento_esperado: Optional[Any] = None
    x_studio_honorrios_1: Optional[Any] = None
    write_date: Optional[Any] = None
    date_closed: Optional[Any] = None
    x_studio_tipo_de_oportunidade_1: Optional[Any] = None
    
    # Additional fields for new mappings
    x_studio_data_calculo_pendente: Optional[Any] = None
    
    # Additional fields from JSON
    phone: Optional[Any] = None
    email_from: Optional[Any] = None
    city: Optional[Any] = None
    zip: Optional[Any] = None
    
    # Stage tracking fields from mail.message
    stage_tracking_prospect_date: Optional[Any] = None
    stage_tracking_prospect_user: Optional[Any] = None
    stage_tracking_primeira_reuniao_date: Optional[Any] = None
    stage_tracking_primeira_reuniao_user: Optional[Any] = None
    stage_tracking_aguardando_documentacao_date: Optional[Any] = None
    stage_tracking_aguardando_documentacao_user: Optional[Any] = None
    stage_tracking_calculo_pendente_date: Optional[Any] = None
    stage_tracking_calculo_pendente_user: Optional[Any] = None
    stage_tracking_em_processamento_date: Optional[Any] = None
    stage_tracking_em_processamento_user: Optional[Any] = None
    stage_tracking_calculo_concluido_date: Optional[Any] = None
    stage_tracking_calculo_concluido_user: Optional[Any] = None
    stage_tracking_revisao_de_calculo_date: Optional[Any] = None
    stage_tracking_revisao_de_calculo_user: Optional[Any] = None
    stage_tracking_apresentacao_date: Optional[Any] = None
    stage_tracking_apresentacao_user: Optional[Any] = None
    stage_tracking_em_negociacao_date: Optional[Any] = None
    stage_tracking_em_negociacao_user: Optional[Any] = None


class OpportunityPowerBIResponse(BaseModel):
    """Modelo de resposta para dados de oportunidades para PowerBI com nomes em português."""
    
    model_config = ConfigDict(extra='allow')
    
    id: Optional[int] = None
    CriadoEm: Optional[Any] = Field(None, alias="create_date")
    Oportunidade: Optional[Any] = Field(None, alias="name")
    Tese: Optional[Any] = Field(None, alias="x_studio_tese")
    Cliente: Optional[Any] = Field(None, alias="partner_id")
    Estado: Optional[Any] = Field(None, alias="state_id")
    Vendedor: Optional[Any] = Field(None, alias="user_id")
    EquipeDeVendas: Optional[Any] = Field(None, alias="team_id")
    UltimaAtividade: Optional[Any] = Field(None, alias="activity_ids")
    ReceitaEsperada: Optional[Any] = Field(None, alias="expected_revenue")
    Estagio: Optional[Any] = Field(None, alias="stage_id")
    Segmento: Optional[Any] = Field(None, alias="x_studio_categoria_economica")
    Ativo: Optional[Any] = Field(None, alias="active")
    StatusGanhoPerda: Optional[Any] = Field(None, alias="won_status")
    MotivoDaPerda: Optional[Any] = Field(None, alias="lost_reason_id")
    PrevisaoInss: Optional[Any] = Field(None, alias="x_studio_previsao_inss")
    PrevisaoIpi: Optional[Any] = Field(None, alias="x_studio_previsao_ipi")
    PrevisaoIrpjCsll: Optional[Any] = Field(None, alias="x_studio_previsao_irpj_e_csll")
    PrevisaoPisCofins: Optional[Any] = Field(None, alias="x_studio_previsao_pis_e_cofins")
    Debitos: Optional[Any] = Field(None, alias="x_studio_debitos")
    UltimaAtualizacaoDeEstagio: Optional[Any] = Field(None, alias="x_studio_ultima_atualizacao_de_estagio")
    TicketDePrimeiraAnalise: Optional[Any] = Field(None, alias="x_studio_ticket_de_1_anlise")
    TicketDeSegundaAnalise: Optional[Any] = Field(None, alias="x_studio_ticket_de_2_analise")
    Probabilidade: Optional[Any] = Field(None, alias="x_studio_probabilidade")
    ReceitaBrutaEsperada: Optional[Any] = Field(None, alias="x_studio_receita_bruta_esperada")
    FaturamentoEsperado: Optional[Any] = Field(None, alias="x_studio_faturamento_esperado")
    Honorarios: Optional[Any] = Field(None, alias="x_studio_honorrios_1")
    UltimaAtualizacao: Optional[Any] = Field(None, alias="write_date")
    DataDeGanhoOuPerda: Optional[Any] = Field(None, alias="date_closed")
    TipoDeOportunidade: Optional[Any] = Field(None, alias="x_studio_tipo_de_oportunidade_1")
    Telefone: Optional[Any] = Field(None, alias="phone")
    Email: Optional[Any] = Field(None, alias="email_from")
    Cidade: Optional[Any] = Field(None, alias="city")
    CEP: Optional[Any] = Field(None, alias="zip")
    DataCalculoPendente: Optional[Any] = Field(None, alias="x_studio_data_calculo_pendente")
    DataEmProcessamento: Optional[Any] = Field(None, alias="x_studio_data_em_processamento_1")
    DataCalculoConcluido: Optional[Any] = Field(None, alias="x_studio_data_calculo_concluido")
    UsuarioCalculoConcluido: Optional[Any] = Field(None, alias="x_studio_usuario_calculo_concluido")
