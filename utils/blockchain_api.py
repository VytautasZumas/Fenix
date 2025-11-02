import requests
import json
from decimal import Decimal, getcontext
import time

# Configura a precisão para operações com Decimal
getcontext().prec = 30

# --- REMOVIDO O DICIONÁRIO DE PREÇOS MOCKADOS ---

# --- NOVA CONFIGURAÇÃO PARA API DE PREÇOS (COINGECKO) E MAPEAMENTO DE IDS ---
PRICE_API_CONFIG = {
    "base_url": "https://api.coingecko.com/api/v3/simple/price",
    "ids_map": {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BSC": "binancecoin",  # A moeda nativa da BSC é o BNB
        "MATIC": "matic-network",
        "TRX": "tron",
        "USDT": "tether",
        # Redes L2 que usam ETH como gás
        "BASE": "ethereum",
        "OPTIMISM": "ethereum",
        "ARBITRUM": "ethereum"
    }
}

# --- URLs Base das APIs e Contratos USDT/Tokens ---
API_CONFIG = {
    "BTC": {
        "base_url": "https://blockstream.info/api",
        "explorer_link_base": "https://web3.okx.com/pt-br/explorer/bitcoin/address/"
    },
    "EVM_COMMON": {
        "base_url_v2_unified": "https://api.etherscan.io/v2/api",
        "explorer_link_base": {
            "ETH": "https://etherscan.io/address/",
            "BSC": "https://bscscan.com/address/",
            "MATIC": "https://polygonscan.com/address/",
            "BASE": "https://basescan.org/address/",
            "OPTIMISM": "https://optimistic.etherscan.io/address/",
            "ARBITRUM": "https://arbiscan.io/address/",
        },
        "chain_ids": {
            "ETH": 1, "BSC": 56, "MATIC": 137, "BASE": 8453, "OPTIMISM": 10, "ARBITRUM": 42161,
        },
        "usdt_contracts": {
            "ETH": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "BSC": "0x55d398326f99059ff775485246999027b3197955",
            "MATIC": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
            "BASE": "0x833589fCD6eDb6E08f4c7C32D4f7B5ab9e6d09",
            "OPTIMISM": "0x94b008aa00579c1307b0ef2c499ad98a8a508789",
            "ARBITRUM": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        }
    },
    "TRX": {
        "base_url": "https://api.trongrid.io",
        "explorer_link_base": "https://tronscan.org/#/address/",
        "usdt_contract": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    }
}

