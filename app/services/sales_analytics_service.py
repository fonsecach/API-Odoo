import logging
from datetime import datetime
from typing import Dict, List

import numpy as np  # Importando NumPy para cálculos mais precisos

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> datetime:
    """
    Converte string de data no formato dd-mm-aaaa para objeto datetime.
    """
    return datetime.strptime(date_str, '%d-%m-%Y')


def format_date_for_odoo(date: datetime) -> str:
    """
    Formata objeto datetime para string no formato esperado pelo Odoo (YYYY-MM-DD).
    """
    return date.strftime('%Y-%m-%d')


def format_decimal(value: float) -> float:
    """
    Formata um valor com 2 casas decimais usando NumPy para maior precisão.
    """
    return float(np.round(value, 2))


def get_won_opportunities(
    models, db: str, uid: int, password: str, start_date: str, end_date: str
) -> List[Dict]:
    """
    Obtém as oportunidades ganhas e ativas no período especificado (stage_id = 10).
    """
    try:
        # Domínio para buscar oportunidades ganhas, ativas e dentro do período
        domain = [
            ('type', '=', 'opportunity'),
            ('stage_id', '=', 10),  # Estágio "Contrato assinado"
            ('active', '=', True),  # Apenas oportunidades ativas
            '|',  # OR para os critérios de data
            ('date_closed', '>=', start_date),
            ('date_last_stage_update', '>=', start_date),
            '|',
            ('date_closed', '<=', end_date),
            ('date_last_stage_update', '<=', end_date),
        ]

        logger.info(
            f'Buscando oportunidades ganhas e ativas (estágio 10) no período {start_date} até {end_date}'
        )

        # Buscar oportunidades ganhas com todos os campos necessários
        opportunities = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'search_read',
            [domain],
            {
                'fields': [
                    'id',
                    'name',
                    'team_id',
                    'user_id',
                    'expected_revenue',
                    'date_closed',
                    'partner_id',
                    'x_studio_tese',
                    'date_last_stage_update',
                    'stage_id',
                    'active',
                    'x_studio_selection_field_37f_1ibrq64l3',
                    'x_studio_segmento',
                ]
            },
        )

        logger.info(
            f'Encontradas {len(opportunities)} oportunidades ganhas e ativas no período'
        )

        return opportunities
    except Exception as e:
        logger.error(f'Erro ao buscar oportunidades ganhas: {e}')

        # Se o campo 'active' não estiver disponível, tente sem esse filtro
        try:
            domain = [
                ('type', '=', 'opportunity'),
                ('stage_id', '=', 10),  # Estágio "Contrato assinado"
                '|',  # OR para os critérios de data
                ('date_closed', '>=', start_date),
                ('date_last_stage_update', '>=', start_date),
                '|',
                ('date_closed', '<=', end_date),
                ('date_last_stage_update', '<=', end_date),
            ]

            logger.info("Tentando busca alternativa sem filtro de 'active'")

            opportunities = models.execute_kw(
                db,
                uid,
                password,
                'crm.lead',
                'search_read',
                [domain],
                {
                    'fields': [
                        'id',
                        'name',
                        'team_id',
                        'user_id',
                        'expected_revenue',
                        'date_closed',
                        'partner_id',
                        'x_studio_tese',
                        'date_last_stage_update',
                        'stage_id',
                        'x_studio_selection_field_37f_1ibrq64l3',
                        'x_studio_segmento',
                    ]
                },
            )

            logger.info(
                f"Encontradas {len(opportunities)} oportunidades ganhas no período (sem filtro 'active')"
            )

            return opportunities
        except Exception as e2:
            logger.error(f'Erro na busca alternativa: {e2}')
            return []


