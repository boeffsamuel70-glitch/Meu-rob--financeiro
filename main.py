import time
import threading
import os
import requests
import random
from flask import Flask, jsonify

# --- 💱 CHAVES EXATAS ACEITAS PELA API ---
ATIVOS_MAPA = {
    "EURUSD": "EUR-USD",
    "USDJPY": "USD-JPY",
    "GBPUSD": "GBP-USD",
    "AUDUSD": "AUD-USD",
    "USDCAD": "USD-CAD",
    "USDCHF": "USD-CHF",
    "NZDUSD": "NZD-USD",
    "EURGBP": "EUR-GBP",
    "EURJPY": "EUR-JPY",
    "USDBRL": "USD-BRL"
}
ATIVOS = list(ATIVOS_MAPA.keys())

app = Flask(__name__)

# Banco de dados inicial para a tela nunca ficar vazia
status_robo = {ativo: f"⚪ AGUARDANDO (Sincronizando feed...) — às {time.strftime('%H:%M:%S')}" for ativo in ATIVOS}

@app.route('/')
def home():
    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex Real</title>
        <script>
            function atualizarDados() {
                fetch('/dados?t=' + new Date().getTime())
                    .then(response => response.json())
                    .then(data => {
                        let lista = document.getElementById('lista-actifs');
                        lista.innerHTML = '';
                        for (let ativo in data) {
                            let item = document.createElement('li');
                            item.innerHTML = `<b>${ativo}:</b> ${data[ativo]}`;
                            lista.appendChild(item);
                        }
                        document.getElementById('aviso-status').innerText = '🟢 PREÇOS REAIS DO MERCADO AO VIVO — Última checagem: ' + new Date().toLocaleTimeString();
                    })
                    .catch(error => console.log('Erro de sincronização:', error));
            }
            setInterval(atualizarDados, 3000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p id='aviso-status' style='color: #28a745; font-weight: bold;'>Buscando cotações reais...</p>
        <hr>
        <ul id='lista-actifs' style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
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
    sorteio = random.randint(1, 15)
    if sorteio == 1:
        return "🟢 COMPRA"
    elif sorteio == 2:
        return "🔴 VENDA"
    return "⚪ AGUARDANDO"

def loop_analise_mercado():
    global status_robo

    while True:
        try:
            # Chama a lista com as chaves corretas e puras da API
            url = "https://awesomeapi.com.br" + ",".join(ATIVOS_MAPA.values())
            resposta = requests.get(url, timeout=10).json()
            
            for ativo in ATIVOS:
                try:
                    # Formata o nome da chave como a API responde (ex: EURUSD)
                    chave_api = ativo + "D" if ativo == "USDBRL" else ATIVOS_MAPA[ativo].replace("-", "")
                    
                    if chave_api in resposta:
                        preco_real = float(resposta[chave_api]["bid"])
                        
                        sinal = calcular_sinal()
                        formato_preco = f"{preco_real:.5f}" if preco_real < 5 else f"{preco_real:.2f}"
                        
                        if "AGUARDANDO" in sinal:
                            status_robo[ativo] = f"{sinal} (Preço: {formato_preco}) — às {time.strftime('%H:%M:%S')}"
                        else:
                            status_robo[ativo] = f"<span style='color: white; background-color: " + ("green" if "COMPRA" in sinal else "red") + f"; padding: 2px 6px; border-radius: 4px;'><b>{sinal} a {formato_preco}</b></span> — às {time.strftime('%H:%M:%S')}"
                except Exception:
                    pass
        except Exception as e:
            print(f"Erro no loop de dados: {e}")
            
        time.sleep(5)

threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
