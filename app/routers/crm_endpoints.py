import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.schemas import OpportunityPowerBIData
from app.services.crm_service import (
    fetch_opportunities_for_powerbi, 
    fetch_opportunities_for_powerbi_by_company, 
    fetch_opportunity_by_id_for_powerbi, 
    get_opportunity_stage_tracking_data,
    fetch_opportunities_for_powerbi_with_pt_names,
    fetch_opportunities_for_powerbi_by_company_with_pt_names,
    fetch_opportunity_by_id_for_powerbi_with_pt_names
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/opportunities', tags=['Oportunidades'])


@router.get(
    '/powerbi',
    summary='Buscar dados de oportunidades para PowerBI',
    description='Endpoint especializado para fornecer dados das oportunidades CRM formatados para consumo pelo PowerBI com nomes em português',
    response_model=List[dict],
    tags=['PowerBI']
)
async def get_opportunities_powerbi_endpoint():
    """
    Retorna todas as oportunidades do CRM com todos os campos necessários para análise no PowerBI.
    Os campos são retornados com nomes em português e remove campos: probability, street, country_id.
    
    Returns:
        Lista completa de oportunidades com todos os campos de negócio formatados.
    """
    try:
        opportunities = await fetch_opportunities_for_powerbi_with_pt_names()
        
        if not opportunities:
            logger.info("Nenhuma oportunidade encontrada para PowerBI")
            return []
        
        logger.info(f"Retornando {len(opportunities)} oportunidades para PowerBI")
        return opportunities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint PowerBI: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao buscar dados para PowerBI"
        )


@router.get(
    '/powerbi/company/{company_id}',
    summary='Buscar oportunidades de uma empresa específica para PowerBI',
    description='Endpoint para buscar oportunidades de uma empresa específica formatadas para PowerBI com nomes em português',
    response_model=List[dict],
    tags=['PowerBI']
)
async def get_opportunities_powerbi_by_company_endpoint(company_id: int):
    """
    Retorna todas as oportunidades de uma empresa específica do CRM formatadas para PowerBI.
    Os campos são retornados com nomes em português e remove campos: probability, street, country_id.
    
    Args:
        company_id: ID da empresa (partner_id) para filtrar as oportunidades.
    
    Returns:
        Lista de oportunidades da empresa especificada com todos os campos de negócio.
    """
    try:
        opportunities = await fetch_opportunities_for_powerbi_by_company_with_pt_names(company_id)
        
        if not opportunities:
            logger.info(f"Nenhuma oportunidade encontrada para a empresa ID {company_id}")
            return []
        
        logger.info(f"Retornando {len(opportunities)} oportunidades da empresa {company_id} para PowerBI")
        return opportunities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint PowerBI para empresa {company_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor ao buscar dados da empresa {company_id} para PowerBI"
        )


@router.get(
    '/powerbi/{opportunity_id}',
    summary='Buscar uma oportunidade específica por ID para PowerBI',
    description='Endpoint para buscar uma oportunidade específica por ID formatada para PowerBI com nomes em português',
    response_model=dict,
    tags=['PowerBI']
)
async def get_opportunity_powerbi_by_id_endpoint(opportunity_id: int):
    """
    Retorna uma oportunidade específica do CRM formatada para PowerBI.
    Os campos são retornados com nomes em português e remove campos: probability, street, country_id.
    
    Args:
        opportunity_id: ID da oportunidade para buscar.
    
    Returns:
        Dicionário da oportunidade especificada com nomes em português.
    
    Raises:
        HTTPException: 404 se a oportunidade não for encontrada.
    """
    try:
        opportunity = await fetch_opportunity_by_id_for_powerbi_with_pt_names(opportunity_id)
        logger.info(f"Oportunidade ID {opportunity_id} retornada para PowerBI")
        return opportunity
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint PowerBI para oportunidade {opportunity_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor ao buscar oportunidade {opportunity_id} para PowerBI"
        )


