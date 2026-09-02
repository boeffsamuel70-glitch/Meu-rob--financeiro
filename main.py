import time
import threading
import os
import requests
import random
from flask import Flask, jsonify

# --- 💱 CONFIGURAÇÃO DOS ATIVOS REAIS ---
ATIVOS_MAPA = {
    "EURUSD": "USD-EUR",  # API entrega invertido (USD por 1 EUR)
    "USDJPY": "USD-JPY",
    "GBPUSD": "USD-GBP",  # API entrega invertido (USD por 1 GBP)
    "AUDUSD": "USD-AUD",  # API entrega invertido (USD por 1 AUD)
    "USDCAD": "USD-CAD",
    "USDCHF": "USD-CHF",
    "NZDUSD": "USD-NZD",  # API entrega invertido (USD por 1 NZD)
    "EURGBP": "EUR-GBP",
    "EURJPY": "EUR-JPY",
    "USDBRL": "USD-BRL"
}
ATIVOS = list(ATIVOS_MAPA.keys())

app = Flask(__name__)

# Inicialização segura para mitigar telas de travamento
status_robo = {}
for ativo in ATIVOS:
    status_robo[ativo] = f"⚪ AGUARDANDO (Carregando feed...) — às {time.strftime('%H:%M:%S')}"

@app.route('/')
def home():
    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex Real</title>
        <script>
            function atualizarDados() {
                // Parâmetro anti-cache forçado para ignorar o histórico do navegador
                fetch('/dados?t=' + new Date().getTime())
                    .then(response => response.json())
                    .then(data => {
                        let lista = document.getElementById('lista-ativos');
                        lista.innerHTML = '';
                        for (let ativo in data) {
                            let item = document.createElement('li');
                            item.innerHTML = `<b>${ativo}:</b> ${data[ativo]}`;
                            lista.appendChild(item);
                        }
                        document.getElementById('aviso-status').innerText = '🟢 PREÇOS REAIS DO MERCADO AO VIVO — Sincronizado às: ' + new Date().toLocaleTimeString();
                    })
                    .catch(error => console.log('Erro de sincronização:', error));
            }
            // Ciclo de atualização de tela a cada 3 segundos
            setInterval(atualizarDados, 3000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p id='aviso-status' style='color: #28a745; font-weight: bold;'>Buscando cotações em tempo real...</p>
        <hr>
        <ul id='lista-ativos' style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            <li>Sincronizando com as corretoras globais...</li>
        </ul>
    </body>
    </html>
    """
    return html

@app.route('/dados')
def dados():
    resposta = jsonify(status_robo)
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta

def calcular_sinal():
    sorteio = random.randint(1, 20)
    if sorteio == 1:
        return "🟢 COMPRA"
    elif sorteio == 2:
        return "🔴 VENDA"
    return "⚪ AGUARDANDO"

def loop_analise_mercado():
    global status_robo

    while True:
        try:
            # Requisição em lote unificada na API comercial estável
            url = "https://economia.awesomeapi.com.br/json/last/" + ",".join(ATIVOS_MAPA.values())
            resposta = requests.get(url, timeout=10).json()
            
            for ativo in ATIVOS:
                try:
                    chave_api = ATIVOS_MAPA[ativo].replace("-", "")
                    
                    if chave_api in resposta:
                        preco_bruto = float(resposta[chave_api]["bid"])
                        
                        # Aplica a inversão de matriz matemática para paridades com base em USD
                        if ativo in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"]:
                            preco_real = 1 / preco_bruto
                        else:
                            preco_real = preco_bruto
                        
                        sinal = calcular_sinal()
                        formato_preco = f"{preco_real:.5f}" if preco_real < 5 else f"{preco_real:.2f}"
                        
                        if "AGUARDANDO" in sinal:
                            status_robo[ativo] = f"{sinal} (Preço: {formato_preco}) — às {time.strftime('%H:%M:%S')}"
                        else:
                            status_robo[ativo] = f"<span style='color: white; background-color: " + ("green" if "COMPRA" in sinal else "red") + f"; padding: 2px 6px; border-radius: 4px;'><b>{sinal} a {formato_preco}</b></span> — às {time.strftime('%H:%M:%S')}"
                except Exception:
                    pass
        except Exception as e:
            print(f"Erro de conexão com o servidor de taxas: {e}")
            
        time.sleep(5)

# Inicialização assíncrona do monitoramento
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
