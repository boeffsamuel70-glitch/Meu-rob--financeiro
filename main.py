import time
import threading
import os
import random
from flask import Flask, jsonify

# --- 💱 CONFIGURAÇÃO DOS ATIVOS ---
ATIVOS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "USDBRL"]

app = Flask(__name__)

PRECOS_BASE = {
    "EURUSD": 1.0850, "USDJPY": 145.20, "GBPUSD": 1.2730, "AUDUSD": 0.6540, "USDCAD": 1.3580,
    "USDCHF": 0.8820, "NZDUSD": 0.5950, "EURGBP": 0.8520, "EURJPY": 157.60, "USDBRL": 5.6250
}

status_robo = {}
for ativo, preco in PRECOS_BASE.items():
    formato = f"{preco:.5f}" if preco < 5 else f"{preco:.2f}"
    status_robo[ativo] = f"⚪ AGUARDANDO (Preço: {formato}) — às {time.strftime('%H:%M:%S')}"

@app.route('/')
def home():
    # Código com proteção dupla anti-cache e JavaScript forçado
    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex 5M</title>
        <script>
            function atualizarDados() {
                // O código adiciona um número aleatório no final da URL (?t=...) 
                // Isso obriga o navegador a buscar dados novos e ignora o travamento
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
                    })
                    .catch(error => console.log('Erro de conexão:', error));
            }
            // Executa a atualização forçada a cada 2 segundos
            setInterval(atualizarDados, 2000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p><i>Painel em Tempo Real (Proteção Ativa Anti-Travamento)</i></p>
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
    # Envia os dados e avisa o navegador que é proibido guardar essa resposta no cache
    resposta = jsonify(status_robo)
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resposta

def calcular_sinal():
    # Aumentei a frequência matemática para os sinais aparecerem bem rápido na sua tela
    sorteio = random.randint(1, 15)
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
                variacao = 0.0003 if PRECOS_BASE[ativo] < 5 else 0.04
                novo_preco = ultimo_preco + random.uniform(-variacao, variacao)
                
                banco_dados[ativo].append(novo_preco)
                if len(banco_dados[ativo]) > 10:
                    banco_dados[ativo].pop(0)
                
                sinal = calcular_sinal()
                formato_preco = f"{novo_preco:.5f}" if novo_preco < 5 else f"{novo_preco:.2f}"
                
                if "AGUARDANDO" in sinal:
                    status_robo[ativo] = f"{sinal} (Preço: {formato_preco}) — às {time.strftime('%H:%M:%S')}"
                else:
                    status_robo[ativo] = f"<span style='color: white; background-color: " + ("green" if "COMPRA" in sinal else "red") + f"; padding: 2px 6px; border-radius: 4px;'><b>{sinal} a {formato_preco}</b></span> — às {time.strftime('%H:%M:%S')}"
                    
            except Exception:
                pass
        
        # O robô atualiza os valores internos a cada 2 segundos
        time.sleep(2)

threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
