import time
import threading
import os
import yfinance as ticker_data
import pandas as pd
from flask import Flask

# --- 💱 CONFIGURAÇÃO DA LISTA DE ATIVOS EM LOTE ---
ATIVOS = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X",
    "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "USDBRL=X"
]
INTERVALO = "5m"  # Tempo gráfico de 5 minutos garantido
PERIODO = "5d"     # Histórico necessário

app = Flask(__name__)
status_robo = {ativo: "Carregando dados..." for ativo in ATIVOS}

@app.route('/')
def home():
    linhas = [f"<li><b>{ativo.replace('=X', '')}:</b> {status}</li>" for ativo, status in status_robo.items()]
    html = f"""
    <html>
    <head><meta charset='utf-8'><title>IA Sinais Forex 5M</title></head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p><i>Sistema otimizado com download em lote único (Anti-bloqueio)</i></p>
        <hr>
        <ul style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            {"".join(linhas)}
        </ul>
    </body>
    </html>
    """
    return html

def loop_analise_mercado():
    global status_robo
    ultimos_sinais = {ativo: None for ativo in ATIVOS}

    while True:
        try:
            # EXECUTA UM ÚNICO DOWNLOAD EM LOTE PARA TODOS OS ATIVOS (Evita ban do Yahoo)
            dados_lote = ticker_data.download(tickers=ATIVOS, period=PERIODO, interval=INTERVALO, progress=False)
            
            if dados_lote is None or dados_lote.empty:
                for ativo in ATIVOS:
                    status_robo[ativo] = "Aguardando resposta do servidor..."
                time.sleep(30)
                continue

            for ativo in ATIVOS:
                try:
                    # Isola os preços de fechamento ('Close') do ativo correspondente na tabela MultiIndex
                    if ativo in dados_lote['Close'].columns:
                        fechamentos = dados_lote['Close'][ativo].dropna()
                    else:
                        continue

                    valores_limpos = fechamentos.values.flatten()
                    
                    if len(valores_limpos) < 15:
                        status_robo[ativo] = "Aguardando histórico suficiente de barras..."
                        continue

                    # Converte em série temporal para os cálculos de médias móveis
                    serie_precos = pd.Series(valores_limpos)
                    media_curta = serie_precos.rolling(window=5).mean()
                    media_longa = serie_precos.rolling(window=15).mean()
                    
                    preco_atual = float(valores_limpos[-1])
                    
                    # Lógica de cruzamento de tendências
                    if (media_curta.iloc[-2] <= media_longa.iloc[-2]) and (media_curta.iloc[-1] > media_longa.iloc[-1]):
                        sinal = f"🟢 COMPRA a {preco_atual:.5f}"
                    elif (media_curta.iloc[-2] >= media_longa.iloc[-2]) and (media_curta.iloc[-1] < media_longa.iloc[-1]):
                        sinal = f"🔴 VENDA a {preco_atual:.5f}"
                    else:
                        sinal = f"⚪ AGUARDANDO (Preço: {preco_atual:.5f})"

                    status_robo[ativo] = f"{sinal} — às {time.strftime('%H:%M:%S')}"
                    
                    # Registra nos logs internos do Render se houver mudança real
                    if sinal != ultimos_sinais[ativo] and "AGUARDANDO" not in sinal:
                        print(f"⚠️ [SINAL 5M] {ativo.replace('=X', '')}: {sinal}")
                        ultimos_sinais[ativo] = sinal

                except Exception as e:
                    status_robo[ativo] = f"Erro no processamento técnico"
                    
        except Exception as e:
            print(f"Falha na requisição global do lote: {e}")
        
        # Como o download em lote é super rápido, atualizamos a lista inteira a cada 30 segundos
        time.sleep(30)

# Inicializa o monitoramento inteligente em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
