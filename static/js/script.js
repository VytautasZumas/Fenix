// Variável global para armazenar todos os endereços derivados
let allDerivedWalletsData = [];

// Função para exibir erros de forma centralizada
function showError(message, isSuccess = false) {
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    if (isSuccess) {
        errorElement.style.backgroundColor = 'rgba(0, 184, 148, 0.1)';
        errorElement.style.color = 'var(--success-color)';
        errorElement.style.borderColor = 'var(--success-color)';
    } else {
        errorElement.style.backgroundColor = 'rgba(255, 118, 117, 0.1)';
        errorElement.style.color = 'var(--error-color)';
        errorElement.style.borderColor = 'var(--error-color)';
    }

    const resultsArea = document.querySelector('.results-area');
    if(resultsArea) resultsArea.style.display = 'block';
    
    setTimeout(() => {
        errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

// --- LÓGICA PRINCIPAL DE BUSCA ---
async function searchAddresses() {
    const seedPhrase = document.getElementById('seedPhrase').value.trim();
    if (!seedPhrase) {
        showError('Por favor, insira a seed mnemônica ou use o decodificador de placa.');
        return;
    }

    const selectedNetworks = Array.from(document.querySelectorAll('input[name="network"]:checked'))
                               .map(checkbox => checkbox.value);
    
    if (selectedNetworks.length === 0) {
        showError('Por favor, selecione pelo menos uma rede/blockchain para análise.');
        return;
    }

    let btcAddressTypes = [];
    if (document.getElementById('btcCheckbox').checked) {
        btcAddressTypes = Array.from(document.querySelectorAll('input[name="btcAddressType"]:checked'))
                               .map(checkbox => checkbox.value);
        if (btcAddressTypes.length === 0) {
            showError('Você selecionou Bitcoin. Por favor, selecione pelo menos um tipo de endereço Bitcoin.');
            return;
        }
    }

    const accountRange = document.getElementById('accountRange').value;
    const indexRange = document.getElementById('indexRange').value;
    const changeTypes = Array.from(document.querySelectorAll('input[name="changeType"]:checked')).map(cb => parseInt(cb.value));
    if (changeTypes.length === 0) {
        showError('Por favor, selecione pelo menos um tipo de cadeia de endereços (Externa/Interna).');
        return;
    }
    
    const usePassphrase = document.getElementById('usePassphrase').checked;
    const passphrase = usePassphrase ? document.getElementById('passphrase').value : '';
    
    const apiKeys = {
        ethereum: document.getElementById('apiKeyEthereum')?.value.trim() ?? '',
        tron: document.getElementById('apiKeyTron')?.value.trim() ?? ''
    };

    document.getElementById('loadingSpinner').style.display = 'inline-block';
    document.querySelector('.results-area').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    
    const resultsTableBody = document.getElementById('resultsTable').querySelector('tbody');
    resultsTableBody.innerHTML = '';
    document.getElementById('totalUsdValue').textContent = '$0.00'; 
    document.getElementById('foundCount').textContent = '0';
    allDerivedWalletsData = [];

    const searchButton = document.getElementById('searchButton');
    searchButton.disabled = true;
    searchButton.innerHTML = '<span class="spinner"></span> Buscando...';

    try {
        const response = await fetch('/derive_and_check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                seed_phrase: seedPhrase, passphrase, selected_networks: selectedNetworks,
                account_indices: accountRange, address_indices: indexRange,
                bitcoin_address_types: btcAddressTypes, api_keys: apiKeys, 
                change_types: changeTypes
            })
        });
        const result = await response.json();
        if (response.ok) {
            displayResults(result.results);
            allDerivedWalletsData = result.all_derived_wallets || []; 
        } else {
            throw new Error(result.error || 'Ocorreu um erro desconhecido.');
        }
    } catch (error) {
        console.error('Erro na requisição:', error);
        showError(`Erro: ${error.message}`);
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
        searchButton.disabled = false;
        searchButton.innerHTML = '<span class="btn-icon">🔍</span> Buscar Ativos';
    }
}

