import os
import sqlite3
import subprocess
import sys
from datetime import datetime

# Añadir soporte de importación del SDK de MCP si está instalado
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: El paquete 'mcp' no está instalado. Ejecute 'pip install mcp' para utilizar este servidor.", file=sys.stderr)
    sys.exit(1)

# Inicializar servidor MCP
mcp = FastMCP("ZonData")

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.sqlite")

@mcp.tool()
def get_incidents(date_str: str = None) -> str:
    """
    Obtiene los incidentes registrados para una fecha específica (formato YYYY-MM-DD).
    Si no se especifica la fecha, se usa la fecha de hoy.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    try:
        if not os.path.exists(DB_PATH):
            return f"Error: No se encontró el archivo de base de datos SQLite en: {DB_PATH}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Consultar incidentes de la fecha dada
        # SQLite: strftime('%Y-%m-%d', event_date) = date_str
        cursor.execute(
            """
            SELECT i.id, i.title, i.description, i.latitude, i.longitude, i.event_date, i.status, c.name 
            FROM incidents i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE strftime('%Y-%m-%d', i.event_date) = ?
            """,
            (date_str,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return f"No se encontraron incidentes registrados para la fecha {date_str}."
            
        result = [f"=== Incidentes del {date_str} ==="]
        for row in rows:
            result.append(
                f"ID: {row[0]}\n"
                f"Categoría: {row[7]}\n"
                f"Título: {row[1]}\n"
                f"Descripción: {row[2]}\n"
                f"Coordenadas: {row[3]}, {row[4]}\n"
                f"Fecha del Evento: {row[5]}\n"
                f"Estado: {row[6]}\n"
                f"----------------------------------------"
            )
        return "\n".join(result)
    except Exception as e:
        return f"Error al consultar la base de datos: {str(e)}"

@mcp.tool()
def search_incidents(query: str) -> str:
    """
    Busca incidentes por palabra clave en el título o la descripción.
    """
    try:
        if not os.path.exists(DB_PATH):
            return f"Error: No se encontró el archivo de base de datos SQLite en: {DB_PATH}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar por texto parcial
        search_pattern = f"%{query}%"
        cursor.execute(
            """
            SELECT i.id, i.title, i.description, i.latitude, i.longitude, i.event_date, c.name 
            FROM incidents i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE i.title LIKE ? OR i.description LIKE ?
            LIMIT 10
            """,
            (search_pattern, search_pattern)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return f"No se encontraron incidentes que coincidan con la búsqueda: '{query}'."
            
        result = [f"=== Resultados de búsqueda para: '{query}' ==="]
        for row in rows:
            result.append(
                f"ID: {row[0]}\n"
                f"Categoría: {row[6]}\n"
                f"Título: {row[1]}\n"
                f"Descripción: {row[2]}\n"
                f"Coordenadas: {row[3]}, {row[4]}\n"
                f"Fecha del Evento: {row[5]}\n"
                f"----------------------------------------"
            )
        return "\n".join(result)
    except Exception as e:
        return f"Error al realizar la búsqueda: {str(e)}"

@mcp.tool()
def get_statistics() -> str:
    """
    Obtiene estadísticas generales del estado actual de la base de datos de ZonData.
    """
    try:
        if not os.path.exists(DB_PATH):
            return f"Error: No se encontró el archivo de base de datos SQLite en: {DB_PATH}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total de incidentes
        cursor.execute("SELECT COUNT(*) FROM incidents")
        total_incidents = cursor.fetchone()[0]
        
        # Por categoría
        cursor.execute(
            """
            SELECT c.name, COUNT(i.id) 
            FROM categories c 
            LEFT JOIN incidents i ON i.category_id = c.id 
            GROUP BY c.name
            """
        )
        by_category = cursor.fetchall()
        
        # Incidentes fatales
        cursor.execute("SELECT COUNT(*) FROM incidents WHERE is_fatal = 1")
        fatal_count = cursor.fetchone()[0]
        
        conn.close()
        
        result = [
            "=== ESTADÍSTICAS GENERALES DE ZONDATA ===",
            f"Total de incidentes en DB: {total_incidents}",
            f"Total de incidentes fatales: {fatal_count}\n",
            "--- Incidentes por Categoría ---"
        ]
        for cat, count in by_category:
            result.append(f"- {cat or 'Sin Categoría'}: {count}")
            
        return "\n".join(result)
    except Exception as e:
        return f"Error al obtener estadísticas: {str(e)}"

@mcp.tool()
def run_scraper_manually() -> str:
    """
    Ejecuta el scraper RSS manualmente en segundo plano y reporta los incidentes descubiertos.
    """
    try:
        scraper_path = os.path.join(BASE_DIR, "scrapers", "rss_scraper.py")
        
        # Ejecutar el scraper usando python
        process = subprocess.run(
            [sys.executable, scraper_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if process.returncode == 0:
            return f"Scraper completado con éxito.\n\nSalida estándar:\n{process.stdout}"
        else:
            return f"El scraper falló con código {process.returncode}.\n\nError:\n{process.stderr}"
    except Exception as e:
        return f"Error al ejecutar el scraper: {str(e)}"

if __name__ == "__main__":
    mcp.run()
