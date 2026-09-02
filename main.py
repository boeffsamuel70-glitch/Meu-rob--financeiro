import time
import threading
import os
from datetime import datetime
import pytz
import yfinance as ticker_data
import pandas as pd
from flask import Flask, jsonify

# --- 💱 APENAS 3 ATIVOS MAIORES ---
ATIVOS = ["EURUSD=X", "GBPUSD=X", "EURJPY=X"]
INTERVALO = "5m"
PERIODO = "2d"

app = Flask(__name__)
FUSO_SP = pytz.timezone("America/Sao_Paulo")

status_robo = {}
for ativo in ATIVOS:
    nome = ativo.replace("=X", "")
    status_robo[nome] = "Carregando mercado ao vivo..."

@app.route('/')
def home():
    linhas = ""
    for ativo, status in status_robo.items():
        linhas += "<li><b>" + ativo + ":</b> " + status + "</li>"
        
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
                        document.getElementById('aviso-status').innerText = '🟢 PREÇOS REAIS AO VIVO — Sincronizado às: ' + new Date().toLocaleTimeString('pt-BR');
                    })
                    .catch(error => console.log('Sincronizando...'));
            }
            setInterval(atualizarDados, 3000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Sinais Forex Real Time (Gráfico de 5m)</h2>
        <p id='aviso-status' style='color: #28a745; font-weight: bold;'>Buscando cotações oficiais...</p>
        <hr>
        <ul id='lista-ativos' style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            <li>Conectando ao terminal de cotações globais...</li>
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

def calcular_estrategia(df):
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)
            
        fechamentos = df['Close'].dropna().values.flatten()
        if len(fechamentos) < 10:
            return "⚪ AGUARDANDO", 0.0

        serie = pd.Series(fechamentos)
        media_curta = serie.rolling(window=3).mean()
        media_longa = serie.rolling(window=8).mean()
        
        preco_atual = float(fechamentos[-1])
        
        if (media_curta.iloc[-2] <= media_longa.iloc[-2]) and (media_curta.iloc[-1] > media_longa.iloc[-1]):
            return "🟢 COMPRA", preco_atual
        elif (media_curta.iloc[-2] >= media_longa.iloc[-2]) and (media_curta.iloc[-1] < media_longa.iloc[-1]):
            return "🔴 VENDA", preco_atual
            
        return "⚪ AGUARDANDO", preco_atual
    except Exception:
        return "⚪ AGUARDANDO", 0.0

def loop_analise_mercado():
    global status_robo

    while True:
        for ativo in ATIVOS:
            nome_limpo = ativo.replace("=X", "")
            try:
                dados_mercado = ticker_data.download(tickers=ativo, period=PERIODO, interval=INTERVALO, progress=False)
                
                if dados_mercado is None or dados_mercado.empty:
                    continue
                    
                sinal, preco = calcular_estrategia(dados_mercado)
                hora_brasilia = datetime.now(FUSO_SP).strftime('%H:%M:%S')
                
                if preco < 5:
                    formato_preco = "{:.5f}".format(preco)
                else:
                    formato_preco = "{:.2f}".format(preco)
                
                if "AGUARDANDO" in sinal:
                    status_robo[nome_limpo] = sinal + " (Preço Real: " + formato_preco + ") — às " + hora_brasilia
                else:
                    cor = "green" if "COMPRA" in sinal else "red"
                    status_robo[nome_limpo] = "<span style='color: white; background-color: " + cor + "; padding: 2px 6px; border-radius: 4px;'><b>" + sinal + " a " + formato_preco + "</b></span> — às " + hora_brasilia
                
                time.sleep(6.0)
                
            except Exception:
                pass
        
        time.sleep(15)

threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