function displayResults(results) {
    const tbody = document.getElementById('resultsTable').querySelector('tbody');
    tbody.innerHTML = '';
    document.getElementById('foundCount').textContent = results.length;
    let totalUsdSum = 0;

    if (results.length === 0) {
        const row = tbody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 7;
        cell.textContent = 'Nenhum endereço com saldo ou histórico encontrado para os parâmetros informados.';
        cell.style.textAlign = 'center';
    } else {
        results.forEach(item => {
            const row = tbody.insertRow();
            
            row.insertCell(0).textContent = item.address;
            row.insertCell(1).textContent = item.network;

            const balanceCryptoNum = parseFloat(item.balance_crypto);
            const balanceUsdNum = parseFloat(item.balance_usd);
            let balanceDisplay = '', statusClass = '';

            if (item.has_real_balance) {
                balanceDisplay = (item.network === 'BTC' && item.balance_satoshi)
                    ? `${item.balance_satoshi} Satoshis`
                    : `${Number(balanceCryptoNum).toFixed(8)} ${item.network || ''}`;
                statusClass = 'indicator-saldo';
            } else if (item.has_transactions) {
                balanceDisplay = `Com Histórico`;
                statusClass = 'indicator-historico';
            } else {
                balanceDisplay = 'Vazio';
                statusClass = 'indicator-vazio';
            }
            
            const balanceCell = row.insertCell(2);
            balanceCell.textContent = balanceDisplay;
            balanceCell.className = `status-col ${statusClass}`;

            const usdCell = row.insertCell(3);
            usdCell.textContent = !isNaN(balanceUsdNum) && balanceUsdNum > 0 ? `$${balanceUsdNum.toFixed(2)}` : '-';
            if (!isNaN(balanceUsdNum)) totalUsdSum += balanceUsdNum;
            
            row.insertCell(4).textContent = item.derivation_path;
            
            const pkCell = row.insertCell(5);
            pkCell.className = 'private-key-cell';
            const pkTextSpan = document.createElement('span');
            pkTextSpan.textContent = item.private_key;
            const copyButton = document.createElement('button');
            copyButton.innerHTML = '📋';
            copyButton.title = 'Copiar chave privada';
            copyButton.className = 'copy-btn';
            copyButton.onclick = () => copyToClipboard(item.private_key, copyButton);
            pkCell.append(pkTextSpan, copyButton);

            const explorerCell = row.insertCell(6);
            const explorerLink = document.createElement('a');
            explorerLink.href = item.explorer_link;
            explorerLink.target = '_blank';
            explorerLink.innerHTML = '🔗';
            explorerLink.title = 'Ver no explorador';
            explorerCell.appendChild(explorerLink);
        });
    }
    document.getElementById('totalUsdValue').textContent = `$${totalUsdSum.toFixed(2)}`;
}

// --- FUNÇÕES DE UTILIDADE ---
async function copyToClipboard(text, buttonElement) {
    try {
        await navigator.clipboard.writeText(text);
        buttonElement.textContent = '✅';
        setTimeout(() => { buttonElement.innerHTML = '📋'; }, 2000);
    } catch (err) {
        console.error('Falha ao copiar:', err);
        showError('Erro ao copiar a chave privada.');
    }
}

function exportResults(format) {
    if (format !== 'csv') return showError(`Formato ${format.toUpperCase()} não suportado.`);
    const headers = Array.from(document.querySelectorAll('#resultsTable thead th')).map(th => `"${th.textContent.trim()}"`);
    const rows = Array.from(document.querySelectorAll('#resultsTable tbody tr'));
    
    if (rows.length === 0 || (rows.length === 1 && rows[0].cells.length < headers.length)) {
        return showError("Não há resultados visíveis para exportar.");
    }
    let csvContent = "\ufeff" + headers.join(',') + '\n';
    rows.forEach(row => {
        const rowData = Array.from(row.querySelectorAll('td')).map((cell, index) => {
            let text = '';
            if (cell.classList.contains('private-key-cell')) {
                text = cell.querySelector('span')?.textContent ?? '';
            } else if (index === 6) { 
                text = cell.querySelector('a')?.href ?? '';
            } else {
                text = cell.textContent;
            }
            return `"${text.replace(/"/g, '""')}"`;
        });
        csvContent += rowData.join(',') + '\n';
    });
    downloadCsv(csvContent, 'fenix_resultados_visiveis.csv');
}

