import requests
import time
import datetime
import numpy as np

# === CONFIG ===
TELEGRAM_TOKEN = "AAGa149FoOiXl9ATmVEcMsPzG9WPOh3gyUI"
CHAT_ID = "1870485251"
FINNHUB_API_KEY = "d1a0mkhr01qltimufc6gd1a0mkhr01qltimufc70"
SYMBOLS = {
    "BTC/USD": "BINANCE:BTCUSDT",
    "XAU/USD": "OANDA:XAU_USD",
    "EUR/USD": "OANDA:EUR_USD",
    "USD/JPY": "OANDA:USD_JPY"
}
INTERVAL = "1"  # 1-minute
ALERTED = {}

# === FUNCTIONS ===

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_candles(symbol):
    url = f"https://finnhub.io/api/v1/forex/candle?symbol={symbol}&resolution={INTERVAL}&count=100&token={FINNHUB_API_KEY}"
    r = requests.get(url)
    data = r.json()
    if data['s'] != 'ok':
        return None
    return data['c']  # close prices

def stochastic_rsi(prices, period=14):
    prices = np.array(prices)
    delta = np.diff(prices)
    up = delta.clip(min=0)
    down = -delta.clip(max=0)
    avg_gain = np.convolve(up, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(down, np.ones(period)/period, mode='valid')
    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    min_rsi = np.min(rsi[-period:])
    max_rsi = np.max(rsi[-period:])
    stoch_rsi = 100 * (rsi[-1] - min_rsi) / (max_rsi - min_rsi + 1e-6)
    return stoch_rsi, rsi

def check_signals():
    for name, symbol in SYMBOLS.items():
        prices = get_candles(symbol)
        if prices is None or len(prices) < 30:
            continue

        stoch, rsi = stochastic_rsi(prices)
        now = datetime.datetime.now().strftime('%H:%M:%S')

        if stoch > 80:
            signal = f"🔴 SELL signal on {name} at {now}\nStochastic RSI: {stoch:.2f}"
        elif stoch < 20:
            signal = f"🟢 BUY signal on {name} at {now}\nStochastic RSI: {stoch:.2f}"
        else:
            continue

        if ALERTED.get(name) != signal:
            send_telegram_alert(signal)
            ALERTED[name] = signal

# === MAIN LOOP ===

print("🚀 Bot is running...")
while True:
    try:
        check_signals()
        time.sleep(60)
    except Exception as e:
        print("Error:", e)
        time.sleep(60)
