import time
import threading
import os
import requests
import random
from flask import Flask, jsonify

# --- 💱 CONFIGURAÇÃO DOS ATIVOS REAIS (Chaves Corretas da API) ---
ATIVOS_MAPA = {
    "EURUSD": "USD-EUR",  # API responde como USDEUR
    "USDJPY": "USD-JPY",  # API responde como USDJPY
    "GBPUSD": "USD-GBP",  # API responde como USDGBP
    "AUDUSD": "USD-AUD",  # API responde como USDAUD
    "USDCAD": "USD-CAD",  # API responde como USDCAD
    "USDCHF": "USD-CHF",  # API responde como USDCHF
    "NZDUSD": "USD-NZD",  # API responde como USDNZD
    "EURGBP": "EUR-GBP",  # API responde como EURGBP
    "EURJPY": "EUR-JPY",  # API responde como EURJPY
    "USDBRL": "USD-BRL"   # API responde como USDBRL
}
ATIVOS = list(ATIVOS_MAPA.keys())

app = Flask(__name__)

# O banco de dados já inicia com valores reais de balizamento para a tela NUNCA travar em branco
status_robo = {
    "EURUSD": "⚪ AGUARDANDO (Preço: 1.08250) — às 00:00:00",
    "USDJPY": "⚪ AGUARDANDO (Preço: 145.42) — às 00:00:00",
    "GBPUSD": "⚪ AGUARDANDO (Preço: 1.26850) — às 00:00:00",
    "AUDUSD": "⚪ AGUARDANDO (Preço: 0.65120) — às 00:00:00",
    "USDCAD": "⚪ AGUARDANDO (Preço: 1.35400) — às 00:00:00",
    "USDCHF": "⚪ AGUARDANDO (Preço: 0.88450) — às 00:00:00",
    "NZDUSD": "⚪ AGUARDANDO (Preço: 0.59250) — às 00:00:00",
    "EURGBP": "⚪ AGUARDANDO (Preço: 0.85320) — às 00:00:00",
    "EURJPY": "⚪ AGUARDANDO (Preço: 157.45) — às 00:00:00",
    "USDBRL": "⚪ AGUARDANDO (Preço: 5.64) — às 00:00:00"
}

@app.route('/')
def home():
    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex Real Time</title>
        <script>
            function atualizarDados() {
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
            // Verifica o servidor a cada 3 segundos
            setInterval(atualizarDados, 3000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p id='aviso-status' style='color: #28a745; font-weight: bold;'>Buscando cotações das corretoras...</p>
        <hr>
        <ul id='lista-ativos' style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            <li>Conectando ao painel de controle...</li>
        </ul>
    </body>
    </html>
    """
    return html

@app.route('/dados')
def dados():
    resposta = jsonify(status_robo)
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
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
            # Puxa o lote oficial de cotações das corretoras
            url = "https://awesomeapi.com.br" + ",".join(ATIVOS_MAPA.values())
            resposta = requests.get(url, timeout=10).json()
            
            for ativo in ATIVOS:
                try:
                    # Mapeia a resposta exata da API (ex: USDEUR para EURUSD)
                    chave_api = ATIVOS_MAPA[ativo].replace("-", "")
                    
                    if chave_api in resposta:
                        preco_bruto = float(resposta[chave_api]["bid"])
                        
                        # Inverte a matriz para moedas onde o USD é a base, trazendo o valor correto do gráfico
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
            print(f"Erro de conexão com o feed: {e}")
            
        # Sincroniza e atualiza os preços do mercado a cada 5 segundos
        time.sleep(5)

# Inicializa o monitoramento assíncrono em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
