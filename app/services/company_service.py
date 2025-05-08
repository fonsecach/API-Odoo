import logging
from typing import Any, Dict, List, Optional, Union

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import CompanyDefault, ContactUpdate
from app.services.async_odoo_client import AsyncOdooClient
from app.utils.utils import clean_vat

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
PARTNER_MODEL = 'res.partner'
PARTNER_DEFAULT_FIELDS = ['id', 'name', 'vat', 'email', 'phone', 'country_id']


async def get_odoo_client() -> AsyncOdooClient:
    """
    Obtém uma instância do cliente Odoo assíncrono.
    Reutiliza conexões existentes quando possível.
    """
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )


async def get_clients_info(limit: int = 100, offset: int = 0,
                         fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Obtém informações de vários clientes/empresas de forma assíncrona.
    
    Args:
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        fields: Campos específicos a serem retornados (usa padrão se None)
        
    Returns:
        Lista de empresas ou lista vazia em caso de erro
    """
    client = await get_odoo_client()

    if fields is None:
        fields = PARTNER_DEFAULT_FIELDS

    try:
        return await client.search_read(
            PARTNER_MODEL,
            [],
            fields=fields,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f'Erro ao buscar e ler informações das empresas: {e}')
        return []


async def get_company_by_vat(vat: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Obtém uma empresa pelo VAT (CNPJ) de forma assíncrona.
    
    Args:
        vat: Número do VAT (CNPJ)
        fields: Campos específicos a serem retornados (usa padrão se None)
        
    Returns:
        Lista de empresas correspondentes ou lista vazia se não encontrada
    """
    client = await get_odoo_client()

    if fields is None:
        fields = PARTNER_DEFAULT_FIELDS

    try:
        vat = clean_vat(vat)  # Limpa o VAT antes de buscar
        return await client.search_read(
            PARTNER_MODEL,
            [['vat', '=', vat]],
            fields=fields
        )
    except Exception as e:
        logger.error(f'Erro ao buscar empresa pelo VAT {vat}: {e}')
        return []


async def fetch_client_by_name(name: str, fields: Optional[List[str]] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Obtém empresas que correspondam ao nome de forma parcial e case-insensitive, de forma assíncrona.
    
    Args:
        name: Nome ou parte do nome da empresa
        fields: Campos específicos a serem retornados (usa padrão se None)
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        
    Returns:
        Lista de empresas correspondentes ou lista vazia se não encontrada
    """
    client = await get_odoo_client()

    if fields is None:
        fields = PARTNER_DEFAULT_FIELDS

    try:
        # Busca por correspondência parcial com "ilike"
        return await client.search_read(
            PARTNER_MODEL,
            [['name', 'ilike', name]],  # 'ilike' para busca parcial case-insensitive
            fields=fields,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f'Erro ao buscar clientes pelo nome {name}: {e}')
        return []


async def get_company_by_id(id: int, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Obtém uma empresa pelo ID de forma assíncrona.
    
    Args:
        id: ID da empresa
        fields: Campos específicos a serem retornados (usa padrão se None)
        
    Returns:
        Lista com a empresa correspondente ou lista vazia se não encontrada
    """
    client = await get_odoo_client()

    if fields is None:
        fields = PARTNER_DEFAULT_FIELDS

    try:
        return await client.search_read(
            PARTNER_MODEL,
            [['id', '=', id]],
            fields=fields
        )
    except Exception as e:
        logger.error(f'Erro ao buscar empresa pelo ID {id}: {e}')
        return []


async def create_company(company_info: Union[CompanyDefault, Dict[str, Any]]) -> Optional[int]:
    """
    Cria uma nova empresa no Odoo de forma assíncrona.
    
    Args:
        company_info: Dados da empresa a ser criada (CompanyDefault ou Dict)
        
    Returns:
        ID da empresa criada ou None em caso de erro
    """
    client = await get_odoo_client()

    try:
        # Converte para dicionário se for um modelo Pydantic
        if hasattr(company_info, 'dict'):
            company_data = company_info.dict(exclude_unset=True)
        else:
            company_data = dict(company_info)

        # Verifica se já existe uma empresa com o mesmo VAT
        existing = await client.search_read(
            PARTNER_MODEL,
            [['vat', '=', company_data['vat']]],
            fields=['id'],
            limit=1
        )

        if existing:
            logger.warning(f"Empresa com VAT {company_data['vat']} já está cadastrada")
            return None

        return await client.create(PARTNER_MODEL, company_data)
    except Exception as e:
        logger.error(f'Erro ao criar empresa: {e}')
        return None


async def update_company(company_id: int, company_info: Union[CompanyDefault, Dict[str, Any]]) -> bool:
    """
    Atualiza uma empresa existente no Odoo de forma assíncrona.
    
    Args:
        company_id: ID da empresa a ser atualizada
        company_info: Dados da empresa para atualização (CompanyDefault ou Dict)
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        # Converte para dicionário se for um modelo Pydantic
        if hasattr(company_info, 'dict'):
            company_data = company_info.dict(exclude_unset=True)
        else:
            company_data = dict(company_info)

        return await client.write(PARTNER_MODEL, company_id, company_data)
    except Exception as e:
        logger.error(f'Erro ao atualizar empresa: {e}')
        return False


async def delete_company(company_id: int) -> bool:
    """
    Exclui uma empresa do Odoo de forma assíncrona.
    
    Args:
        company_id: ID da empresa a ser excluída
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        return await client.unlink(PARTNER_MODEL, company_id)
    except Exception as e:
        logger.error(f'Erro ao excluir empresa: {e}')
        return False


async def update_contact_fields(contact_id: int, contact_update: ContactUpdate) -> bool:
    """
    Atualiza campos específicos de um contato/cliente de forma assíncrona.
    
    Args:
        contact_id: ID do contato a ser atualizado
        contact_update: Dados para atualização (ContactUpdate)
        
    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        update_data = {}

        # Atualiza o certificado se fornecido
        if contact_update.x_studio_certificado is not None:
            update_data['x_studio_certificado'] = contact_update.x_studio_certificado

        # Atualiza a validade da procuração se fornecida
        if contact_update.x_studio_validade_da_procuracao is not None:
            update_data['x_studio_validade_da_procuracao'] = contact_update.x_studio_validade_da_procuracao.strftime('%Y-%m-%d')

        # Retorna True se não houver campos para atualizar
        if not update_data:
            logger.info(f"Nenhum campo para atualizar para o contato ID {contact_id}")
            return True

        return await client.write(PARTNER_MODEL, contact_id, update_data)
    except Exception as e:
        logger.error(f'Erro ao atualizar campos do contato: {e}')
        return False


async def get_or_create_partner(contact_name: str) -> Optional[int]:
    """
    Verifica se o cliente já existe, senão cria um novo de forma assíncrona.
    
    Args:
        contact_name: Nome do contato/cliente
        
    Returns:
        ID do cliente/parceiro existente ou novo, None em caso de erro
    """
    client = await get_odoo_client()

    try:
        # Tenta encontrar o cliente pelo nome
        existing_partners = await client.search_read(
            PARTNER_MODEL,
            [['name', '=', contact_name]],
            fields=['id']
        )

        if existing_partners:
            return existing_partners[0]['id']  # Retorna o ID se já existir

        # Se não existir, cria um novo cliente
        return await client.create(PARTNER_MODEL, {'name': contact_name})
    except Exception as e:
        logger.error(f'Erro ao buscar/criar cliente: {e}')
        return None