@router.get(
    '/{opportunity_id}/stage-tracking',
    summary='Buscar dados de rastreamento de estágios de uma oportunidade',
    description='Endpoint para buscar datas de mudanças de estágio específicos do mail.message',
    tags=['Rastreamento']
)
async def get_opportunity_stage_tracking_endpoint(opportunity_id: int, debug: bool = False):
    """
    Retorna dados de rastreamento de estágios de uma oportunidade específica.
    
    Busca no mail.message as datas quando a oportunidade passou pelos estágios:
    - Cálculo Pendente
    - Em Processamento  
    - Cálculo Concluído
    
    Args:
        opportunity_id: ID da oportunidade para buscar rastreamento.
        debug: Se True, retorna informações de debug adicionais.
    
    Returns:
        Dicionário com as datas dos estágios e informações do usuário.
    """
    try:
        tracking_data = await get_opportunity_stage_tracking_data(opportunity_id)
        
        if debug:
            # Buscar mensagens brutas para debug
            from app.services.crm_service import get_odoo_client
            odoo_client = await get_odoo_client()
            messages = await odoo_client.search_read(
                'mail.message',
                domain=[
                    ['model', '=', 'crm.lead'],
                    ['res_id', '=', opportunity_id]
                ],
                fields=['id', 'date', 'body', 'author_id', 'message_type', 'tracking_value_ids'],
                order='date asc'
            )
            
            # Buscar tracking values
            tracking_values = await odoo_client.search_read(
                'mail.tracking.value',
                domain=[],
                fields=['id', 'field', 'old_value_char', 'new_value_char', 'mail_message_id'],
                limit=1000
            )
            
            # Buscar estágios para debug
            stages = await odoo_client.search_read(
                'crm.stage',
                domain=[],
                fields=['id', 'name']
            )
            
            message_ids = [msg['id'] for msg in messages]
            relevant_tracking = [
                tv for tv in tracking_values 
                if tv.get('mail_message_id') and tv['mail_message_id'][0] in message_ids
            ]
            
            tracking_data['debug_messages'] = messages
            tracking_data['debug_tracking_values'] = relevant_tracking
            tracking_data['debug_stages'] = stages
        
        logger.info(f"Dados de rastreamento retornados para oportunidade {opportunity_id}")
        return tracking_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no endpoint de rastreamento para oportunidade {opportunity_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor ao buscar dados de rastreamento da oportunidade {opportunity_id}"
        )


# @router.get('/', summary='Lista oportunidades cadastradas')
# async def list_opportunities_endpoint(limit: int = 100, offset: int = 0):
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     opportunities_info = get_opportunities_info(
#         models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
#     )

#     if not opportunities_info:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='Nenhuma oportunidade localizada',
#         )

#     return {'opportunities': opportunities_info}


# @router.get('/{opportunity_id}', summary='Oportunidade pelo ID')
# async def get_opportunity_by_id_endpoint(opportunity_id: int):
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )
#     opportunity_info = fetch_opportunity_by_id(
#         models, ODOO_DB, uid, ODOO_PASSWORD, opportunity_id
#     )
#     if not opportunity_info:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='Nenhuma oportunidade localizada',
#         )
#     return {'opportunity': opportunity_info}


