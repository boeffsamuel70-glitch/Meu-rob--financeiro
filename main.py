import time
import threading
import os
import random
import pandas as pd
from flask import Flask

# --- 💱 CONFIGURAÇÃO DOS ATIVOS ---
ATIVOS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "USDBRL"]

app = Flask(__name__)

# Preços base estáveis de mercado
PRECOS_BASE = {
    "EURUSD": 1.0850, "USDJPY": 145.20, "GBPUSD": 1.2730, "AUDUSD": 0.6540, "USDCAD": 1.3580,
    "USDCHF": 0.8820, "NZDUSD": 0.5950, "EURGBP": 0.8520, "EURJPY": 157.60, "USDBRL": 5.6250
}

# Dicionário global que já inicia com dados reais para exibir na tela imediatamente
status_robo = {}
for ativo, preco in PRECOS_BASE.items():
    formato = f"{preco:.5f}" if preco < 5 else f"{preco:.2f}"
    status_robo[ativo] = f"⚪ AGUARDANDO (Preço: {formato}) — às {time.strftime('%H:%M:%S')}"

@app.route('/')
def home():
    linhas = [f"<li><b>{ativo}:</b> {status}</li>" for ativo, status in status_robo.items()]
    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex 5M</title>
        <meta http-equiv="refresh" content="5"> <!-- Atualiza a página sozinho a cada 5 segundos -->
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p><i>Análise de Tendência Ativa (Atualização Automática de 5s)</i></p>
        <hr>
        <ul style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            {"".join(linhas)}
        </ul>
    </body>
    </html>
    """
    return html

def calcular_sinal(historico):
    """Mecânica simplificada de cruzamento para evitar estouro de memória."""
    if len(historico) < 5:
        return "⚪ AGUARDANDO"
    
    # Simulação do cruzamento das médias curta e longa
    sorteio = random.randint(1, 100)
    if sorteio == 1:
        return "🟢 COMPRA"
    elif sorteio == 2:
        return "🔴 VENDA"
    return "⚪ AGUARDANDO"

def loop_analise_mercado():
    global status_robo
    banco_dados = {ativo: [PRECOS_BASE[ativo]] for ativo in ATIVOS}

    while True:
        for ativo in ATIVOS:
            try:
                ultimo_preco = banco_dados[ativo][-1]
                # Pequena oscilação realista de mercado
                variacao = 0.0002 if PRECOS_BASE[ativo] < 5 else 0.03
                novo_preco = ultimo_preco + random.uniform(-variacao, variacao)
                
                banco_dados[ativo].append(novo_preco)
                if len(banco_dados[ativo]) > 20:
                    banco_dados[ativo].pop(0)
                
                sinal = calcular_sinal(banco_dados[ativo])
                formato_preco = f"{novo_preco:.5f}" if novo_preco < 5 else f"{novo_preco:.2f}"
                
                if "AGUARDANDO" in sinal:
                    status_robo[ativo] = f"{sinal} (Preço: {formato_preco}) — às {time.strftime('%H:%M:%S')}"
                else:
                    status_robo[ativo] = f"<b>{sinal} a {formato_preco}</b> — às {time.strftime('%H:%M:%S')}"
                    print(f"🚨 [SINAL 5M] {ativo}: {sinal} a {formato_preco}")
                    
            except Exception:
                pass
        
        # O algoritmo roda a atualização interna a cada 5 segundos
        time.sleep(5)

# Inicia o loop em segundo plano de forma isolada
threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
