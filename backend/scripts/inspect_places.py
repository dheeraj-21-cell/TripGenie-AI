import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("d:/TripGenie-AI/backend/data/places.db")
c = conn.cursor()

print("--- Searching Darj ---")
darj_rows = c.execute("SELECT name, name_ascii, region, country, full_name, population FROM places WHERE name_ascii LIKE '%Darj%' OR full_name LIKE '%Darj%'").fetchall()
print("Darj rows:", darj_rows)

print("\n--- Searching San Jose USA ---")
sanjose_us = c.execute("SELECT name, name_ascii, region, country, full_name, population FROM places WHERE name_ascii = 'San Jose' AND country_code = 'US'").fetchall()
for r in sanjose_us:
    print(" ", r)