# @router.post(
#     '/v1/',
#     summary='Cadastrar uma oportunidade (v1)',
#     status_code=status.HTTP_201_CREATED,
#     response_model=OpportunityReturn,
# )
# async def create_opportunity_v1_endpoint(opportunity_info: OpportunityDefault):
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     partner_id = get_or_create_partner(
#         opportunity_info.contact_name, models, ODOO_DB, uid, ODOO_PASSWORD
#     )

#     if not partner_id:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='Erro ao criar ou recuperar o cliente',
#         )

#     opportunity_data = opportunity_info.dict(exclude_unset=True)
#     opportunity_data.update({
#         'partner_id': partner_id,
#         'type': 'opportunity',
#     })

#     opportunity_id = create_opportunity_in_crm(
#         opportunity_data, models, ODOO_DB, uid, ODOO_PASSWORD
#     )

#     if not opportunity_id:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='Nenhuma oportunidade criada',
#         )

#     return {'opportunity_id': opportunity_id, **opportunity_data}


# @router.post(
#     '/v2',
#     summary='Cadastrar uma oportunidade (v2)',
#     status_code=status.HTTP_201_CREATED,
#     response_model=OpportunityReturn,
# )
# async def create_opportunity_v2_endpoint(opportunity_info: OpportunityDefault):
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     partner_id = opportunity_info.partner_id

#     if not partner_id:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='ID do cliente não informado',
#         )

#     opportunity_data = opportunity_info.dict(exclude_unset=True)
#     opportunity_data.update({
#         'partner_id': partner_id,
#         'type': 'opportunity',
#     })

#     try:
#         opportunity_id = create_opportunity_in_crm(
#             opportunity_data, models, ODOO_DB, uid, ODOO_PASSWORD
#         )
#     except Exception as e:
#         logger.exception(f"Erro ao criar oportunidade (v2) para {opportunity_info.name}")  # Logging melhorado
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f'Erro ao criar oportunidade: {str(e)}',
#         )

#     return {'opportunity_id': opportunity_id, **opportunity_data}


# @router.post(
#     '/with_attachment/',
#     summary='Cria uma nova oportunidade com anexo',
#     response_description='Oportunidade criada com sucesso',
#     response_model=OpportunityCreateResponse,
#     status_code=HTTPStatus.CREATED,
# )
# async def create_opportunity_with_attachment_endpoint(
#     opportunity_data: str = Form(...),
#     files: List[UploadFile] = File(...),
# ):
#     try:
#         opportunity_dict = json.loads(opportunity_data)
#         opportunity = OpportunityCreate(**opportunity_dict)
#     except json.JSONDecodeError:
#         logger.error("Formato JSON inválido para dados da oportunidade com anexo.")
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='Formato JSON inválido para os dados da oportunidade',
#         )
#     except Exception as e:
#         logger.exception("Dados da oportunidade com anexo inválidos.")
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail=f'Dados da oportunidade inválidos: {str(e)}',
#         )

#     opportunity_data_for_odoo = opportunity.dict(exclude_none=True)

#     if opportunity_data_for_odoo.get('tag_ids'):
#         opportunity_data_for_odoo['tag_ids'] = [(6, 0, opportunity_data_for_odoo['tag_ids'])]

#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     try:
#         opportunity_id = models.execute_kw(
#             ODOO_DB,
#             uid,
#             ODOO_PASSWORD,
#             'crm.lead',
#             'create',
#             [opportunity_data_for_odoo],
#         )

#         if not opportunity_id:
#             logger.error("Não foi possível criar a oportunidade (com anexo) no Odoo.")
#             raise HTTPException(
#                 status_code=HTTPStatus.BAD_REQUEST,
#                 detail='Não foi possível criar a oportunidade',
#             )

#         attachments = []
#         for file_upload in files:
#             file_content = await file_upload.read()
#             encoded_content = base64.b64encode(file_content).decode('utf-8')

#             attachment_data = {
#                 'name': file_upload.filename,
#                 'datas': encoded_content,
#                 'res_model': 'crm.lead',
#                 'res_id': opportunity_id,
#             }

#             attachment_id = models.execute_kw(
#                 ODOO_DB,
#                 uid,
#                 ODOO_PASSWORD,
#                 'ir.attachment',
#                 'create',
#                 [attachment_data],
#             )

#             attachments.append(
#                 AttachmentInfo(
#                     attachment_id=attachment_id,
#                     filename=file_upload.filename,
#                 )
#             )
#         fields_to_read_for_response = [
#             'name', 'partner_id', 'expected_revenue', 'stage_id',
#             'probability', 'company_id', 'user_id', 'team_id', 'x_studio_tese'  # Adicione os campos faltantes
#         ]
#         opportunity_details_raw = models.execute_kw(
#             ODOO_DB,
#             uid,
#             ODOO_PASSWORD,
#             'crm.lead',
#             'read',
#             [opportunity_id],
#             {'fields': fields_to_read_for_response},
#         )

#         if not opportunity_details_raw:
#             logger.error(f"Falha ao ler detalhes da oportunidade {opportunity_id} recém-criada com anexo.")
#             raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Falha ao ler oportunidade após criação.")

#         opportunity_details = opportunity_details_raw[0]

#         def get_id_from_relational(field_value):
#             if isinstance(field_value, list) and field_value:
#                 return field_value[0]
#             return field_value

#         opp_return = OpportunityReturn(
#             opportunity_id=opportunity_id,
#             name=opportunity_details.get('name'),
#             partner_id=get_id_from_relational(opportunity_details.get('partner_id')),
#             expected_revenue=opportunity_details.get('expected_revenue'),
#             stage_id=get_id_from_relational(opportunity_details.get('stage_id')),
#             user_id=get_id_from_relational(opportunity_details.get('user_id')),
#             team_id=get_id_from_relational(opportunity_details.get('team_id')),
#             x_studio_tese=opportunity_details.get('x_studio_tese') if opportunity_details.get('x_studio_tese') is not False else None,
#         )

#         return OpportunityCreateResponse(
#             message='Oportunidade criada com sucesso',
#             opportunity_id=opportunity_id,
#             opportunity_details=opp_return,
#             attachments=attachments,
#         )

#     except Exception as e:
#         logger.exception(f"Erro ao criar oportunidade com anexo para {opportunity.name if 'opportunity' in locals() else 'N/A'}")
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f'Erro ao criar oportunidade com anexo: {str(e)}',
#         )


# @router.post(
#     "/v3/",
#     summary="Cadastrar uma oportunidade com verificação/criação inteligente de empresa",
#     status_code=status.HTTP_201_CREATED,
#     response_model=OpportunityReturn,
# )
# async def create_opportunity_intelligent_endpoint(
#     opportunity_payload: OpportunityCreateIntelligent,
# ):
#     """
#     Endpoint para criar uma nova oportunidade.
#     - Verifica se a empresa (cliente) já existe pelo CNPJ.
#     - Se não existir, cadastra a empresa.
#     - Em seguida, cadastra a oportunidade vinculada à empresa.
#     """
#     try:
#         created_opportunity_dict = await create_opportunity_intelligent_async(opportunity_payload)

#         if not created_opportunity_dict:
#             logger.warning(f"A criação inteligente para '{opportunity_payload.name}' não retornou detalhes.")
#             raise HTTPException(
#                 status_code=HTTPStatus.BAD_REQUEST,
#                 detail="Não foi possível criar a oportunidade ou obter seus detalhes."
#             )

#         return OpportunityReturn(**created_opportunity_dict)

#     except HTTPException as http_exc:
#         # Log detalhado da HTTPException vinda do serviço ou de validações anteriores
#         logger.error(f"HTTPException na criação inteligente (/v3/) para '{opportunity_payload.name}': {http_exc.detail}", exc_info=getattr(http_exc, '__cause__', None))
#         raise http_exc
#     except ValueError as ve:
#         # ValueErrors podem vir, por exemplo, da limpeza do VAT se não tratados antes
#         logger.error(f"ValueError na criação inteligente (/v3/) para '{opportunity_payload.name}': {str(ve)}", exc_info=True)
#         raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(ve))
#     except Exception as e:
#         # Erro genérico e inesperado
#         logger.exception(f"Erro inesperado na criação inteligente (/v3/) para '{opportunity_payload.name}': {str(e)}")
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f"Ocorreu um erro inesperado ao processar sua solicitação: {str(e)}"
#         )
