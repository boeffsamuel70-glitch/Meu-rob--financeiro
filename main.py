import time
import threading
import yfinance as ticker_data
import pandas as pd
from flask import Flask

# --- CONFIGURAÇÕES DO ROBÔ ---
ATIVO = "PETR4.SA"  # Ativo que será analisado
INTERVALO = "1m"    # Tempo gráfico
PERIODO = "1d"      # Dados do dia atual

# Servidor Web simples para manter o site gratuito ativo
app = Flask(__name__)
status_robo = "Iniciando..."

@app.route('/')
def home():
    return f"🤖 IA de Sinais Online! Status atual: {status_robo}"

def calcular_estrategia(df):
    """Calcula as Médias Móveis e gera os sinais."""
    df['Media_Curta'] = df['Close'].rolling(window=5).mean()
    df['Media_Longa'] = df['Close'].rolling(window=15).mean()
    
    ultima_linha = df.iloc[-1]
    linha_anterior = df.iloc[-2]
    preco_atual = float(ultima_linha['Close'])
    
    if (linha_anterior['Media_Curta'] <= linha_anterior['Media_Longa']) and \
       (ultima_linha['Media_Curta'] > ultima_linha['Media_Longa']):
        return f"🟢 COMPRA a R$ {preco_atual:.2f}", preco_atual
        
    elif (linha_anterior['Media_Curta'] >= linha_anterior['Media_Longa']) and \
         (ultima_linha['Media_Curta'] < ultima_linha['Media_Longa']):
        return f"🔴 VENDA a R$ {preco_atual:.2f}", preco_atual
        
    return f"⚪ AGUARDANDO (Preço: R$ {preco_atual:.2f})", preco_atual

def loop_analise_mercado():
    global status_robo
    ultimo_sinal = None
    
    while True:
        try:
            dados = ticker_data.download(tickers=ATIVO, period=PERIODO, interval=INTERVALO, progress=False)
            
            if len(dados) < 15:
                status_robo = "Aguardando mais dados históricos do mercado..."
                time.sleep(10)
                continue
                
            sinal, preco = calcular_estrategia(dados)
            status_robo = f"Última análise: {sinal} às {time.strftime('%H:%M:%S')}"
            
            if sinal != ultimo_sinal and "AGUARDANDO" not in sinal:
                print(f"[{time.strftime('%H:%M:%S')}] {sinal}")
                ultimo_sinal = sinal
            
            time.sleep(30) # Analisa a cada 30 segundos
            
        except Exception as e:
            status_robo = f"Erro na leitura dos dados: {e}"
            time.sleep(10)

# Inicia o robô em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    # Roda o servidor web na porta exigida pela nuvem
    app.run(host="0.0.0.0", port=8080)
