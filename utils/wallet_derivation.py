from bip_utils import (
    Bip39MnemonicValidator, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
    Bip49, Bip49Coins,
    Bip84, Bip84Coins,
    Bip86, Bip86Coins,
    Bip32Secp256k1, Bip32PathParser,
    Bip32KeyIndex,
    WifEncoder,
    Secp256k1PrivateKey, Secp256k1PublicKey
)
from bip_utils.addr import (
    EthAddrEncoder, TrxAddrEncoder,
    P2PKHAddrEncoder, P2SHAddrEncoder, P2WPKHAddrEncoder, P2TRAddrEncoder
)

def parse_range_input(input_str):
    """Parse a range input string (e.g., '0-5' or '1,3,5') into a list of integers)."""
    if not input_str:
        return []
    
    if ',' in input_str:
        return [int(x.strip()) for x in input_str.split(',') if x.strip().isdigit()]
    
    if '-' in input_str:
        parts = input_str.split('-')
        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            return list(range(int(parts[0]), int(parts[1]) + 1))
    
    if input_str.strip().isdigit():
        return [int(input_str)]
    
    return []

def derive_custom_network(seed_bytes, account_idx, addr_idx, config, change_type):
    """Derive addresses for custom networks (BASE, OPTIMISM, ARBITRUM)."""
    try:
        if change_type != 0:
            return None

        path_template = config["path_template"]
        path = path_template.format(account=account_idx, address=addr_idx)
        
        bip32_ctx = Bip32Secp256k1.FromSeed(seed_bytes)
        bip32_ctx = bip32_ctx.DerivePath(path)
        
        private_key = bip32_ctx.PrivateKey().Raw().ToHex()
        public_key = bip32_ctx.PublicKey()
        
        secp_pub_key = Secp256k1PublicKey.FromBytes(public_key.RawCompressed().ToBytes())
        address = config["address_format"](secp_pub_key)
        
        return {
            "address": address,
            "derivation_path": path,
            "private_key": private_key
        }
    except Exception as e:
        print(f"Erro ao derivar endereço para rede personalizada: {str(e)}")
        return None

# Mapeamento de redes
NETWORK_CONFIGS = {
    "BTC": {
        "coin_type": Bip44Coins.BITCOIN,
        "derivation_paths": {
            "P2PKH": {"purpose": 44, "coin_type": Bip44Coins.BITCOIN},
            "P2SH": {"purpose": 49, "coin_type": Bip49Coins.BITCOIN},
            "BECH32": {"purpose": 84, "coin_type": Bip84Coins.BITCOIN},
            "TAPROOT": {"purpose": 86, "coin_type": Bip86Coins.BITCOIN}
        },
        "address_formats": {
            "P2PKH": lambda pub_key: P2PKHAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes(), net_ver=b"\x00"),
            "P2SH": lambda pub_key: P2SHAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes(), net_ver=b"\x05"),
            "BECH32": lambda pub_key: P2WPKHAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes(), hrp="bc"),
            "TAPROOT": lambda pub_key: P2TRAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes(), hrp="bc")
        },
        "private_key_format": "WIF"
    },
    "ETH": {
        "coin_type": Bip44Coins.ETHEREUM,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: EthAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes())
    },
    "BSC": {
        "coin_type": Bip44Coins.BINANCE_SMART_CHAIN,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: EthAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes())
    },
    "MATIC": {
        "coin_type": Bip44Coins.POLYGON,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: EthAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes())
    },
    "TRX": {
        "coin_type": Bip44Coins.TRON,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: TrxAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes())
    },
    "BASE": {
        "coin_type": Bip44Coins.ETHEREUM,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: EthAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes()),
    },
    "OPTIMISM": {
        "coin_type": Bip44Coins.ETHEREUM,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: EthAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes()),
    },
    "ARBITRUM": {
        "coin_type": Bip44Coins.ETHEREUM,
        "private_key_format": "HEX",
        "address_format": lambda pub_key: EthAddrEncoder.EncodeKey(pub_key.RawCompressed().ToBytes()),
    }
}

# INÍCIO DA ALTERAÇÃO
def derive_addresses(seed_phrase, passphrase, selected_networks,
                    account_indices_str, address_indices_str, bitcoin_address_types, change_types):
