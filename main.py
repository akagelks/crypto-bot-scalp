# main.py
import ccxt, os, time, requests
from datetime import datetime

def conectar_bitget():
    # Chaves de API são configuradas no Railway (não estão no código)
    return ccxt.bitget({
        'apiKey': os.getenv('BITGET_API_KEY'),
        'secret': os.getenv('BITGET_SECRET'),
        'options': {'defaultType': 'swap'}
    })

def enviar_telegram(mensagem):
    # Token e ID do Telegram são configurados no Railway (não estão no código)
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': mensagem}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

def checar_sinal(candles):
    close = [c[4] for c in candles]
    volume = [c[5] for c in candles]
    high = [c[2] for c in candles]
    low = [c[3] for c in candles]

    pump = close[-1] > close[-6] * 1.12
    avg_vol = sum(volume[-11:-1]) / 10
    volume_alto = volume[-1] > 2.5 * avg_vol
    rsi = calcular_rsi(close, 5)
    rsi_alto = rsi[-1] > 80 and rsi[-1] < rsi[-2]
    ema9 = calcular_ema(close, 9)
    tendencia_baixa = ema9[-1] < ema9[-2] < ema9[-3]
    wick_ratio = (high[-1] - close[-1]) / (high[-1] - low[-1]) if high[-1] != low[-1] else 0
    rejeicao = wick_ratio > 0.7

    return pump and volume_alto and rsi_alto and tendencia_baixa and rejeicao

def calcular_rsi(prices, period=14):
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    rsi = [100 - (100 / (1 + rs))]
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period-1) + gains[i]) / period
        avg_loss = (avg_loss * (period-1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi.append(100 - (100 / (1 + rs)))
    return rsi

def calcular_ema(prices, period):
    ema = [prices[0]]
    multiplier = 2 / (period + 1)
    for price in prices[1:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return ema

def main():
    exchange = conectar_bitget()
    
    # Pares confirmados e operáveis na Bitget
    pares = [
        'SOL/USDT:USDT',  # Explosivo, correlacionado com ETH/BTC
        'DOGE/USDT:USDT',  # Memecoin clássico, fácil scalp
        'FET/USDT:USDT',  # Narrativa de IA → correção técnica
        'APT/USDT:USDT',  # Altcoin emergente → spikes frequentes
        'WIF/USDT:USDT',  # Novo memecoin explosivo
        'ETH/USDT:USDT',  # Segundo maior cripto por market cap
        'BTC/USDT:USDT',  # Maior cripto por market cap
        'MATIC/USDT:USDT'  # Blockchain escalável → movimentos técnicos
    ]
    
    # Variáveis fixas
    leverage = 20
    position_size = 1  # $1 por trade
    
    while True:
        try:
            # Verifica se já tem posição aberta
            posicoes_abertas = []
            for par in pares:
                try:
                    positions = exchange.fetch_positions([par])
                    for pos in positions:
                        if pos['side'] != 'none' and pos['contracts'] > 0:
                            posicoes_abertas.append(par)
                except:
                    continue
            
            if posicoes_abertas:
                print(f"Já tem posição aberta em {posicoes_abertas}")
                time.sleep(60)
                continue

            # Checa cada par
            for par in pares:
                try:
                    candles = exchange.fetch_ohlcv(par, '3m', limit=20)
                    if len(candles) < 10:
                        continue

                    if checar_sinal(candles):
                        # === Calcular valores da entrada ===
                        markets = exchange.load_markets()
                        market = markets[par]
                        price = candles[-1][4]
                        amount = position_size / price * leverage
                        amount = amount / market['contractSize']
                        tp_price = price * 0.97  # Take Profit 3% abaixo

                        # === Verificar saldo ===
                        balance = exchange.fetch_balance()
                        free_balance = float(balance['USDT']['free'])
                        if free_balance < position_size:
                            # Notificação de simulação de entrada (sem saldo)
                            msg = (
                                f"✅ Simulação de Entrada ✅\n"
                                f"Par: {par}\n"
                                f"Preço: ${price:.2f}\n"
                                f"Margem: ${position_size}\n"
                                f"Alavancagem: x{leverage}\n"
                                f"Take Profit: ${tp_price:.2f}\n\n"
                                f"⚠️ Nota: Saldo insuficiente para abrir posição."
                            )
                            enviar_telegram(msg)
                            print(msg)
                            break  # Sai do loop após simulação

                        # === Criar ordem real ===
                        order = exchange.create_order(par, 'market', 'sell', amount, params={'takeProfit': tp_price})
                        msg = (
                            f"✅ Entrada Realizada ✅\n"
                            f"Par: {par}\n"
                            f"Preço: ${price:.2f}\n"
                            f"Margem: ${position_size}\n"
                            f"Alavancagem: x{leverage}\n"
                            f"Take Profit: ${tp_price:.2f}"
                        )
                        enviar_telegram(msg)
                        print(msg)

                        # Sai do loop após entrada
                        break

                except Exception as e:
                    print(f"Erro no par {par}: {e}")
                    continue

        except Exception as e:
            print(f"Erro geral: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
