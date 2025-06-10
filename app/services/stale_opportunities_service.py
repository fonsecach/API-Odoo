import io
import json
import logging
from datetime import datetime, timedelta

import httpx
import pandas as pd
import pytz

from app.services.async_odoo_client import AsyncOdooClient
from app.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL_ENDPOINT_URL = "https://leitura-despachos-twilight-cherry-7550.fly.dev/email/send"


async def get_odoo_client() -> AsyncOdooClient:
    """Obtém uma instância do cliente Odoo assíncrono."""
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )


async def check_and_report_stale_opportunities():
    """
    Busca oportunidades no Odoo que não são atualizadas há 72 horas nos estágios 8 ou 9,
    gera um relatório em Excel e o envia por e-mail.
    """
    logger.info("Iniciando verificação de oportunidades estagnadas...")

    try:
        sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
        now_in_sao_paulo = datetime.now(sao_paulo_tz)
        cutoff_datetime_sp = now_in_sao_paulo - timedelta(hours=72)
        
        cutoff_datetime_utc = cutoff_datetime_sp.astimezone(pytz.utc)
        cutoff_str_utc = cutoff_datetime_utc.strftime('%Y-%m-%d %H:%M:%S')

        logger.info(f"Buscando oportunidades não atualizadas desde: {cutoff_str_utc} (UTC)")

        client = await get_odoo_client()
        domain = [
            ('stage_id', 'in', [8, 9]),
            ('write_date', '<=', cutoff_str_utc),
        ]
        fields = ['id', 'name', 'partner_id', 'user_id', 'team_id']
        
        opportunities = await client.search_read('crm.lead', domain, fields=fields)

        if not opportunities:
            logger.info("Nenhuma oportunidade estagnada encontrada. Nenhuma ação necessária.")
            return

        logger.info(f"Encontradas {len(opportunities)} oportunidades estagnadas.")

        processed_data = []
        for opp in opportunities:
            processed_data.append({
                'ID da Oportunidade': opp.get('id'),
                'Nome': opp.get('name', 'N/A'),
                'Cliente': opp.get('partner_id')[1] if opp.get('partner_id') else 'N/A',
                'Vendedor': opp.get('user_id')[1] if opp.get('user_id') else 'N/A',
                'Equipe de Vendas': opp.get('team_id')[1] if opp.get('team_id') else 'N/A',
            })
        
        df = pd.DataFrame(processed_data)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Oportunidades Estagnadas')
        excel_buffer.seek(0)
        # todo Substituir 'cleiton.fonseca@tributojusto.com.br' por seu endereço de e-mail
        email_data = {
            'to': 'marcio.faria@tributojusto.com.br',
            # 'to': 'bruna.veiga@tributojusto.com.br',
            'subject': 'TESTE | Relatório de 72 horas CRM/Odoo',
            'template_name': 'welcome_email.html',
            'body_json': json.dumps({"name": "Marcio"}),
        }
        
        files = {
            'attachments': ('relatorio_oportunidades_72h.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        async with httpx.AsyncClient() as email_client:
            logger.info(f"Enviando relatório para {email_data['to']}...")
            response = await email_client.post(EMAIL_ENDPOINT_URL, data=email_data, files=files, timeout=30.0)

            if response.status_code == 202:
                logger.info("Relatório enviado com sucesso por e-mail.")
            else:
                logger.error(f"Falha ao enviar e-mail. Status: {response.status_code}, Resposta: {response.text}")

    except Exception as e:
        logger.exception(f"Ocorreu um erro inesperado no serviço de relatório: {e}")