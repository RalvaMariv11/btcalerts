import os
import json
import requests
import yfinance as yf

# 1. Credenciales desde Secrets
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 2. Configuración de alertas
ALERTAS = {
    "AMZN": {"objetivo": 260.0, "tipo": "SUBIDA"},
    "NVDA": {"objetivo": 235.0, "tipo": "SUBIDA"},
    "UBER": {"objetivo": 70.0,  "tipo": "BAJADA"},
    "TMDX": {"objetivo": 91.0,  "tipo": "SUBIDA"},
}

ARCHIVO_ESTADO = "estado.json"

def cargar_estado():
    if os.path.exists(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_estado(estado):
    with open(ARCHIVO_ESTADO, "w") as f:
        json.dump(estado, f, indent=4)

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
    estado = cargar_estado()
    hubo_cambios = False
    
    # Filtrar solo los que aún no se han disparado
    pendientes = [t for t, cfg in ALERTAS.items() if not estado.get(t, False)]
    
    if not pendientes:
        print("Todas las alertas ya fueron disparadas previamente. Nada por hacer.")
        return False

    print(f"Revisando activos pendientes: {pendientes}...")
    
    for ticker in pendientes:
        try:
            cfg = ALERTAS[ticker]
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
                    f"• *Condición:* El activo {texto}.\n\n"
                    f"⚠️ _Esta alerta se disparó (1/1) y queda guardada en el historial para no repetir._"
                )
                if enviar_telegram(mensaje):
                    estado[ticker] = True
                    hubo_cambios = True
                    print(f"-> Disparada y registrada alerta para {ticker}.")

        except Exception as e:
            print(f"Error consultando {ticker}: {e}")

    if hubo_cambios:
        guardar_estado(estado)
        return True
    
    return False

if __name__ == "__main__":
    revisar()