# FIM DA ALTERAÇÃO
    validator = Bip39MnemonicValidator()
    if not validator.IsValid(seed_phrase):
        words = seed_phrase.split()
        if len(words) not in [12, 15, 18, 21, 24]:
            raise ValueError("Seed phrase inválida. Deve conter 12, 15, 18, 21 ou 24 palavras.")
        raise ValueError("Seed phrase inválida. Verifique a ortografia das palavras.")

    # INÍCIO DA ALTERAÇÃO
    # Gera a semente usando a passphrase. Se a passphrase for uma string vazia, o resultado é o mesmo que sem ela.
    seed_bytes = Bip39SeedGenerator(seed_phrase).Generate(passphrase)
    # FIM DA ALTERAÇÃO
    
    all_derived_wallets = []

    account_indices = parse_range_input(account_indices_str)
    address_indices = parse_range_input(address_indices_str)

    if not account_indices:
        account_indices = [0]
    if not address_indices:
        address_indices = [0] 
    
    COIN_TYPE_MAP = {
        "BTC": 0,
        "ETH": 60,
        "BSC": 60,
        "MATIC": 60,
        "TRX": 195,
        "BASE": 60,
        "OPTIMISM": 60,
        "ARBITRUM": 60
    }

    for network in selected_networks:
        config = NETWORK_CONFIGS.get(network)
        if not config:
            print(f"Aviso: Configuração para rede {network} não encontrada. Pulando.")
            continue

        print(f"Derivando para rede: {network}")
        
        coin_type_num = COIN_TYPE_MAP.get(network, 60)

        for account_idx in account_indices:
            for change_type in change_types:
                if network == "BTC":
                    if not bitcoin_address_types:
                        print("Aviso: Nenhum tipo de endereço Bitcoin selecionado. Pulando BTC.")
                        continue

                    for btc_addr_type in bitcoin_address_types:
                        btc_der_config = config["derivation_paths"].get(btc_addr_type)
                        if not btc_der_config:
                            print(f"Aviso: Tipo de endereço BTC {btc_addr_type} não configurado. Pulando.")
                            continue

                        try:
                            
                            if btc_der_config["purpose"] == 44:
                                bip_obj = Bip44.FromSeed(seed_bytes, btc_der_config["coin_type"])
                                path_template = f"m/44'/{COIN_TYPE_MAP['BTC']}'/{account_idx}'/{change_type}/{{address}}"
                            elif btc_der_config["purpose"] == 49:
                                bip_obj = Bip49.FromSeed(seed_bytes, btc_der_config["coin_type"])
                                path_template = f"m/49'/{COIN_TYPE_MAP['BTC']}'/{account_idx}'/{change_type}/{{address}}"
                            elif btc_der_config["purpose"] == 84:
                                bip_obj = Bip84.FromSeed(seed_bytes, btc_der_config["coin_type"])
                                path_template = f"m/84'/{COIN_TYPE_MAP['BTC']}'/{account_idx}'/{change_type}/{{address}}"
                            elif btc_der_config["purpose"] == 86:
                                bip_obj = Bip86.FromSeed(seed_bytes, btc_der_config["coin_type"])
                                path_template = f"m/86'/{COIN_TYPE_MAP['BTC']}'/{account_idx}'/{change_type}/{{address}}"
                            else:
                                continue

                            account_node = bip_obj.Purpose().Coin().Account(account_idx)
                            
                            change_bip_enum = Bip44Changes.CHAIN_EXT if change_type == 0 else Bip44Changes.CHAIN_INT
                            change_node = account_node.Change(change_bip_enum)


                            for addr_idx in address_indices:
                                
                                address_node = change_node.AddressIndex(addr_idx)
                                private_key = address_node.PrivateKey().Raw().ToHex()
                                
                                if config["private_key_format"] == "WIF":
                                    priv_key_bytes = address_node.PrivateKey().Raw().ToBytes()
                                    priv_key = Secp256k1PrivateKey.FromBytes(priv_key_bytes)
                                    private_key = WifEncoder.Encode(priv_key, net_ver=b"\x80")

                                pub_key = address_node.PublicKey()
                                address = config["address_formats"][btc_addr_type](pub_key)
                                
                                derivation_path = path_template.format(address=addr_idx)

                                all_derived_wallets.append({
                                    "network": network,
                                    "address": address,
                                    "derivation_path": derivation_path,
                                    "private_key": private_key,
                                    "address_type": btc_addr_type
                                })
                            
                        except Exception as e:
                            print(f"Erro ao derivar endereço(s) para BTC {btc_addr_type} na conta {account_idx}, change {change_type}: {str(e)}")

                elif network in ["ETH", "BSC", "MATIC", "BASE", "OPTIMISM", "ARBITRUM", "TRX"]:
                    try:
                        bip_obj = Bip44.FromSeed(seed_bytes, config["coin_type"])
                        account_node = bip_obj.Purpose().Coin().Account(account_idx)
                        
                        change_bip_enum = Bip44Changes.CHAIN_EXT if change_type == 0 else Bip44Changes.CHAIN_INT
                        change_node = account_node.Change(change_bip_enum)

                        for addr_idx in address_indices:
                            
                            address_node = change_node.AddressIndex(addr_idx)
                            private_key = address_node.PrivateKey().Raw().ToHex()
                            
                            pub_key = address_node.PublicKey()
                            address = config["address_format"](pub_key)
                            
                            derivation_path = f"m/44'/{coin_type_num}'/{account_idx}'/{change_type}/{addr_idx}"

                            all_derived_wallets.append({
                                "network": network,
                                "address": address,
                                "derivation_path": derivation_path,
                                "private_key": private_key,
                                "address_type": "N/A"
                            })

                    except Exception as e:
                        print(f"Erro ao derivar conta {account_idx} ou endereço para {network} na cadeia {change_type}: {str(e)}")

    return all_derived_wallets