# --- NOVA FUNÇÃO PARA BUSCAR PREÇOS EM TEMPO REAL ---
def get_real_time_prices(asset_ids):
    """
    Busca os preços em USD para uma lista de IDs de ativos usando a API da CoinGecko.
    asset_ids: Uma lista de strings com os IDs da CoinGecko (ex: ['bitcoin', 'ethereum']).
    """
    if not asset_ids:
        return {}

    # Garante que os IDs sejam únicos para não pedir o mesmo preço duas vezes
    unique_ids = list(set(asset_ids))
    
    url = PRICE_API_CONFIG["base_url"]
    params = {
        "ids": ",".join(unique_ids),
        "vs_currencies": "usd"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        price_data = response.json()
        
        # Converte os preços para Decimal para manter a precisão
        prices_decimal = {asset_id: Decimal(data["usd"]) for asset_id, data in price_data.items()}
        print(f"DEBUG: Preços em tempo real obtidos: {prices_decimal}")
        return prices_decimal
        
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Não foi possível buscar os preços da CoinGecko: {e}")
        return {} # Retorna um dicionário vazio em caso de erro

# --- Função Auxiliar para Requisições HTTP (sem modificações) ---
def _fetch_data(url, params=None, api_key=None, headers=None):
    if params is None:
        params = {}
    if api_key and isinstance(api_key, str) and api_key.strip(): 
        if "trongrid.io" in url:
            headers = headers if headers is not None else {}
            headers["TRON-PRO-API-KEY"] = api_key.strip()
        else: # Etherscan-like
             params["apikey"] = api_key.strip()
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status() 
        if response.status_code == 204:
            return {"message": "No Content from API."}
        data = response.json()
        if isinstance(data, dict) and data.get("status") == "0":
            message = data.get("message", "").lower()
            if "no transactions found" in message or "no records found" in message or "zero balance" in message:
                return {"status": "1", "result": "0"}
            else:
                return {"message": data.get("message", "Sem resultados ou limite de taxa excedido.")}
        if "trongrid.io" in url and isinstance(data, dict) and data.get("success") is False:
             return {"message": data.get("message", "Erro na API Tron.")}
        return data
    except requests.exceptions.RequestException as e:
        return {"error_fatal": f"Erro na requisição da API: {e}"}
    except json.JSONDecodeError:
        return {"error_fatal": "Resposta inválida da API (não é JSON)."}


# --- Funções de Consulta Específicas (MODIFICADAS) ---

def get_btc_data(address, api_key=None):
    """Obtém saldo e histórico para Bitcoin usando Blockstream.info."""
    config = API_CONFIG["BTC"]
    summary_url = f"{config['base_url']}/address/{address}"
    summary_data = _fetch_data(summary_url)

    if isinstance(summary_data, dict) and summary_data.get("error_fatal"):
        return {"error_fatal": summary_data["error_fatal"]}

    # Garante que os dados de stats existam antes de acessá-los
    chain_stats = summary_data.get("chain_stats", {})
    mempool_stats = summary_data.get("mempool_stats", {})
    
    funded_satoshi = Decimal(chain_stats.get("funded_txo_sum", 0)) + Decimal(mempool_stats.get("funded_txo_sum", 0))
    spent_satoshi = Decimal(chain_stats.get("spent_txo_sum", 0)) + Decimal(mempool_stats.get("spent_txo_sum", 0))
    tx_count = chain_stats.get("tx_count", 0) + mempool_stats.get("tx_count", 0)
    
    balance_satoshi_net = funded_satoshi - spent_satoshi
    balance_btc = balance_satoshi_net / Decimal("100000000")
    
    balance_usd = Decimal(0)
    
    # Busca o preço apenas se houver saldo
    if balance_btc > 0:
        btc_id = PRICE_API_CONFIG["ids_map"]["BTC"]
        prices = get_real_time_prices([btc_id])
        if prices and btc_id in prices:
            balance_usd = balance_btc * prices[btc_id]

    return {
        "balance_crypto": balance_btc,
        "balance_usd": balance_usd,
        "has_transactions": tx_count > 0,
        "has_real_balance": balance_satoshi_net > 0,
        "explorer_link": f"{config['explorer_link_base']}{address}",
        "balance_satoshi": balance_satoshi_net  # <-- AQUI ESTÁ A CORREÇÃO
    }

def get_evm_data(address, network, api_key=None):
    evm_common_config = API_CONFIG["EVM_COMMON"]
    base_url_v2_unified = evm_common_config["base_url_v2_unified"]
    chain_id = evm_common_config["chain_ids"][network]
    usdt_contract_address = evm_common_config["usdt_contracts"][network]
    
    balance_native = Decimal(0)
    balance_usdt = Decimal(0)
    has_transactions = False
    
    required_price_ids = []

    def _get_v2_params(action_name):
        return {"module": "account", "action": action_name, "address": address, "chainid": chain_id, "tag": "latest"}

    # 1. Saldo da moeda nativa
    native_balance_data = _fetch_data(base_url_v2_unified, params=_get_v2_params("balance"), api_key=api_key)
    if isinstance(native_balance_data, dict) and native_balance_data.get("status") == "1":
        balance_wei = Decimal(native_balance_data.get("result", "0"))
        balance_native = balance_wei / Decimal("1e18")
        # MODIFICAÇÃO: Se houver saldo, marca que precisa do preço da moeda nativa
        if balance_native > 0:
            native_coin_id = PRICE_API_CONFIG["ids_map"][network]
            required_price_ids.append(native_coin_id)

    # 2. Saldo de USDT
    if usdt_contract_address:
        usdt_params = _get_v2_params("tokenbalance")
        usdt_params["contractaddress"] = usdt_contract_address
        usdt_balance_data = _fetch_data(base_url_v2_unified, params=usdt_params, api_key=api_key)
        if isinstance(usdt_balance_data, dict) and usdt_balance_data.get("status") == "1":
            balance_usdt_raw = Decimal(usdt_balance_data.get("result", "0"))
            balance_usdt = balance_usdt_raw / Decimal("1e6") # USDT tem 6 decimais
            # MODIFICAÇÃO: Se houver saldo de USDT, marca que precisa do preço do Tether
            if balance_usdt > 0:
                required_price_ids.append(PRICE_API_CONFIG["ids_map"]["USDT"])

    # 3. Histórico de transações (verificação)
    tx_list_data = _fetch_data(base_url_v2_unified, params=_get_v2_params("txlist"), api_key=api_key)
    if isinstance(tx_list_data, dict) and tx_list_data.get("status") == "1" and isinstance(tx_list_data.get("result"), list) and len(tx_list_data["result"]) > 0:
        has_transactions = True
    
    if not has_transactions and usdt_contract_address:
        token_tx_params = _get_v2_params("tokentx")
        token_tx_params["contractaddress"] = usdt_contract_address
        token_tx_data = _fetch_data(base_url_v2_unified, params=token_tx_params, api_key=api_key)
        if isinstance(token_tx_data, dict) and token_tx_data.get("status") == "1" and isinstance(token_tx_data.get("result"), list) and len(token_tx_data["result"]) > 0:
            has_transactions = True

    # MODIFICAÇÃO: Busca todos os preços necessários de uma vez e calcula o valor em USD
    total_usd_balance = Decimal(0)
    prices = get_real_time_prices(required_price_ids)

    if balance_native > 0:
        native_coin_id = PRICE_API_CONFIG["ids_map"][network]
        if native_coin_id in prices:
            total_usd_balance += balance_native * prices[native_coin_id]

    if balance_usdt > 0:
        usdt_id = PRICE_API_CONFIG["ids_map"]["USDT"]
        if usdt_id in prices:
            total_usd_balance += balance_usdt * prices[usdt_id]

    return {
        "balance_crypto": balance_native + balance_usdt, # Soma de ativos, pode não ser ideal mas serve como total
        "balance_usd": total_usd_balance,
        "has_transactions": has_transactions,
        "explorer_link": f"{evm_common_config['explorer_link_base'][network]}{address}",
        "has_real_balance": (balance_native > 0 or balance_usdt > 0)
    }


def get_trx_data(address, api_key=None):
    config = API_CONFIG["TRX"]
    balance_trx = Decimal(0)
    balance_usdt = Decimal(0)
    required_price_ids = []

    # 1. Obter saldo nativo e de tokens
    account_info_url = f"{config['base_url']}/v1/accounts/{address}"
    account_data = _fetch_data(account_info_url, api_key=api_key)

    if isinstance(account_data, dict) and "data" in account_data and len(account_data["data"]) > 0:
        details = account_data["data"][0]
        balance_trx = Decimal(details.get("balance", 0)) / Decimal("1e6")
        if balance_trx > 0:
            required_price_ids.append(PRICE_API_CONFIG["ids_map"]["TRX"])

        usdt_contract = config.get("usdt_contract")
        
        # CORREÇÃO: trc20 é um dicionário, não uma lista
        if usdt_contract and "trc20" in details:
            trc20_balances = details["trc20"]
            # Verifica se é um dicionário e se o contrato USDT está nele
            if isinstance(trc20_balances, dict) and usdt_contract in trc20_balances:
                balance_usdt = Decimal(trc20_balances[usdt_contract]) / Decimal("1e6")
                if balance_usdt > 0:
                    required_price_ids.append(PRICE_API_CONFIG["ids_map"]["USDT"])
    
    # 2. Verificar histórico
    tx_url = f"{config['base_url']}/v1/accounts/{address}/transactions"
    tx_data = _fetch_data(tx_url, params={"limit": 1}, api_key=api_key)
    has_transactions = isinstance(tx_data, dict) and "data" in tx_data and len(tx_data["data"]) > 0

    # 3. Buscar preços e calcular valor em USD
    total_usd_balance = Decimal(0)
    prices = get_real_time_prices(required_price_ids)

    if balance_trx > 0:
        trx_id = PRICE_API_CONFIG["ids_map"]["TRX"]
        if trx_id in prices:
            total_usd_balance += balance_trx * prices[trx_id]

    if balance_usdt > 0:
        usdt_id = PRICE_API_CONFIG["ids_map"]["USDT"]
        if usdt_id in prices:
            total_usd_balance += balance_usdt * prices[usdt_id]

    return {
        "balance_crypto": balance_trx + balance_usdt,
        "balance_usd": total_usd_balance,
        "has_transactions": has_transactions,
        "explorer_link": f"{config['explorer_link_base']}{address}",
        "has_real_balance": (balance_trx > 0 or balance_usdt > 0)
    }

# --- Função Principal (sem modificações na lógica, apenas no que ela chama) ---
def get_blockchain_data(address, network, api_key=None):
    """
    Função principal para obter dados da blockchain, roteando para a função correta.
    Retorna saldo, histórico de transações e link para o explorador.
    """
    try:
        if network == "BTC":
            return get_btc_data(address, api_key)
        elif network in ["ETH", "BSC", "MATIC", "BASE", "OPTIMISM", "ARBITRUM"]:
            return get_evm_data(address, network, api_key)
        elif network == "TRX":
            return get_trx_data(address, api_key)
        else:
            return {
                "balance_crypto": Decimal(0), "balance_usd": Decimal(0),
                "has_transactions": False, "explorer_link": "#",
                "error": "Rede não suportada para consulta de dados on-chain."
            }
    except Exception as e:
        return {
            "balance_crypto": Decimal(0), "balance_usd": Decimal(0),
            "has_transactions": False, "explorer_link": "#",
            "error_fatal": f"Erro interno ao consultar dados: {str(e)}"
        }