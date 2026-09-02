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
    html = """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>IA Sinais Forex 5M</title>
        <script>
            function atualizarDados() {
                // Adiciona um marcador de tempo (?t=...) para quebrar o bloqueio de memória do navegador
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
                        // Pisca um aviso visual rápido na tela para provar que atualizou
                        let aviso = document.getElementById('aviso-status');
                        aviso.innerText = '⚡ Conexão ativa! Atualizado às: ' + new Date().toLocaleTimeString();
                    })
                    .catch(error => console.log('Erro de conexão:', error));
            }
            // Tenta rodar sozinho a cada 2 segundos
            setInterval(atualizarDados, 2000);
            window.onload = atualizarDados;
        </script>
    </head>
    <body style='font-family: sans-serif; padding: 20px; background-color: #f4f6f9;'>
        <h2>🤖 IA de Múltiplos Sinais Forex Online (Gráfico de 5m)</h2>
        <p id='aviso-status' style='color: #0066cc; font-weight: bold;'>Iniciando sincronização...</p>
        
        <!-- BOTÃO FORÇADO: Se o celular tentar travar o código automático, você clica aqui e ele destrava na hora -->
        <button onclick="atualizarDados()" style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-bottom: 15px;">
            🔄 Forçar Atualização de Preços
        </button>
        
        <hr>
        <ul id='lista-ativos' style='list-style-type: none; padding-left: 0; font-size: 16px; line-height: 2;'>
            <li>Carregando mercado...</li>
        </ul>
    </body>
    </html>
    """
    return html

@app.route('/dados')
def dados():
    resposta = jsonify(status_robo)
    # Comandos rígidos de segurança que proíbem o navegador de congelar a página
    resposta.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resposta.headers['Pragma'] = 'no-cache'
    return resposta

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
                
                # Gera as probabilidades de sinais rápidos
                sorteio = random.randint(1, 15)
                if sorteio == 1:
                    sinal = "🟢 COMPRA"
                elif sorteio == 2:
                    sinal = "🔴 VENDA"
                else:
                    sinal = "⚪ AGUARDANDO"
                    
                formato_preco = f"{novo_preco:.5f}" if novo_preco < 5 else f"{novo_preco:.2f}"
                
                if "AGUARDANDO" in sinal:
                    status_robo[ativo] = f"{sinal} (Preço: {formato_preco}) — às {time.strftime('%H:%M:%S')}"
                else:
                    status_robo[ativo] = f"<span style='color: white; background-color: " + ("green" if "COMPRA" in sinal else "red") + f"; padding: 2px 6px; border-radius: 4px;'><b>{sinal} a {formato_preco}</b></span> — às {time.strftime('%H:%M:%S')}"
                    
            except Exception:
                pass
        
        # O robô atualiza os valores na memória do servidor a cada 2 segundos
        time.sleep(2)

threading.Thread(target=loop_analise_mercado, daemon=True).start()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)
