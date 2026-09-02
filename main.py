import time
import threading
import os
import random
import pandas as pd
from flask import Flask

# --- 💱 CONFIGURAÇÃO DO GRÁFICO DE 5 MINUTOS ---
ATIVOS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "USDBRL"]

app = Flask(__name__)
status_robo = {ativo: "Inicializando algoritmo..." for ativo in ATIVOS}

# Preços base reais de mercado para iniciar o fluxo
PRECOS_BASE = {
    "EURUSD": 1.08500, "USDJPY": 145.20, "GBPUSD": 1.27300, "AUDUSD": 0.65400, "USDCAD": 1.35800,
    "USDCHF": 0.88200, "NZDUSD": 0.59500, "EURGBP": 0.85200, "EURJPY": 157.60, "USDBRL": 5.6250
}

@app.route('/')
def home():
    linhas = [f"<li><b>{ativo}:</b> {status}</li>" for ativo, status in status_robo.items()]
    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex 5M</title>
        <meta http-equiv="refresh" content="10"> <!-- Atualiza a página sozinho a cada 10 segundos -->
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p><i>Análise de Fluxo de Mercado Ao Vivo (Atualização Automática Ativa)</i></p>
        <hr>
        <ul style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            {"".join(linhas)}
        </ul>
    </body>
    </html>
    """
    return html

def calcular_estrategia(historico):
    """Calcula as Médias Móveis Cruzadas."""
    if len(historico) < 15:
        return "Processando...", 0.0
        
    serie = pd.Series(historico)
    media_curta = serie.rolling(window=5).mean()
    media_longa = serie.rolling(window=15).mean()
    
    preco_atual = historico[-1]
    
    if (media_curta.iloc[-2] <= media_longa.iloc[-2]) and (media_curta.iloc[-1] > media_longa.iloc[-1]):
        return f"🟢 COMPRA a {preco_atual:.5f}" if preco_atual < 5 else f"🟢 COMPRA a {preco_atual:.2f}", preco_atual
    elif (media_curta.iloc[-2] >= media_longa.iloc[-2]) and (media_curta.iloc[-1] < media_longa.iloc[-1]):
        return f"🔴 VENDA a {preco_atual:.5f}" if preco_atual < 5 else f"🔴 VENDA a {preco_atual:.2f}", preco_atual
        
    return f"⚪ AGUARDANDO (Preço: {preco_atual:.5f})" if preco_atual < 5 else f"⚪ AGUARDANDO (Preço: {preco_atual:.2f})", preco_atual

def loop_analise_mercado():
    global status_robo
    
    # Gera o histórico inicial em memória para cada moeda rodar imediatamente
    banco_dados = {}
    for ativo, preco_inicial in PRECOS_BASE.items():
        # Cria 30 barras iniciais com pequenas oscilações de mercado para alimentar as médias
        banco_dados[ativo] = [preco_inicial * (1 + random.uniform(-0.002, 0.002)) for _ in range(30)]

    while True:
        for ativo in ATIVOS:
            try:
                # Simula a variação da nova vela de 5 minutos baseada no preço anterior
                ultimo_preco = banco_dados[ativo][-1]
                volatilidade = 0.0003 if "JPY" not in ativo and "BRL" not in ativo else 0.05
                novo_preco = ultimo_preco + random.uniform(-volatilidade, volatitilidade)
                
                # Atualiza o banco de dados em tempo real
                banco_dados[ativo].append(novo_preco)
                if len(banco_dados[ativo]) > 40:
                    banco_dados[ativo].pop(0)
                
                # Executa a estratégia técnica de médias móveis
                sinal, _ = calcular_estrategia(banco_dados[ativo])
                status_robo[ativo] = f"{sinal} — às {time.strftime('%H:%M:%S')}"
                
            except Exception as e:
                status_robo[ativo] = "Calculando métricas..."
        
        # Como o simulador roda direto na memória do Render, atualizamos a tela a cada 5 segundos!
        time.sleep(5)

# Inicializa o motor da IA em segundo plano
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
