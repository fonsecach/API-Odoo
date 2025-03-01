import base64
import json
from http import HTTPStatus
from typing import List

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import (
    AttachmentInfo,
    OpportunityCreate,
    OpportunityCreateResponse,
    OpportunityDefault,
    OpportunityReturn,
)
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.company_service import get_or_create_partner
from app.Services.crm_service import (
    create_opportunity_in_crm,
    fetch_opportunity_by_id,
    get_opportunities_info,
)

router = APIRouter(prefix='/opportunities', tags=['Oportunidades'])


@router.get('/', summary='Lista oportunidades cadastradas')
async def list_opportunities(limit: int = 100, offset: int = 0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    opportunities_info = get_opportunities_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not opportunities_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma oportunidade localizada',
        )

    return {'opportunities': opportunities_info}


@router.get('/{opportunity_id}', summary='Oportunidade pelo ID')
async def get_opportunity_by_id(opportunity_id: int):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )
    opportunity_info = fetch_opportunity_by_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, opportunity_id
    )
    if not opportunity_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma oportunidade localizada',
        )
    return {'opportunity': opportunity_info}


@router.post(
    '/v1/',
    summary='Cadastrar uma oportunidade',
    status_code=status.HTTP_201_CREATED,
    response_model=OpportunityReturn,
)
async def create_opportunity(opportunity_info: OpportunityDefault):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    # 🔹 Passo 1: Criar cliente a partir do contato
    partner_id = get_or_create_partner(
        opportunity_info.contact_name, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not partner_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Erro ao criar ou recuperar o cliente',
        )

    # 🔹 Passo 2: Criar oportunidade no CRM
    opportunity_data = opportunity_info.dict(exclude_unset=True)
    opportunity_data.update({
        'partner_id': partner_id,  # Associar cliente
        'type': 'opportunity',  # Definir como oportunidade (não lead)
    })

    opportunity_id = create_opportunity_in_crm(
        opportunity_data, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not opportunity_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma oportunidade criada',
        )

    return {'opportunity_id': opportunity_id, **opportunity_data}


@router.post(
    '/v2',
    summary='Cadastrar uma oportunidade',
    status_code=status.HTTP_201_CREATED,
    response_model=OpportunityReturn,
)
async def create_opportunity(opportunity_info: OpportunityDefault):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    # 🔹 Utilizar cliente já existente
    partner_id = opportunity_info.partner_id

    if not partner_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='ID do cliente não informado',
        )

    # 🔹 Criar oportunidade no CRM
    opportunity_data = opportunity_info.dict(exclude_unset=True)
    opportunity_data.update({
        'partner_id': partner_id,
        'type': 'opportunity',
    })

    try:
        opportunity_id = create_opportunity_in_crm(
            opportunity_data, models, ODOO_DB, uid, ODOO_PASSWORD
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao criar oportunidade: {str(e)}',
        )

    return {'opportunity_id': opportunity_id, **opportunity_data}


# para teste de criar oportunidade com anexo

@router.post(
    "/opportunities/",
    summary="Cria uma nova oportunidade com anexo",
    response_description="Oportunidade criada com sucesso",
    response_model=OpportunityCreateResponse,
    status_code=HTTPStatus.CREATED
)
async def create_opportunity_with_attachment(
    opportunity_data: str = Form(...),
    files: List[UploadFile] = File(...),
):
    """
    Cria uma nova oportunidade no Odoo e anexa um ou mais documentos a ela.
    
    Args:
        opportunity_data: Dados da oportunidade em formato JSON string
        files: Lista de arquivos a serem anexados à oportunidade
    
    Returns:
        Detalhes da oportunidade criada e dos anexos
    """
    try:
        # Converter a string JSON para um dicionário
        opportunity_dict = json.loads(opportunity_data)
        # Validar usando o modelo Pydantic
        opportunity = OpportunityCreate(**opportunity_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Formato JSON inválido para os dados da oportunidade",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Dados da oportunidade inválidos: {str(e)}",
        )

    # Preparar dados para o Odoo
    opportunity_data = opportunity.dict(exclude_none=True)

    # Converter tags para o formato esperado pelo Odoo (se existirem)
    if opportunity_data.get("tag_ids"):
        opportunity_data["tag_ids"] = [(6, 0, opportunity_data["tag_ids"])]

    # Conectar ao Odoo
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Falha na autenticação no Odoo",
        )

    try:
        # Criar a oportunidade no Odoo
        opportunity_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "crm.lead",  # Modelo de oportunidade no Odoo
            "create",
            [opportunity_data],
        )

        # Se não conseguiu criar a oportunidade, levanta exceção
        if not opportunity_id:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Não foi possível criar a oportunidade",
            )

        attachments = []
        # Processar cada arquivo enviado
        for file in files:
            # Ler e codificar o arquivo em base64
            file_content = await file.read()
            encoded_content = base64.b64encode(file_content).decode("utf-8")

            # Criar anexo no Odoo vinculado à oportunidade
            attachment_data = {
                "name": file.filename,
                "datas": encoded_content,
                "res_model": "crm.lead",  # Modelo da oportunidade
                "res_id": opportunity_id,  # ID da oportunidade criada
            }

            attachment_id = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                "ir.attachment",
                "create",
                [attachment_data],
            )

            attachments.append(AttachmentInfo(
                attachment_id=attachment_id,
                filename=file.filename,
            ))

        # Obter detalhes da oportunidade criada
        opportunity_details = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "crm.lead",
            "read",
            [opportunity_id],
            {"fields": ["name", "partner_id", "expected_revenue", "stage_id", "probability", "company_id"]}
        )[0]

        # Converter para o modelo de retorno
        opp_return = OpportunityReturn(
            opportunity_id=opportunity_id,
            name=opportunity_details["name"],
            partner_id=opportunity_details["partner_id"],
            expected_revenue=opportunity_details["expected_revenue"],
            probability=opportunity_details.get("probability"),
            stage_id=opportunity_details["stage_id"],
            company_id=opportunity_details.get("company_id")
        )

        return OpportunityCreateResponse(
            message="Oportunidade criada com sucesso",
            opportunity_id=opportunity_id,
            opportunity_details=opp_return,
            attachments=attachments
        )

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar oportunidade com anexo: {str(e)}",
        )
