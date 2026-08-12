import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

SYMBOL = "BTCUSDT"
INTERVAL = "15m"
RSI_PERIOD = 14

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def get_klines():
    url = (
        "https://api.binance.com/api/v3/klines"
        f"?symbol={SYMBOL}&interval={INTERVAL}&limit=100"
    )

    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode())


def calculate_rsi(closes, period=14):
    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []

    def get_rsi(gain, loss):
        if loss == 0:
            return 100.0
        rs = gain / loss
        return 100.0 - (100.0 / (1.0 + rs))

    rsi_values.append(get_rsi(avg_gain, avg_loss))

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        rsi_values.append(get_rsi(avg_gain, avg_loss))

    return rsi_values


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()

    request = urllib.request.Request(url, data=data, method="POST")

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode()


def main():
    klines = get_klines()

    # Ignoramos la vela actual porque todavía está formándose.
    closed_klines = klines[:-1]

    closes = [float(k[4]) for k in closed_klines]

    rsi = calculate_rsi(closes, RSI_PERIOD)

    previous_rsi = rsi[-2]
    current_rsi = rsi[-1]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Cruce hacia abajo de 30
    if previous_rsi > 30 and current_rsi <= 30:
        send_telegram(
            f"🔴 RSI BTC/USDT\n\n"
            f"RSI(14) cruzó hacia ABAJO de 30.\n"
            f"RSI actual: {current_rsi:.2f}\n"
            f"Temporalidad: 15 minutos\n"
            f"Hora: {now}"
        )

    # Cruce hacia arriba de 70
    elif previous_rsi < 70 and current_rsi >= 70:
        send_telegram(
            f"🟢 RSI BTC/USDT\n\n"
            f"RSI(14) cruzó hacia ARRIBA de 70.\n"
            f"RSI actual: {current_rsi:.2f}\n"
            f"Temporalidad: 15 minutos\n"
            f"Hora: {now}"
        )


if name == "main":
    main()
