import time
import threading
import os
import yfinance as ticker_data
import pandas as pd
from flask import Flask

# --- 💱 LISTA EXPANDIDA COM OS PARES MAIS OPERADOS DO MUNDO ---
ATIVOS = [
    "EURUSD=X",  # 1. Euro / Dólar (O mais operado do mundo)
    "USDJPY=X",  # 2. Dólar / Iene Japonês
    "GBPUSD=X",  # 3. Libra / Dólar (famoso 'Cable')
    "AUDUSD=X",  # 4. Dólar Australiano / Dólar
    "USDCAD=X",  # 5. Dólar / Dólar Canadense
    "USDCHF=X",  # 6. Dólar / Franco Suíço
    "NZDUSD=X",  # 7. Dólar da Nova Zelândia / Dólar
    "EURGBP=X",  # 8. Euro / Libra
    "EURJPY=X",  # 9. Euro / Iene Japonês
    "USDBRL=X"   # 10. Dólar / Real Brasileiro (Para acompanhar a moeda local)
]

INTERVALO = "5m"    # Tempo gráfico de 5 minutos
PERIODO = "5d"      # Histórico necessário para calcular as médias

app = Flask(__name__)
status_robo = {}

@app.route('/')
def home():
    # Exibe a lista de monitoramento organizada em HTML
    linhas = [f"<li><b>{ativo.replace('=X', '')}:</b> {status}</li>" for ativo, status in status_robo.items()]
    html = f"""
    <html>
    <head><meta charset='utf-8'><title>IA de Sinais Forex</title></head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online</h2>
        <p><i>Análise baseada em cruzamento de médias móveis (5m)</i></p>
        <hr>
        <ul style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            {"".join(linhas)}
        </ul>
    </body>
    </html>
    """
    return html

def calcular_estrategia(df):
    """Calcula as Médias Móveis e gera os sinais."""
    df['Media_Curta'] = df['Close'].rolling(window=5).mean()
    df['Media_Longa'] = df['Close'].rolling(window=15).mean()
    
    ultima_linha = df.iloc[-1]
    linha_anterior = df.iloc[-2]
    preco_atual = float(ultima_linha['Close'])
    
    # Lógica de cruzamento de médias
    if (linha_anterior['Media_Curta'] <= linha_anterior['Media_Longa']) and \
       (ultima_linha['Media_Curta'] > ultima_linha['Media_Longa']):
        return f"🟢 COMPRA a {preco_atual:.5f}", preco_atual
        
    elif (linha_anterior['Media_Curta'] >= linha_anterior['Media_Longa']) and \
         (ultima_linha['Media_Curta'] < ultima_linha['Media_Longa']):
        return f"🔴 VENDA a {preco_atual:.5f}", preco_atual
        
    return f"⚪ AGUARDANDO (Preço: {preco_atual:.5f})", preco_atual

def loop_analise_mercado():
    global status_robo
    ultimos_sinais = {ativo: None for ativo in ATIVOS}
    
    for ativo in ATIVOS:
        status_robo[ativo] = "Iniciando análise técnica..."

    while True:
        for ativo in ATIVOS:
            try:
                dados = ticker_data.download(tickers=ativo, period=PERIODO, interval=INTERVALO, progress=False)
                
                if len(dados) < 15:
                    status_robo[ativo] = "Aguardando histórico de mercado..."
                    continue
                    
                sinal, preco = calcular_estrategia(dados)
                status_robo[ativo] = f"{sinal} — às {time.strftime('%H:%M:%S')}"
                
                # Exibe um alerta chamativo no painel de Logs se houver uma nova oportunidade
                if sinal != ultimos_sinais[ativo] and "AGUARDANDO" not in sinal:
                    print(f"⚠️ [SINAL] {ativo.replace('=X', '')}: {sinal}")
                    ultimos_sinais[ativo] = sinal
                
                # Pausa rápida para não enviar requisições coladas no Yahoo Finance
                time.sleep(1.5)
                
            except Exception as e:
                status_robo[ativo] = f"Erro ao atualizar: {e}"
        
        # Aguarda 1 minuto para refazer a varredura completa da lista
        time.sleep(60)

# Inicializa o monitoramento em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