function exportAllResultsToCsv() {
    if (allDerivedWalletsData.length === 0) {
        return showError('Não há endereços derivados para exportar. Execute uma busca primeiro.');
    }
    const headers = ["Endereço", "Rede", "Caminho Derivação", "Chave Privada", "Tipo de Endereço"];
    let csvContent = "\ufeff" + headers.map(h => `"${h}"`).join(',') + '\n';
    allDerivedWalletsData.forEach(item => {
        const rowData = [
            item.address, item.network, item.derivation_path,
            item.private_key, item.address_type || 'N/A'
        ].map(data => `"${String(data).replace(/"/g, '""')}"`);
        csvContent += rowData.join(',') + '\n';
    });
    downloadCsv(csvContent, 'fenix_todos_enderecos.csv');
}

function downloadCsv(content, fileName) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function uploadApiKeys(file) {
    if (!file) {
        document.getElementById('fileName').textContent = 'Nenhum arquivo selecionado.';
        return;
    }
    document.getElementById('fileName').textContent = file.name;

    const reader = new FileReader();
    reader.onload = (e) => {
        const lines = e.target.result.split('\n');
        let keysLoadedCount = 0;
        lines.forEach(line => {
            const [keyName, keyValue] = line.split('=').map(s => s.trim());
            if (keyName && keyValue) {
                let targetInputId = '';
                const lowerKeyName = keyName.toLowerCase();
                if (lowerKeyName === 'ethereum' || lowerKeyName === 'evm' || lowerKeyName === 'etherscan') {
                    targetInputId = 'apiKeyEthereum';
                } else if (lowerKeyName === 'tron' || lowerKeyName === 'trongrid') {
                    targetInputId = 'apiKeyTron';
                }
                
                const targetElement = document.getElementById(targetInputId);
                if (targetElement) {
                    targetElement.value = keyValue;
                    keysLoadedCount++;
                }
            }
        });
        showError(`${keysLoadedCount} chave(s) de API preenchida(s) do arquivo.`, true);
    };
    reader.readAsText(file);
}

// --- FUNÇÕES PARA O PAINEL 1248 ---
function createSeed1248InputPanel(start, end, containerElement) {
    if (!containerElement) return;
    const panel = document.createElement('div');
    panel.className = 'word-panel';
    panel.innerHTML = `<h4>Palavras ${start} - ${end}</h4>`;
    const grid = document.createElement('div');
    grid.className = 'word-input-grid';
    for (let i = start; i <= end; i++) {
        const block = document.createElement('div');
        block.className = 'word-input-block';
        block.innerHTML = `<span class="word-label">#${String(i).padStart(2, '0')}</span>`;
        const digitsContainer = document.createElement('div');
        digitsContainer.className = 'digit-groups-container';
        for (let j = 0; j < 4; j++) {
            const digitGroup = document.createElement('div');
            digitGroup.className = 'digit-group';
            digitGroup.dataset.wordIndex = i;
            digitGroup.dataset.digitIndex = j;
            ['1', '2', '4', '8'].forEach(val => {
                const checkboxId = `cb-w${i}-d${j}-v${val}`;
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = checkboxId;
                checkbox.value = val;
                const label = document.createElement('label');
                label.htmlFor = checkboxId;
                label.textContent = val;
                digitGroup.append(checkbox, label);
            });
            digitsContainer.appendChild(digitGroup);
        }
        block.appendChild(digitsContainer);
        grid.appendChild(block);
    }
    panel.appendChild(grid);
    containerElement.appendChild(panel);
}

