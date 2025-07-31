# main.py
import ccxt, os, time, requests
from datetime import datetime

# === Configurações da Bitget ===
def conectar_bitget():
    return ccxt.bitget({
        'apiKey': os.getenv('BITGET_API_KEY'),
        'secret': os.getenv('BITGET_SECRET'),
        'password': os.getenv('BITGET_PASSWORD'),
        'options': {'defaultType': 'swap'}
    })

# === Enviar mensagem no Telegram ===
def enviar_telegram(mensagem):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print("Telegram não configurado")
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': mensagem}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        print("Falha ao enviar Telegram")

# === Lógica do IMPULSO-BEAR ===
def checar_sinal(candles):
    close = [c[4] for c in candles]
    volume = [c[5] for c in candles]
    high = [c[2] for c in candles]
    low = [c[3] for c in candles]

    # Condições
    pump = close[-1] > close[-6] * 1.12  # +12% em 30m
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

# === Loop principal ===
def main():
    exchange = conectar_bitget()
    symbol = os.getenv('SYMBOL', 'SOL/USDT:USDT')
    while True:
        try:
            candles = exchange.fetch_ohlcv(symbol, '3m', limit=20)
            if len(candles) < 10:
                time.sleep(10)
                continue

            if checar_sinal(candles):
                # Verifica se já tem posição
                try:
                    positions = exchange.fetch_positions([symbol])
                    position = [p for p in positions if p['side'] != 'none'][0]
                    if position['contracts'] > 0:
                        print("Já tem posição aberta")
                        time.sleep(60)
                        continue
                except:
                    pass

                # === Entrada com $1 ===
                leverage = int(os.getenv('LEVERAGE', 20))
                exchange.set_leverage(leverage, symbol)
                markets = exchange.load_markets()
                market = markets[symbol]
                price = candles[-1][4]
                notional = float(os.getenv('POSITION_SIZE', 1))  # $1
                amount = notional / price * leverage
                amount = amount / market['contractSize']

                order = exchange.create_order(symbol, 'market', 'sell', amount)
                msg = f"🚨 SHORT ABERTO\nPar: {symbol}\nPreço: ${price:.2f}\nMargem: ${notional}, x{leverage}"
                enviar_telegram(msg)
                print(msg)

                # Cooldown
                time.sleep(300)

        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
