<img width="691" height="593" alt="image" src="https://github.com/user-attachments/assets/ef0f1135-6ae1-4eaf-a0cc-bd907b9ee491" />

# Fenix
Ferramenta gratuita desenvolvida especificamente para apoiar investigações envolvendo criptoativos. A Fenix surgiu a partir das dificuldades enfrentadas por profissionais ao se depararem com uma seed de recuperação e a necessidade de derivar endereços em profundidade suficiente para localizar saldos ocultos em carteiras de ativos virtuais.

Para uso imediato, basta executar o arquivo disponibilizado (compatível apenas com o sistema operacional Windows).

Os scripts fonte estão organizados nas demais pastas, sendo necessário possuir o Python instalado e realizar a instalação das bibliotecas listadas no arquivo requirements.txt.

É imprescindível para o bom funcionamento do sistema a inserção das chaves de API da Etherscan e da Trongrid, a fim de permitir a consulta correta dos endereços gerados. É possível realizar o upload de um arquivo .txt contendo as chaves, o qual deve seguir o formato do arquivo modelo keys.txt disponível no repositório.

# Guia de Instalação
Visão geral: A aplicação é um servidor web Flask que renderiza um front-end estático (HTML/CSS/JS) e expõe rotas para: converter códigos “1248” em seed BIP39 e derivar endereços para múltiplas redes, consultando saldos e histórico via APIs públicas (Blockstream, Etherscan v2-unified/Chainscan, TronGrid) e preços via CoinGecko.​

Requisitos: Sistema operacional: Windows, macOS ou Linux com rede e navegador atualizados.​

Python: 3.11 recomendado (3.10–3.12 também deve funcionar).​

Chaves de API:

Ethereum/EVM: uma chave compatível com API Etherscan v2 Unified, usada também em BSC/Polygon/Base/Optimism/Arbitrum via “chainid” na mesma base de endpoint.​

Tron: TRON-PRO-API-KEY para api.trongrid.io.​

Para BTC (Blockstream): não requer chave.​

Baixar o código: No GitHub, clique em Code > Download ZIP, e salve o arquivo em uma pasta local (ex.: Downloads/FenixApp).​

Extraia o ZIP. Garanta que os arquivos fiquem na mesma hierarquia indicada abaixo (não deixe uma pasta “dentro da outra” após a extração).​

Estrutura de pastas correta
Organize a estrutura exatamente assim (respeite nomes e caixa baixa/alta):​

raiz_do_projeto/

app.py

templates/

index.html

static/

style.css

script.js

utils/

wallet_derivation.py

blockchain_api.py

bip39_wordlist.py

Observações:

Instale as bibliotecas através do arquivo requirements.txt com a lista das dependências (uma por linha) utilizando o comando:
bash
pip install -r requirements.txt
Esse comando instala automaticamente todas as bibliotecas listadas no arquivo, com as versões especificadas.

O Flask usa render_template para buscar index.html em templates/.​

O front-end referencia CSS e JS servidos como estáticos; por padrão, armazene em static/.​

Os módulos utilitários são importados como utils.X no app.py; portanto, mantenha-os em utils/.​

Preparar o ambiente Python
Instale o Python 3.11 a partir do site oficial, caso não tenha instalado.​

Abra um terminal na pasta raiz_do_projeto/ (onde está app.py).​

Crie e ative um ambiente virtual:

Windows (PowerShell):

python -m venv .venv​

..venv\Scripts\Activate​

macOS/Linux (bash/zsh):

python3 -m venv .venv​

source .venv/bin/activate​

Instalar dependências: A aplicação utiliza Flask, requests, decimal (nativo), e bip_utils para derivação BIP32/BIP44/49/84/86. Instale com:​

pip install --upgrade pip​

pip install Flask requests bip-utils​

Notas:

bip-utils fornece Bip39SeedGenerator, Bip44/Bip49/Bip84/Bip86 e encoders de endereço para BTC, ETH/EVM e TRX usados em wallet_derivation.py.​

Não há dependência externa adicional para preços: usa requests direto na API CoinGecko.​

Configurar chaves de API:
Ethereum/EVM: use uma chave do provedor compatível com “api.etherscan.io/v2/api” e parâmetro chainid para outras EVM (BSC, Polygon, Base, Optimism, Arbitrum) na mesma rota unificada.​

Tron: cadastre uma TRON-PRO-API-KEY em TronGrid e forneça no campo apropriado.​

Como fornecer:

Na interface, existem campos para “Ethereum/EVM API Key” e “Tron API Key”.​