function resetSeed1248Panel() {
    const checkboxes = document.querySelectorAll('#seed1248-panel input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
}

// --- INÍCIO DA CORREÇÃO ---
async function convertAndUseSeed1248() {
    // A nova lógica coleta os dados de todas as 24 posições primeiro.
    const allWordsData = [];
    for (let i = 1; i <= 24; i++) {
        const wordDigits = [];
        for (let j = 0; j < 4; j++) {
            const digitGroup = document.querySelector(`.digit-group[data-word-index='${i}'][data-digit-index='${j}']`);
            if (!digitGroup) continue;
            
            const checkedBoxes = digitGroup.querySelectorAll('input:checked');
            let digitSum = 0;
            checkedBoxes.forEach(cb => { digitSum += parseInt(cb.value, 10); });
            wordDigits.push(digitSum);
        }
        allWordsData.push(wordDigits);
    }

    // Filtra apenas as palavras que foram de fato preenchidas (pelo menos um dígito não é zero)
    const filledWordData = allWordsData.filter(digits => digits.some(d => d > 0));

    // Valida o número de palavras preenchidas
    if (filledWordData.length !== 12 && filledWordData.length !== 24) {
        if (filledWordData.length === 0) return showError('Nenhum número foi marcado no painel.');
        return showError(`Foram preenchidas ${filledWordData.length} palavras. Por favor, preencha exatamente 12 ou 24 palavras.`);
    }

    try {
        const response = await fetch('/convert_1248_to_seed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Envia apenas os dados das palavras preenchidas
            body: JSON.stringify({ word_data: filledWordData })
        });
        const result = await response.json();
        if (response.ok && result.success) {
            document.getElementById('seedPhrase').value = result.seed_phrase;
            document.getElementById('seed1248-panel-overlay').style.display = 'none';
            document.getElementById('useSeed1248').checked = false;
            showError('Seed preenchida com sucesso a partir do decodificador!', true);
        } else {
            throw new Error(result.error || 'Falha ao converter a seed.');
        }
    } catch (error) {
        showError(`Erro na conversão: ${error.message}`);
    }
}
// --- FIM DA CORREÇÃO ---

// --- EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    const btcCheckbox = document.getElementById('btcCheckbox');
    const btcAddressTypesDiv = document.querySelector('.btc-address-types');
    btcCheckbox.addEventListener('change', () => {
        btcAddressTypesDiv.style.display = btcCheckbox.checked ? 'block' : 'none';
    });
    if(btcCheckbox.checked) btcAddressTypesDiv.style.display = 'block';

    const usePassphraseCheckbox = document.getElementById('usePassphrase');
    const passphraseGroup = document.getElementById('passphraseGroup');
    usePassphraseCheckbox.addEventListener('change', () => {
        passphraseGroup.style.display = usePassphraseCheckbox.checked ? 'block' : 'none';
        if (!usePassphraseCheckbox.checked) document.getElementById('passphrase').value = '';
    });
    
    document.getElementById('searchButton').addEventListener('click', searchAddresses);

    const apiKeyUploadInput = document.getElementById('apiKeyUpload');
    apiKeyUploadInput.addEventListener('change', () => {
        uploadApiKeys(apiKeyUploadInput.files[0]);
    });

    // Listeners para o painel 1248
    const useSeed1248Checkbox = document.getElementById('useSeed1248');
    const panelOverlay = document.getElementById('seed1248-panel-overlay');
    const closePanelBtn = document.getElementById('close-panel-btn');

    useSeed1248Checkbox.addEventListener('change', () => {
        panelOverlay.style.display = useSeed1248Checkbox.checked ? 'flex' : 'none';
    });
    closePanelBtn.addEventListener('click', () => {
        panelOverlay.style.display = 'none';
        useSeed1248Checkbox.checked = false;
    });
    panelOverlay.addEventListener('click', (e) => {
        if (e.target === panelOverlay) closePanelBtn.click();
    });

    // Gera o conteúdo do painel dinamicamente
    const panelsContainer = document.querySelector('#seed1248-panel .panels-container');
    if(panelsContainer) {
        panelsContainer.innerHTML = '';
        const panelWrapper1 = document.createElement('div');
        const panelWrapper2 = document.createElement('div');
        panelsContainer.append(panelWrapper1, panelWrapper2);
        createSeed1248InputPanel(1, 12, panelWrapper1);
        createSeed1248InputPanel(13, 24, panelWrapper2);
    }
});
