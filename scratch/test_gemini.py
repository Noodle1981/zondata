import os
import requests
import json

def get_env_variable(key):
    # Buscar en el directorio actual y en el directorio padre (.env)
    paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        ".env",
        "d:/Zondata/.env"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(key + "="):
                            val = line.split("=", 1)[1].strip()
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            return val
            except Exception:
                pass
    return os.environ.get(key)

gemini_key = get_env_variable("GEMINI_API_KEY")
if not gemini_key:
    print("[ERROR] GEMINI_API_KEY no encontrada en el archivo .env")
    exit(1)

print(f"[INFO] Probando clave: {gemini_key[:8]}...{gemini_key[-8:] if len(gemini_key) > 16 else ''}")

# Intentar hacer una petición simple a Gemini 2.5 Flash
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
headers = {"Content-Type": "application/json"}
payload = {
    "contents": [{
        "parts": [{"text": "Dime 'Conexión exitosa con Gemini' en español."}]
    }]
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"[STATUS] Código de estado: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        try:
            text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            print(f"[SUCCESS] Respuesta de Gemini: {text}")
        except (KeyError, IndexError):
            print(f"[WARNING] Estructura de respuesta inesperada: {json.dumps(data, indent=2)}")
    else:
        print(f"[FAILED] Error en la API: {response.text}")
except Exception as e:
    print(f"[ERROR] Excepción al realizar la petición: {e}")
