import time
import threading
import os
import yfinance as ticker_data
import pandas as pd
from flask import Flask

# --- 💱 CONFIGURAÇÃO EM 5 MINUTOS ---
ATIVOS = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X",
    "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "USDBRL=X"
]
INTERVALO = "5m"  # Configurado para 5 minutos conforme solicitado!
PERIODO = "5d"    # Puxa histórico dos últimos 5 dias para o cálculo

app = Flask(__name__)
status_robo = {}

@app.route('/')
def home():
    linhas = [f"<li><b>{ativo.replace('=X', '')}:</b> {status}</li>" for ativo, status in status_robo.items()]
    html = f"""
    <html>
    <head><meta charset='utf-8'><title>IA de Sinais Forex 5M</title></head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
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
    """Calcula as Médias Móveis isolando corretamente os preços de fechamento."""
    try:
        # Resolve bugs de formatação de tabelas do yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)
            
        fechamentos = df['Close'].dropna()
        
        # Converte em matriz unidimensional limpa de números decimais
        valores_limpos = fechamentos.values.flatten()
        
        if len(valores_limpos) < 15:
            return "Aguardando histórico suficiente...", 0.0

        # Cria uma série temporal pura para aplicar os cálculos matemáticos
        serie_precos = pd.Series(valores_limpos)

        media_curta = serie_precos.rolling(window=5).mean()
        media_longa = serie_precos.rolling(window=15).mean()
        
        preco_atual = float(valores_limpos[-1])
        
        # Lógica de cruzamento com checagem de segurança de índice
        if (media_curta.iloc[-2] <= media_longa.iloc[-2]) and (media_curta.iloc[-1] > media_longa.iloc[-1]):
            return f"🟢 COMPRA a {preco_atual:.5f}", preco_atual
            
        elif (media_curta.iloc[-2] >= media_longa.iloc[-2]) and (media_curta.iloc[-1] < media_longa.iloc[-1]):
            return f"🔴 VENDA a {preco_atual:.5f}", preco_atual
            
        return f"⚪ AGUARDANDO (Preço: {preco_atual:.5f})", preco_atual
    except Exception as e:
        return f"Processando dados técnicos...", 0.0

def loop_analise_mercado():
    global status_robo
    ultimos_sinais = {ativo: None for ativo in ATIVOS}
    
    for ativo in ATIVOS:
        status_robo[ativo] = "Carregando dados..."

    while True:
        for ativo in ATIVOS:
            try:
                # Baixa os dados online de forma direta e sem filtros que causam travamento
                dados = ticker_data.download(tickers=ativo, period=PERIODO, interval=INTERVALO, progress=False)
                
                if dados is None or dados.empty:
                    status_robo[ativo] = "Conectando ao mercado..."
                    continue
                    
                sinal, preco = calcular_estrategia(dados)
                status_robo[ativo] = f"{sinal} — às {time.strftime('%H:%M:%S')}"
                
                if sinal != ultimos_sinais[ativo] and "AGUARDANDO" not in sinal and "dados" not in sinal:
                    print(f"⚠️ [SINAL 5M] {ativo.replace('=X', '')}: {sinal}")
                    ultimos_sinais[ativo] = sinal
                
                # Pausa obrigatória de 4 segundos para evitar punições por velocidade da API
                time.sleep(4.0)
                
            except Exception as e:
                status_robo[ativo] = "Reconectando..."
        
        # Refaz o teste completo a cada 45 segundos para manter o gráfico de 5m sempre atualizado
        time.sleep(45)

# Inicializa o monitoramento em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
