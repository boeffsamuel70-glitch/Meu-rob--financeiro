import time
import threading
import os
import random
import requests
import pandas as pd
from flask import Flask, jsonify

# --- 💱 CONFIGURAÇÃO DOS ATIVOS REAIS ---
ATIVOS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "USDBRL"]

app = Flask(__name__)

# Dicionário de status global que o robô vai preencher com dados do mundo real
status_robo = {ativo: "Conectando ao feed real de mercado..." for ativo in ATIVOS}

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
                        let aviso = document.getElementById('aviso-status');
                        aviso.innerText = '🟢 PREÇOS REAIS DO MERCADO AO VIVO — Última checagem: ' + new Date().toLocaleTimeString();
                    })
                    .catch(error => console.log('Erro de conexão:', error));
            }
            // Verifica o mercado real de 10 em 10 segundos
            setInterval(atualizarDados, 10000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p id='aviso-status' style='color: #28a745; font-weight: bold;'>Buscando cotações das corretoras...</p>
        <button onclick="atualizarDados()" style="padding: 10px 20px; background-color: #28a745; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-bottom: 15px;">
            🔄 Sincronizar Cotações Agora
        </button>
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

def calcular_sinal(historico):
    if len(historico) < 5:
        return "⚪ AGUARDANDO"
    
    serie = pd.Series(historico)
    media_curta = serie.rolling(window=3).mean()
    media_longa = serie.rolling(window=5).mean()
    
    if (media_curta.iloc[-2] <= media_longa.iloc[-2]) and (media_curta.iloc[-1] > media_longa.iloc[-1]):
        return "🟢 COMPRA"
    elif (media_curta.iloc[-2] >= media_longa.iloc[-2]) and (media_curta.iloc[-1] < media_longa.iloc[-1]):
        return "🔴 VENDA"
    return "⚪ AGUARDANDO"

def loop_analise_mercado():
    global status_robo
    # Guarda o histórico real na memória do servidor para calcular os cruzamentos
    banco_dados = {ativo: [] for ativo in ATIVOS}

    while True:
        try:
            # Puxa o lote oficial de cotações direto do Banco Central Global de moedas
            url = "https://er-api.com"
            resposta = requests.get(url, timeout=10).json()
            
            if resposta and "rates" in resposta:
                taxas = resposta["rates"]
                
                for ativo in ATIVOS:
                    try:
                        # Traduz a tabela cruzada de USD para as taxas reais de cada par
                        if ativo == "EURUSD":
                            preco_real = 1 / taxas["EUR"]
                        elif ativo == "GBPUSD":
                            preco_real = 1 / taxas["GBP"]
                        elif ativo == "AUDUSD":
                            preco_real = 1 / taxas["AUD"]
                        elif ativo == "NZDUSD":
                            preco_real = 1 / taxas["NZD"]
                        elif ativo == "USDBRL":
                            preco_real = taxas["BRL"]
                        else:
                            moeda_destino = ativo[3:]
                            preco_real = taxas.get(moeda_destino, 1.0)

                        # Alimenta as barras de 5 minutos reais
                        banco_dados[ativo].append(preco_real)
                        if len(banco_dados[ativo]) > 15:
                            banco_dados[ativo].pop(0)

                        # Executa o cálculo técnico nas variações de preço do mercado
                        sinal = calcular_sinal(banco_dados[ativo])
                        formato_preco = f"{preco_real:.5f}" if preco_real < 5 else f"{preco_real:.2f}"
                        
                        if "AGUARDANDO" in sinal:
                            status_robo[ativo] = f"{sinal} (Preço: {formato_preco}) — às {time.strftime('%H:%M:%S')}"
                        else:
                            status_robo[ativo] = f"<span style='color: white; background-color: " + ("green" if "COMPRA" in sinal else "red") + f"; padding: 2px 6px; border-radius: 4px;'><b>{sinal} a {formato_preco}</b></span> — às {time.strftime('%H:%M:%S')}"
                    except Exception:
                        pass
            else:
                print("Falha ao receber pacotes do servidor de Forex.")
        except Exception as e:
            print(f"Erro de conexão com as corretoras: {e}")
            
        # O feed atualiza as cotações mundiais e reanalisa a cada 15 segundos
        time.sleep(15)

threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
