import os
import time
import requests
import yfinance as yf

# 1. Credenciales leídas de forma segura desde GitHub Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. Configuración explícita de alertas
ALERTAS = {
    "AMZN": {"objetivo": 260.0, "tipo": "SUBIDA"},
    "NVDA": {"objetivo": 235.0, "tipo": "SUBIDA"},
    "UBER": {"objetivo": 70.0,  "tipo": "BAJADA"},
    "TMDX": {"objetivo": 91.0,  "tipo": "SUBIDA"},
}

def enviar_telegram(mensaje: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")
        return False

def revisar():
    print("Revisando cotizaciones...")
    for ticker, cfg in ALERTAS.items():
        try:
            obj = cfg["objetivo"]
            tipo = cfg["tipo"]
            activo = yf.Ticker(ticker)
            precio_actual = activo.fast_info['last_price']
            
            print(f"[{ticker}] Actual: ${precio_actual:.2f} | Condición: {tipo} a ${obj:.2f}")

            se_cumple = False
            if tipo == "SUBIDA" and precio_actual >= obj:
                se_cumple = True
            elif tipo == "BAJADA" and precio_actual <= obj:
                se_cumple = True

            if se_cumple:
                icono = "🚀" if tipo == "SUBIDA" else "🔻"
                texto = "alcanzó o superó el techo" if tipo == "SUBIDA" else "perforó el suelo"
                mensaje = (
                    f"{icono} *ALERTA EJECUTADA: {ticker}*\n\n"
                    f"• *Precio actual:* `${precio_actual:.2f}`\n"
                    f"• *Nivel objetivo:* `${obj:.2f}`\n"
                    f"• *Condición:* El activo {texto}."
                )
                enviar_telegram(mensaje)
                print(f"-> Disparada alerta para {ticker}.")

        except Exception as e:
            print(f"Error consultando {ticker}: {e}")

if __name__ == "__main__":
    revisar()