def prepare_opportunity_details(
    opportunities: List[Dict], models, db: str, uid: int, password: str
) -> List[Dict]:
    """
    Prepara o objeto detalhado de oportunidades com as informações solicitadas.

    Args:
        opportunities: Lista de oportunidades a serem processadas
        models: Objeto de modelos do Odoo
        db: Nome do banco de dados
        uid: ID do usuário autenticado
        password: Senha do usuário

    Returns:
        Lista de objetos detalhados de oportunidades
    """
    opportunity_details = []

    for opp in opportunities:
        try:
            # Formatação da data de fechamento (se disponível)
            date_closed = opp.get('date_closed')
            if date_closed:
                # Tentar formatar a data para um formato mais amigável
                try:
                    date_obj = datetime.strptime(
                        date_closed, '%Y-%m-%d %H:%M:%S'
                    )
                    date_closed = date_obj.strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    # Manter o formato original se não for possível converter
                    pass

            # Formatação da receita esperada para 2 casas decimais
            expected_revenue = format_decimal(
                float(opp.get('expected_revenue', 0))
            )

            # Obter o VAT do parceiro se disponível
            vat = None
            if opp.get('partner_id') and opp['partner_id'][0]:
                # Busca o parceiro para obter o VAT
                try:
                    partner = models.execute_kw(
                        db,
                        uid,
                        password,
                        'res.partner',
                        'search_read',
                        [[['id', '=', opp['partner_id'][0]]]],
                        {'fields': ['vat']},
                    )
                    if partner and partner[0].get('vat'):
                        vat = partner[0]['vat']
                except Exception as e:
                    logger.error(
                        f'Erro ao buscar VAT do parceiro ID {opp["partner_id"][0]}: {e}'
                    )

            # Garantir que commercial_partner seja string ou None
            commercial_partner = opp.get(
                'x_studio_selection_field_37f_1ibrq64l3'
            )
            if commercial_partner is False:
                commercial_partner = None
            elif commercial_partner is not None:
                commercial_partner = str(commercial_partner)

            # Garantir que segment seja string ou None
            segment = opp.get('x_studio_segmento')
            if segment is False:
                segment = None
            elif segment is not None:
                segment = str(segment)

            # Preparar o objeto de detalhe da oportunidade
            detail = {
                'id': opp['id'],
                'name': opp.get('name', ''),
                'client': opp.get('partner_id') and opp['partner_id'][1] or '',
                'vat': vat,  # Adicionar o VAT ao detalhe da oportunidade
                'expected_revenue': expected_revenue,
                'date_closed': date_closed or '',
                'sales_person': opp.get('user_id') and opp['user_id'][1] or '',
                'commercial_partner': commercial_partner,  # Já convertido para string ou None
                'segment': segment,  # Já convertido para string ou None
                'sales_team': opp.get('team_id') and opp['team_id'][1] or '',
            }

            opportunity_details.append(detail)
        except Exception as e:
            logger.error(
                f'Erro ao processar detalhes da oportunidade ID {opp.get("id", "desconhecido")}: {e}'
            )
            # Continuar para a próxima oportunidade se houver erro
            continue

    return opportunity_details


