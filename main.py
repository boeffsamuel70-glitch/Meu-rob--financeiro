import time
import threading
import os
import yfinance as ticker_data
import pandas as pd
from flask import Flask

# --- 💱 LISTA DE ATIVOS MAIS OPERADOS ---
ATIVOS = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X",
    "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "USDBRL=X"
]
INTERVALO = "5m"  # Gráfico de 5 minutos
PERIODO = "5d"    # Histórico necessário

app = Flask(__name__)
status_robo = {}

@app.route('/')
def home():
    # Renderiza a lista de moedas de forma limpa na tela do navegador
    linhas = [f"<li><b>{ativo.replace('=X', '')}:</b> {status}</li>" for ativo, status in status_robo.items()]
    html = f"""
    <html>
    <head><meta charset='utf-8'><title>IA de Sinais Forex</title></head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online</h2>
        <p><i>Análise ao vivo por cruzamento de médias móveis</i></p>
        <hr>
        <ul style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            {"".join(linhas)}
        </ul>
    </body>
    </html>
    """
    return html

def calcular_estrategia(df):
    """Calcula as Médias Móveis e gera os sinais limpando o formato dos dados."""
    try:
        # Corrige possíveis colunas duplicadas geradas pelo yfinance atualizado
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        fechamentos = df['Close'].dropna()
        
        if len(fechamentos) < 15:
            return "Aguardando histórico suficiente...", 0.0

        # Força os dados a serem tratados como uma série limpa de números decimais
        fechamentos = pd.Series(fechamentos.values.flatten(), index=fechamentos.index)

        media_curta = fechamentos.rolling(window=5).mean()
        media_longa = fechamentos.rolling(window=15).mean()
        
        preco_atual = float(fechamentos.iloc[-1])
        
        # Identifica o cruzamento das linhas nas duas últimas barras do gráfico
        if (media_curta.iloc[-2] <= media_longa.iloc[-2]) and (media_curta.iloc[-1] > media_longa.iloc[-1]):
            return f"🟢 COMPRA a {preco_atual:.5f}", preco_atual
            
        elif (media_curta.iloc[-2] >= media_longa.iloc[-2]) and (media_curta.iloc[-1] < media_longa.iloc[-1]):
            return f"🔴 VENDA a {preco_atual:.5f}", preco_atual
            
        return f"⚪ AGUARDANDO (Preço: {preco_atual:.5f})", preco_atual
    except Exception as e:
        return f"Erro no cálculo técnico: {str(e)[:30]}", 0.0

def loop_analise_mercado():
    global status_robo
    ultimos_sinais = {ativo: None for ativo in ATIVOS}
    
    # Define o status inicial visível
    for ativo in ATIVOS:
        status_robo[ativo] = "Carregando dados..."

    while True:
        for ativo in ATIVOS:
            try:
                # Baixa os dados online forçando o formato correto sem travar
                dados = ticker_data.download(tickers=ativo, period=PERIODO, interval=INTERVALO, progress=False, group_by='ticker')
                
                if dados is None or dados.empty:
                    status_robo[ativo] = "Sem resposta do mercado..."
                    continue
                    
                sinal, preco = calcular_estrategia(dados)
                status_robo[ativo] = f"{sinal} — às {time.strftime('%H:%M:%S')}"
                
                if sinal != ultimos_sinais[ativo] and "AGUARDANDO" not in sinal and "Erro" not in sinal:
                    print(f"⚠️ [SINAL] {ativo.replace('=X', '')}: {sinal}")
                    ultimos_sinais[ativo] = sinal
                
                # Pausa de 3 segundos entre moedas para evitar bloqueio por velocidade
                time.sleep(3.0)
                
            except Exception as e:
                status_robo[ativo] = f"Erro ao atualizar: {str(e)[:30]}"
        
        # Aguarda 1 minuto antes de checar toda a lista de ativos novamente
        time.sleep(60)

# Inicializa o monitoramento em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    # Garante o funcionamento correto na porta do Render
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
