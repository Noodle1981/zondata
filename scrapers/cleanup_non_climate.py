"""
scrapers/cleanup_non_climate.py
=================================
Limpieza de incidentes no climáticos de la base de datos.

Elimina todos los incidentes cuya categoría corresponde a eventos viales
puros (choque, vuelco, atropello, accidente, transito) que no tienen
relación con el nuevo enfoque climático del proyecto.

Uso:
    python scrapers/cleanup_non_climate.py
    python scrapers/cleanup_non_climate.py --dry-run      (solo muestra lo que se borraría, sin borrar)
    python scrapers/cleanup_non_climate.py --confirm      (ejecuta sin pedir confirmación interactiva)
"""

import sqlite3
import argparse
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'database.sqlite')

# Slugs de categorías que se consideran NO climáticas y deben eliminarse
NON_CLIMATE_CATEGORY_SLUGS = [
    'choque',
    'vuelco',
    'atropello',
    'accidente',
    'transito',
    'transito-urbano',
    'accidente-vial',
    'colision',
]

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inspect(conn):
    cur = conn.cursor()
    cur.execute('''
        SELECT c.slug, COUNT(i.id) as count
        FROM incidents i
        LEFT JOIN categories c ON i.category_id = c.id
        GROUP BY c.slug
        ORDER BY count DESC
    ''')
    rows = cur.fetchall()
    print("\n[INFO] Estado actual de la tabla incidents:")
    print(f"{'Categoria':<35} {'Cantidad':>8}")
    print("-" * 45)
    total = 0
    for row in rows:
        slug = row['slug'] or 'sin-categoria'
        count = row['count']
        total += count
        print(f"  {slug:<33} {count:>8}")
    print("-" * 45)
    print(f"  {'TOTAL':<33} {total:>8}\n")
    return total

def get_vial_incident_ids(conn):
    """Obtiene los IDs de incidentes viales para eliminar."""
    placeholders = ','.join('?' * len(NON_CLIMATE_CATEGORY_SLUGS))
    cur = conn.cursor()
    cur.execute(f'''
        SELECT i.id, c.slug, i.title
        FROM incidents i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE c.slug IN ({placeholders})
    ''', NON_CLIMATE_CATEGORY_SLUGS)
    return cur.fetchall()

def cleanup(conn, dry_run=False):
    incidents = get_vial_incident_ids(conn)

    if not incidents:
        print("[OK] No hay incidentes viales para eliminar. La base de datos ya esta limpia.")
        return

    print(f"\n[BORRAR] Incidentes a eliminar ({len(incidents)} registros):")
    for i in incidents:
        print(f"  [ID {i['id']}] ({i['slug']}) - {i['title'][:80] if i['title'] else 'sin titulo'}")

    if dry_run:
        print(f"\n[DRY RUN] Se eliminarian {len(incidents)} incidentes. No se hizo ningun cambio.")
        return

    ids = [row['id'] for row in incidents]
    placeholders = ','.join('?' * len(ids))
    cur = conn.cursor()

    # Eliminar registros relacionados en tablas dependientes si las hay
    # (medias/attachments si existieran — se elimina en cascada por FK o manualmente)
    cur.execute(f'DELETE FROM incidents WHERE id IN ({placeholders})', ids)
    conn.commit()

    print(f"\n[OK] Limpieza completada: {len(incidents)} incidentes viales eliminados.")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def cleanup_orphan_categories(conn, dry_run=False):
    """
    Elimina de la tabla `categories` aquellas categorías viales que ya
    no tienen ningún incidente asociado.
    """
    placeholders = ','.join('?' * len(NON_CLIMATE_CATEGORY_SLUGS))
    cur = conn.cursor()
    cur.execute(f'''
        SELECT c.id, c.slug, COUNT(i.id) as incident_count
        FROM categories c
        LEFT JOIN incidents i ON i.category_id = c.id
        WHERE c.slug IN ({placeholders})
        GROUP BY c.id
        HAVING incident_count = 0
    ''', NON_CLIMATE_CATEGORY_SLUGS)
    orphans = cur.fetchall()

    if not orphans:
        return

    print(f"\n[INFO] Categorias viales sin incidentes (candidatas a eliminar): {len(orphans)}")
    for o in orphans:
        print(f"  [ID {o['id']}] {o['slug']}")

    if dry_run:
        print("   (DRY RUN: no se eliminaron)")
        return

    ids = [o['id'] for o in orphans]
    placeholders2 = ','.join('?' * len(ids))
    cur.execute(f'DELETE FROM categories WHERE id IN ({placeholders2})', ids)
    conn.commit()
    print(f"   [OK] {len(orphans)} categorias viales huerfanas eliminadas.")

def main():
    parser = argparse.ArgumentParser(
        description='Limpia incidentes viales no climáticos de la base de datos ZonData.'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra qué se borraría, sin ejecutar ningún cambio.')
    parser.add_argument('--confirm', action='store_true',
                        help='Ejecuta sin pedir confirmación interactiva.')
    args = parser.parse_args()

    conn = get_conn()

    print("=" * 60)
    print("  ZonData — Limpieza de Incidentes No Climáticos")
    print("=" * 60)

    total_before = inspect(conn)

    incidents_to_delete = get_vial_incident_ids(conn)
    if not incidents_to_delete:
        print("[OK] La base de datos ya esta limpia. No hay nada que eliminar.")
        conn.close()
        return

    print(f"[ATENCION] Se encontraron {len(incidents_to_delete)} incidentes viales para eliminar.")

    if not args.dry_run and not args.confirm:
        respuesta = input("\n¿Confirmar eliminación? Escribe 'si' para continuar: ").strip().lower()
        if respuesta not in ('si', 'sí', 'yes', 's', 'y'):
            print("[CANCELADO] Operacion cancelada por el usuario.")
            conn.close()
            return

    cleanup(conn, dry_run=args.dry_run)
    cleanup_orphan_categories(conn, dry_run=args.dry_run)

    if not args.dry_run:
        total_after = inspect(conn)
        print(f"[RESULTADO] Incidentes: {total_before} -> {total_after} (eliminados: {total_before - total_after})")

    conn.close()

if __name__ == '__main__':
    main()
