import os
import requests
import json

def get_env_variable(key):
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
    print("[ERROR] GEMINI_API_KEY no encontrada")
    exit(1)

# Noticia de prueba ficticia pero realista para San Juan
title = "Feroz choque en Rivadavia: un auto volcó en Avenida Libertador y Santo Domingo"
description = "Un Peugeot 208 terminó con las ruedas para arriba tras colisionar con una camioneta. No se registraron víctimas fatales, pero el conductor fue trasladado al Hospital Rawson."
body_text = """
El siniestro vial ocurrió cerca de las 23 horas de este viernes en el departamento Rivadavia. 
Por motivos que se investigan, un automóvil marca Peugeot 208 que circulaba por Avenida Libertador San Martín en sentido oeste-este colisionó fuertemente contra una camioneta Hilux a la altura de la intersección con calle Santo Domingo.
Debido al violento impacto, el Peugeot dio un vuelco y quedó volcado sobre la calzada. 
Al lugar asistió personal policial de la Comisaría 13° y personal médico del 107, quienes asistieron a los conductores. 
Afortunadamente, los involucrados solo sufrieron golpes leves y no hubo fallecidos en el lugar, aunque el joven conductor del auto fue derivado por prevención al servicio de urgencias del Hospital Guillermo Rawson.
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
headers = {"Content-Type": "application/json"}

prompt = f"""Analiza la siguiente noticia de la provincia de San Juan, Argentina, y extrae la información solicitada de forma estructurada.

Título: {title}
Descripción: {description}
Cuerpo: {body_text}"""

payload = {
    "contents": [{
        "parts": [{"text": prompt}]
    }],
    "generationConfig": {
        "responseMimeType": "application/json",
        "responseSchema": {
            "type": "OBJECT",
            "properties": {
                "location_query": {
                    "type": "STRING",
                    "description": "Una consulta de dirección limpia y específica en San Juan, Argentina. Ej: 'Avenida Libertador & San Miguel' o 'Ruta 40 y Calle 9' o 'Hospital Rawson'. Si solo se menciona un departamento general sin calles ni referencias de altura, devolver el nombre del departamento/localidad."
                },
                "is_approximate": {
                    "type": "BOOLEAN",
                    "description": "true si la dirección es aproximada (solo se conoce el departamento, localidad o barrio general sin calles específicas). false si la dirección es exacta (se menciona una calle y altura, intersección de calles, o un lugar muy específico como un hospital o plaza)."
                },
                "is_fatal": {
                    "type": "BOOLEAN",
                    "description": "true si la noticia indica claramente que hubo al menos una víctima fatal o fallecido en el lugar. false en caso contrario."
                },
                "category": {
                    "type": "STRING",
                    "enum": ["choque", "vuelco", "atropello", "incendio-vivienda", "incendio-pastizales", "incendio-vehiculo", "arboles", "corte", "techo", "incendio", "accidente", "desconocido"],
                    "description": "La categoría del incidente."
                }
            },
            "required": ["location_query", "is_approximate", "is_fatal", "category"]
        }
    }
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"[STATUS] Código de estado: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        parsed = json.loads(text)
        print(f"[SUCCESS] JSON extraído por Gemini:")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    else:
        print(f"[FAILED] Error en la API: {response.text}")
except Exception as e:
    print(f"[ERROR] Excepción: {e}")
