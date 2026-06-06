import sqlite3

conn = sqlite3.connect('database/database.sqlite')
cursor = conn.cursor()

print("=== TABLAS EN LA BASE DE DATOS ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"\nTabla: {table}")
    # Mostrar columnas de cada tabla
    cursor.execute(f"PRAGMA table_info({table});")
    cols = [col[1] for col in cursor.fetchall()]
    print(f"  Columnas: {', '.join(cols)}")
    
    # Si la tabla tiene que ver con reglas (rules), mostrar un par de filas
    if 'rule' in table.lower():
        print("  -- Contenido de muestra --")
        cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"    {r}")
            
conn.close()
