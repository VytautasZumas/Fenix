import sys
import os
import webbrowser
import threading
import time
import traceback
from flask import Flask, render_template, request, jsonify

# Importar módulos utilitários
from utils.wallet_derivation import derive_addresses
from utils.blockchain_api import get_blockchain_data

# Carrega a lista de palavras DIRETAMENTE do arquivo local.
try:
    from utils.bip39_wordlist import WORD_LIST
    print("OK: Lista de palavras BIP39 carregada com sucesso do arquivo local 'utils/bip39_wordlist.py'.")
except ImportError:
    print("ERRO FATAL: Arquivo 'utils/bip39_wordlist.py' não encontrado. A função 1248 não irá funcionar.")
    WORD_LIST = []

# --- Configurações da Aplicação ---
DEBUG_MODE = True
FLASK_PORT = 5000
FLASK_HOST = '127.0.0.1'

# --- Inicialização do Flask ---
app = Flask(__name__)

# --- Rotas da Aplicação ---
@app.route('/')
def index():
    """ Rota principal que renderiza a interface HTML. """
    return render_template('index.html')


@app.route('/convert_1248_to_seed', methods=['POST'])
def convert_1248_to_seed():
    """ Converte os números do painel 1248 para uma seed phrase. """
    try:
        if not WORD_LIST:
             return jsonify({"error": "A lista de palavras BIP39 não está disponível no servidor."}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "Requisição JSON inválida."}), 400

        word_data = data.get('word_data')
        if not isinstance(word_data, list) or len(word_data) not in [12, 24]:
            return jsonify({"error": f"Número inválido de palavras ({len(word_data)}). São necessárias 12 ou 24."}), 400
        
        seed_words = []
        for i, word_digits in enumerate(word_data):
            if not (isinstance(word_digits, list) and len(word_digits) == 4):
                 return jsonify({"error": f"Formato inválido para os dados da palavra #{i+1}."}), 400
            number_as_string = "".join(map(str, word_digits))
            try:
                word_number = int(number_as_string)
            except (ValueError, TypeError):
                 return jsonify({"error": f"Valor numérico inválido '{number_as_string}' para a palavra #{i+1}."}), 400

            # --- INÍCIO DA ALTERAÇÃO ---
            # 1. Validação do número agora é de 0 a 2047.
            if not (0 <= word_number <= 2047):
                return jsonify({"error": f"Número da palavra ({word_number}) fora do intervalo (0-2047) para a palavra #{i+1}."}), 400

            # 2. O índice da palavra é agora EXATAMENTE o número inserido.
            word_index = word_number
            # --- FIM DA ALTERAÇÃO ---
            
            seed_words.append(WORD_LIST[word_index])
        
        final_seed_phrase = " ".join(seed_words)
        return jsonify({"success": True, "seed_phrase": final_seed_phrase})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Ocorreu um erro interno no servidor durante a conversão."}), 500


@app.route('/derive_and_check', methods=['POST'])
def derive_and_check():
    """ Rota para receber os dados da seed, derivar endereços e consultar APIs. """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Requisição JSON inválida."}), 400

        seed_phrase = data.get('seed_phrase')
        passphrase = data.get('passphrase', '')
        selected_networks = data.get('selected_networks', [])
        account_indices_str = data.get('account_indices', '0')
        address_indices_str = data.get('address_indices', '0-10')
        bitcoin_address_types = data.get('bitcoin_address_types', [])
        api_keys = data.get('api_keys', {}) 
        change_types = data.get('change_types', [0])

        if not seed_phrase:
            return jsonify({"error": "Seed phrase é obrigatória."}), 400

        derived_wallets_full_list = derive_addresses(
            seed_phrase, passphrase, selected_networks,
            account_indices_str, address_indices_str,
            bitcoin_address_types, change_types
        )
        
        results_filtered = []
        for wallet_info in derived_wallets_full_list:
            address = wallet_info['address']
            network = wallet_info['network']
            print(f"Consultando: {address} ({network})")
            api_key_for_network = api_keys.get('tron') if network == "TRX" else api_keys.get('ethereum')
            blockchain_data = get_blockchain_data(address, network, api_key_for_network)

            if blockchain_data and not blockchain_data.get("error_fatal"):
                if blockchain_data.get('has_real_balance', False) or blockchain_data.get('has_transactions', False):
                    result_item = {**wallet_info, **blockchain_data}
                    result_item["balance_crypto"] = str(result_item.get('balance_crypto', '0'))
                    result_item["balance_usd"] = str(result_item.get('balance_usd', '0'))
                    if network == "BTC":
                        result_item["balance_satoshi"] = str(result_item.get('balance_satoshi', '0'))
                    results_filtered.append(result_item)
            elif blockchain_data and blockchain_data.get("error_fatal"):
                print(f"AVISO: Erro na API para {address} ({network}): {blockchain_data['error_fatal']}")
            time.sleep(0.2)
            
        return jsonify({
            "success": True, 
            "results": results_filtered, 
            "all_derived_wallets": derived_wallets_full_list
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500

# --- Ponto de Entrada Principal ---
if __name__ == '__main__':
    url = f"http://{FLASK_HOST}:{FLASK_PORT}"
    print(f"Servidor Fênix iniciando em {url}")
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, lambda: webbrowser.open_new(url)).start()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG_MODE)