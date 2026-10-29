import sqlite3
import sys

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("d:/TripGenie-AI/backend/data/places.db")
c = conn.cursor()

queries = ["Banff", "Manali", "Paris", "Cambridge", "Iceland", "Japan", "Goa", "Bali", "Positano", "Hallstatt", "Zermatt", "Texas"]

for q in queries:
    prefix = f"{q}%"
    contains = f"%{q}%"
    rows = c.execute("""
    SELECT name, region, country, country_code, full_name, place_type, population
    FROM places
    WHERE name_ascii LIKE ?
       OR country LIKE ?
       OR region LIKE ?
       OR full_name LIKE ?
    ORDER BY
       (CASE
          WHEN LOWER(name_ascii) = LOWER(?) THEN 1
          WHEN LOWER(country) = LOWER(?) THEN 2
          WHEN name_ascii LIKE ? THEN 3
          WHEN country LIKE ? THEN 4
          WHEN region LIKE ? THEN 5
          ELSE 6
        END) ASC,
       (place_type = 'country') DESC,
       population DESC
    LIMIT 3
    """, (prefix, prefix, prefix, contains, q, q, prefix, prefix, prefix)).fetchall()

    print(f"=== Query: {q} ===")
    for r in rows:
        print(f"  {r[0]} | Region: {r[1]} | Country: {r[2]} ({r[3]}) | Full: {r[4]} | Type: {r[5]}")
