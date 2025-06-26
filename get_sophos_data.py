#!/usr/bin/env python3
import json
import sys
import logging
from urllib import request, parse
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuração .env ---
sophos_client_id = os.getenv("SOPHOS_CLIENT_ID")
sophos_client_secret = os.getenv("SOPHOS_CLIENT_SECRET")
sophos_tenant_id = os.getenv("SOPHOS_TENANT_ID")
sophos_auth_host = os.getenv("SOPHOS_API_AUTH_HOST")
sophos_data_host = os.getenv("SOPHOS_API_DATA_HOST")
# ------------------
LOG_FILE = "/var/log/sophos-api.log"
#LOG_FILE = "sophos-api.log" (debbugar no windows)
CURSOR_FILE_PREFIX = "/var/ossec/wodles/sophos_cursor"
#CURSOR_FILE_PREFIX = "sophos_cursor"(debbugar no windows)
# ------------------

if not all([sophos_client_id, sophos_client_secret, sophos_auth_host, sophos_data_host, sophos_tenant_id]):
    print("Erro Crítico: Uma ou mais variáveis de ambiente da Sophos não foram definidas.")
    print("Verifique se o arquivo .env existe e contém SOPHOS_CLIENT_ID, SOPHOS_CLIENT_SECRET e SOPHOS_API_HOST.")
    exit(1) # Encerra o script se as credenciais estiverem faltando

logger = logging.getLogger('sophos_siem')
logger.setLevel(logging.INFO)
try:
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
except PermissionError:
    sys.stderr.write(f"ERRO: Sem permissão para escrever em {LOG_FILE}.\n")
    sys.exit(1)

def read_cursor(endpoint_type):
    """Lê o último cursor salvo do arquivo específico."""
    cursor_file = f"{CURSOR_FILE_PREFIX}_{endpoint_type}.txt"
    if os.path.exists(cursor_file):
        with open(cursor_file, 'r') as f:
            return f.read().strip()
    return None

def save_cursor(cursor_value, endpoint_type):
    """Salva o novo cursor no arquivo específico."""
    cursor_file = f"{CURSOR_FILE_PREFIX}_{endpoint_type}.txt"
    with open(cursor_file, 'w') as f:
        f.write(cursor_value)

def get_sophos_token():
    auth_url = f"https://{sophos_auth_host}/api/v2/oauth2/token"
    try:
        auth_data = parse.urlencode({"grant_type": "client_credentials", "client_id": sophos_client_id, "client_secret": sophos_client_secret, "scope": "token"}).encode("utf-8")
        req = request.Request(auth_url, data=auth_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8")).get("access_token")
    except Exception as e:
        sys.stderr.write(f"EXCEÇÃO AO OBTER TOKEN: {e}\n")
    return None

def fetch_sophos_data(access_token, endpoint_type):
    """Busca dados da Sophos (alerts ou events) em loop usando o cursor correto."""
    current_cursor = read_cursor(endpoint_type)
    total_items_fetched = 0

    while True:
        params = {'limit': 1000}
        if current_cursor:
            params['cursor'] = current_cursor

        query_string = parse.urlencode(params)
        data_url = f"https://{sophos_data_host}/siem/v1/{endpoint_type}?{query_string}"

        sys.stderr.write(f"INFO: Buscando dados de: {data_url}\n")

        try:
            req_sophos = request.Request(data_url)
            req_sophos.add_header("Authorization", f"Bearer {access_token}")
            req_sophos.add_header("X-Tenant-ID", sophos_tenant_id)

            with request.urlopen(req_sophos, timeout=60) as response_sophos:
                if response_sophos.status != 200:
                    sys.stderr.write(f"ERRO: A API da Sophos retornou o status {response_sophos.status}\n")
                    break

                response_data = json.loads(response_sophos.read().decode("utf-8"))
                items = response_data.get("items", [])
                item_count = len(items)
                total_items_fetched += item_count

                if item_count > 0:
                    for item in items:
                        logger.info(json.dumps(item))

                has_more = response_data.get("has_more", False)
                next_cursor = response_data.get("next_cursor")

                if next_cursor:
                    save_cursor(next_cursor, endpoint_type)

                if not has_more:
                    break
                else:
                    current_cursor = next_cursor

        except Exception as e:
            sys.stderr.write(f"EXCEÇÃO ao buscar dados: {e}\n")
            break

    sys.stderr.write(f"SUCESSO: Total de {total_items_fetched} items do tipo '{endpoint_type}' coletados.\n")

if __name__ == "__main__":
    if sophos_client_id.startswith("SEU_"):
        sys.stderr.write("ERRO CRÍTICO: Preencha as credenciais no script.\n")
        sys.exit(1)

    endpoint_to_fetch = 'events' # Padrão
    if len(sys.argv) > 1 and sys.argv[1] in ["alerts", "events"]:
        endpoint_to_fetch = sys.argv[1]

    token = get_sophos_token()
    if token:
        fetch_sophos_data(token, endpoint_to_fetch)
    else:
        sys.stderr.write("FALHA: Impossível continuar sem um token da API da Sophos.\n")