def process_opportunities_analytics(
    models,
    db: str,
    uid: int,
    password: str,
    opportunities: List[Dict],
    start_date: str,
    end_date: str,
) -> Dict:
    """
    Processa métricas de análise a partir das oportunidades ganhas.
    Utiliza NumPy para maior precisão nos cálculos.
    """
    # Estruturas para armazenar os resultados
    teams_data = {}
    users_data = {}
    products_data = {}

    # Arrays para calcular totais com NumPy
    team_totals = {}

    # Iterar sobre as oportunidades para calcular as métricas
    for opp in opportunities:
        # Pular oportunidades sem time ou vendedor definido
        if not opp.get('team_id') or not opp.get('user_id'):
            continue

        team_id = opp['team_id'][0]
        team_name = opp['team_id'][1]
        user_id = opp['user_id'][0]
        user_name = opp['user_id'][1]
        amount = float(
            opp.get('expected_revenue', 0)
        )  # Converter para float explicitamente

        # Adicionar aos arrays para cálculos NumPy por equipe
        if team_id not in team_totals:
            team_totals[team_id] = []
        team_totals[team_id].append(amount)

        # Processar dados por equipe
        if team_id not in teams_data:
            teams_data[team_id] = {
                'id': team_id,
                'name': team_name,
                'total_contracts': 0,
                'total_amount': 0.0,
                'expected_revenue_partial': 0.0,
            }

        teams_data[team_id]['total_contracts'] += 1
        teams_data[team_id]['total_amount'] = np.float64(
            teams_data[team_id]['total_amount']
        ) + np.float64(amount)

        # Processar dados por vendedor
        if user_id not in users_data:
            users_data[user_id] = {
                'id': user_id,
                'name': user_name,
                'team_id': team_id,
                'team_name': team_name,
                'total_contracts': 0,
                'total_amount': 0.0,
            }

        users_data[user_id]['total_contracts'] += 1
        users_data[user_id]['total_amount'] = np.float64(
            users_data[user_id]['total_amount']
        ) + np.float64(amount)

        # Adicionar dados por tese (produto)
        if opp.get('x_studio_tese'):
            tese = opp['x_studio_tese']

            if tese not in products_data:
                products_data[tese] = {
                    'id': None,
                    'name': tese,
                    'total_sales': 0,
                    'total_amount': 0.0,
                }

            products_data[tese]['total_sales'] += 1
            products_data[tese]['total_amount'] = np.float64(
                products_data[tese]['total_amount']
            ) + np.float64(amount)

    # Calcular expected_revenue_partial com maior precisão usando NumPy
    for team_id, amounts in team_totals.items():
        if team_id in teams_data:
            # Usar NumPy para soma com precisão estendida
            total = np.sum(np.array(amounts, dtype=np.float64))
            teams_data[team_id]['total_amount'] = float(total)
            # Calcular os 8% com maior precisão
            teams_data[team_id]['expected_revenue_partial'] = float(
                np.multiply(total, np.float64(0.08))
            )

    # Formatar valores decimais com 2 casas utilizando NumPy para maior precisão
    for team in teams_data.values():
        team['total_amount'] = format_decimal(team['total_amount'])
        team['expected_revenue_partial'] = format_decimal(
            team['expected_revenue_partial']
        )

    for user in users_data.values():
        user['total_amount'] = format_decimal(user['total_amount'])

    for product in products_data.values():
        product['total_amount'] = format_decimal(product['total_amount'])

    # Formatar para retorno
    return {
        'period': {'start_date': start_date, 'end_date': end_date},
        'teams': list(teams_data.values()),
        'users': list(users_data.values()),
        'products': list(products_data.values()),
    }


def get_sales_analytics(
    models, db: str, uid: int, password: str, start_date: str, end_date: str
) -> Dict:
    """
    Obtém métricas de análise de vendas por equipe, vendedor e produto.
    Baseado apenas nos dados do CRM, sem buscar pedidos de venda.
    """
    try:
        # Converter datas para o formato do Odoo
        start_date_odoo = format_date_for_odoo(parse_date(start_date))
        end_date_odoo = format_date_for_odoo(parse_date(end_date))

        logger.info(
            f'Iniciando análise de vendas para o período: {start_date} até {end_date}'
        )

        # Obter oportunidades ganhas no período
        won_opportunities = get_won_opportunities(
            models, db, uid, password, start_date_odoo, end_date_odoo
        )

        if not won_opportunities:
            logger.warning('Nenhuma oportunidade ganha encontrada no período')

            return {
                'period': {'start_date': start_date, 'end_date': end_date},
                'teams': [],
                'users': [],
                'products': [],
                'opportunities': [],
            }

        # Preparar os detalhes das oportunidades - Agora passando os parâmetros corretos
        opportunity_details = prepare_opportunity_details(
            won_opportunities, models, db, uid, password
        )

        # Processar as métricas
        analytics_data = process_opportunities_analytics(
            models, db, uid, password, won_opportunities, start_date, end_date
        )

        # Adicionar os detalhes das oportunidades ao resultado
        analytics_data['opportunities'] = opportunity_details

        return analytics_data
    except Exception as e:
        logger.error(f'Erro ao gerar análise de vendas: {e}')
        raise