Opcionalmente, use o botão de upload para carregar um arquivo .txt com linhas no formato:

ethereum=MINHA_CHAVE_EVM

tron=MINHA_CHAVE_TRON​

BTC não requer chave; consultas usam Blockstream.info.​

Executar o servidor: Com o ambiente virtual ativo e dependências instaladas, execute:​

python app.py (Windows)​

ou python3 app.py (macOS/Linux)​

O servidor inicia em http://127.0.0.1:5000 e abre o navegador automaticamente após ~1,5s, se possível.​

Se a janela do navegador não abrir, acesse manualmente: http://127.0.0.1:5000.​

Parâmetros de execução: Host: 127.0.0.1, Porta: 5000, debug=True por padrão.​

Uso da interface: Cole uma seed BIP39 válida ou monte via painel “1248” e clique para converter; a API interna /convert_1248_to_seed valida números 0–2047 e gera a seed com base no índice direto na WORD_LIST local.​

Selecione redes: BTC, ETH, BSC, MATIC, TRX, BASE, OPTIMISM, ARBITRUM.​

Para BTC, escolha tipos de endereço (P2PKH/44, P2SH/49, Bech32/84, Taproot/86) e ranges de conta/índice e change (externa 0, interna 1).​

Informe chaves de API quando possível (melhor taxa de sucesso nas consultas) e clique “Buscar Ativos”; o front-end envia POST para /derive_and_check, depois exibe endereços com status, valor USD, caminho de derivação, chave privada e link do explorador.​

Exportar resultados: Botões para exportar CSV dos resultados visíveis e de todos os endereços derivados estão disponíveis na interface.​

CSV inclui colunas de endereço, rede, caminho, chave privada e tipo de endereço.​

Observações de rede e limites: EVM: a API unificada usa “module=account” e “action” como balance/txlist/tokenbalance com “chainid” para redes suportadas; a mesma “apikey” é usada para todas as EVM no mesmo endpoint.​

TRX: TronGrid exige TRON-PRO-API-KEY no cabeçalho; o código injeta quando fornecida.​

BTC: consultas via Blockstream.info sem chave; sem histórico ou saldo retornam indicadores apropriados.​

A consulta de preços usa CoinGecko simple/price apenas quando há saldo a precificar; sem chave e com tolerância a erros.​

Solução de problemas: ImportError em WORD_LIST: verifique se utils/bip39_wordlist.py existe; o app avisa que a função 1248 não funcionará sem esse arquivo.​

404/Template not found: confirme templates/index.html e nome do arquivo correto.​

Erros EVM “limite de taxa excedido” ou “Sem resultados”: aguarde e/ou use uma API key válida; o código já trata algumas respostas “status=0” como zero-balance para seguir fluxo.​

Tron “Erro na API Tron”: confira se a TRON-PRO-API-KEY está definida, copiando exatamente para o campo.​

BTC sem saldo em USD: preço é buscado só quando há saldo >0; caso contrário “-” em USD é esperado.​

Comandos resumidos
Windows:

python -m venv .venv​

..venv\Scripts\Activate​

pip install --upgrade pip​

pip install Flask requests bip-utils​

python app.py​

macOS/Linux:

python3 -m venv .venv​

source .venv/bin/activate​

pip install --upgrade pip​

pip install Flask requests bip-utils​

python3 app.py​

Segurança: Chaves privadas derivadas aparecem na interface e podem ser exportadas; use apenas em ambiente offline/seguro e com seeds autorizadas para análise forense ou testes.​

Chaves de API não são persistidas pelo back-end; são enviadas na requisição e usadas somente para consultas necessárias.​

<img width="1454" height="954" alt="image" src="https://github.com/user-attachments/assets/26a81b89-fe4e-4e94-869e-2449b502325e" />
<p>

<img width="1364" height="795" alt="image" src="https://github.com/user-attachments/assets/5a9e1cbd-0561-4633-bb35-c94ac3dcea01" />

<img width="1308" height="812" alt="image" src="https://github.com/user-attachments/assets/fd8bb074-b0f1-43d8-93de-16d1f49c9063" />
https://etherscan.io/apidashboard

<img width="1434" height="606" alt="image" src="https://github.com/user-attachments/assets/2bd78b63-0d7c-4ac8-82c9-c2db0cfb983f" />
https://www.trongrid.io/dashboard/keys

[Guia Fênix.pdf](https://github.com/user-attachments/files/23291499/Guia.Fenix.pdf)
