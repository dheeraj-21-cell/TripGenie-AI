"""
Script to build the local SQLite gazetteer database (places.db) from free GeoNames data.
Data source: GeoNames (https://www.geonames.org/export/)
Licensing: Creative Commons Attribution 4.0 International (CC BY 4.0)
Attribution: GeoNames data is provided free of charge under CC BY 4.0.

This script extracts:
1. All ~250 countries and official territories (countryInfo.txt)
2. All ~3,800 primary administrative divisions/states (admin1CodesASCII.txt)
3. All ~70,000 cities and towns worldwide with population >= 5,000 (cities5000.zip)
4. Curated supplementary world-famous heritage and travel destinations under 5,000 population.
"""

import os
import io
import time
import zipfile
import sqlite3
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "places.db"

GEONAMES_BASE = "https://download.geonames.org/export/dump"

SUPPLEMENTARY_DESTINATIONS = [
    {
        "name": "Manali",
        "name_ascii": "Manali",
        "region": "Himachal Pradesh",
        "country": "India",
        "country_code": "IN",
        "full_name": "Manali, Himachal Pradesh, India",
        "place_type": "destination",
        "population": 8099,
        "latitude": 32.2396,
        "longitude": 77.1887,
    },
    {
        "name": "Rishikesh",
        "name_ascii": "Rishikesh",
        "region": "Uttarakhand",
        "country": "India",
        "country_code": "IN",
        "full_name": "Rishikesh, Uttarakhand, India",
        "place_type": "destination",
        "population": 102138,
        "latitude": 30.0869,
        "longitude": 78.2676,
    },
    {
        "name": "Whistler",
        "name_ascii": "Whistler",
        "region": "British Columbia",
        "country": "Canada",
        "country_code": "CA",
        "full_name": "Whistler, British Columbia, Canada",
        "place_type": "destination",
        "population": 11854,
        "latitude": 50.1163,
        "longitude": -122.9574,
    },
    {
        "name": "Zermatt",
        "name_ascii": "Zermatt",
        "region": "Valais",
        "country": "Switzerland",
        "country_code": "CH",
        "full_name": "Zermatt, Valais, Switzerland",
        "place_type": "destination",
        "population": 5765,
        "latitude": 45.9765,
        "longitude": 7.7491,
    },
    {
        "name": "Interlaken",
        "name_ascii": "Interlaken",
        "region": "Bern",
        "country": "Switzerland",
        "country_code": "CH",
        "full_name": "Interlaken, Bern, Switzerland",
        "place_type": "destination",
        "population": 5610,
        "latitude": 46.6863,
        "longitude": 7.8632,
    },
    {
        "name": "Amalfi",
        "name_ascii": "Amalfi",
        "region": "Campania",
        "country": "Italy",
        "country_code": "IT",
        "full_name": "Amalfi, Campania, Italy",
        "place_type": "destination",
        "population": 5100,
        "latitude": 40.6340,
        "longitude": 14.6027,
    },
    {
        "name": "Positano",
        "name_ascii": "Positano",
        "region": "Campania",
        "country": "Italy",
        "country_code": "IT",
        "full_name": "Positano, Campania, Italy",
        "place_type": "destination",
        "population": 3950,
        "latitude": 40.6281,
        "longitude": 14.4850,
    },
    {
        "name": "Hallstatt",
        "name_ascii": "Hallstatt",
        "region": "Upper Austria",
        "country": "Austria",
        "country_code": "AT",
        "full_name": "Hallstatt, Upper Austria, Austria",
        "place_type": "destination",
        "population": 780,
        "latitude": 47.5622,
        "longitude": 13.6493,
    },
    {
        "name": "Oia",
        "name_ascii": "Oia",
        "region": "Santorini, South Aegean",
        "country": "Greece",
        "country_code": "GR",
        "full_name": "Oia, Santorini, Greece",
        "place_type": "destination",
        "population": 1540,
        "latitude": 36.4618,
        "longitude": 25.3753,
    },
    {
        "name": "Fira",
        "name_ascii": "Fira",
        "region": "Santorini, South Aegean",
        "country": "Greece",
        "country_code": "GR",
        "full_name": "Fira, Santorini, Greece",
        "place_type": "destination",
        "population": 1600,
        "latitude": 36.4166,
        "longitude": 25.4324,
    },
    {
        "name": "Santorini",
        "name_ascii": "Santorini",
        "region": "South Aegean",
        "country": "Greece",
        "country_code": "GR",
        "full_name": "Santorini, Greece",
        "place_type": "destination",
        "population": 15500,
        "latitude": 36.3932,
        "longitude": 25.4615,
    },
    {
        "name": "Leh Ladakh",
        "name_ascii": "Leh Ladakh",
        "region": "Ladakh",
        "country": "India",
        "country_code": "IN",
        "full_name": "Leh Ladakh, India",
        "place_type": "destination",
        "population": 30870,
        "latitude": 34.1526,
        "longitude": 77.5771,
    },
    {
        "name": "Havelock Island",
        "name_ascii": "Havelock Island",
        "region": "Andaman & Nicobar",
        "country": "India",
        "country_code": "IN",
        "full_name": "Havelock Island, Andaman & Nicobar, India",
        "place_type": "destination",
        "population": 6300,
        "latitude": 11.9761,
        "longitude": 92.9876,
    },
    {
        "name": "Bora Bora",
        "name_ascii": "Bora Bora",
        "region": "Leeward Islands",
        "country": "French Polynesia",
        "country_code": "PF",
        "full_name": "Bora Bora, French Polynesia",
        "place_type": "destination",
        "population": 10600,
        "latitude": -16.5004,
        "longitude": -151.7415,
    },
    {
        "name": "Machu Picchu",
        "name_ascii": "Machu Picchu",
        "region": "Cusco",
        "country": "Peru",
        "country_code": "PE",
        "full_name": "Machu Picchu, Cusco, Peru",
        "place_type": "destination",
        "population": 4500,
        "latitude": -13.1631,
        "longitude": -72.5450,
    },
    {
        "name": "Lake Louise",
        "name_ascii": "Lake Louise",
        "region": "Alberta",
        "country": "Canada",
        "country_code": "CA",
        "full_name": "Lake Louise, Alberta, Canada",
        "place_type": "destination",
        "population": 1000,
        "latitude": 51.4254,
        "longitude": -116.1773,
    },
    {
        "name": "Cappadocia",
        "name_ascii": "Cappadocia",
        "region": "Central Anatolia",
        "country": "Turkey",
        "country_code": "TR",
        "full_name": "Cappadocia, Turkey",
        "place_type": "destination",
        "population": 25000,
        "latitude": 38.6431,
        "longitude": 34.8289,
    },
    {
        "name": "Giethoorn",
        "name_ascii": "Giethoorn",
        "region": "Overijssel",
        "country": "Netherlands",
        "country_code": "NL",
        "full_name": "Giethoorn, Overijssel, Netherlands",
        "place_type": "destination",
        "population": 2600,
        "latitude": 52.7397,
        "longitude": 6.0772,
    },
    {
        "name": "Mont Saint-Michel",
        "name_ascii": "Mont Saint-Michel",
        "region": "Normandy",
        "country": "France",
        "country_code": "FR",
        "full_name": "Mont Saint-Michel, Normandy, France",
        "place_type": "destination",
        "population": 30,
        "latitude": 48.6360,
        "longitude": -1.5115,
    },
    {
        "name": "Sintra",
        "name_ascii": "Sintra",
        "region": "Lisbon",
        "country": "Portugal",
        "country_code": "PT",
        "full_name": "Sintra, Lisbon, Portugal",
        "place_type": "destination",
        "population": 29500,
        "latitude": 38.8029,
        "longitude": -9.3817,
    },
]


def download_url(url: str, description: str, timeout: int = 40) -> bytes:
    print(f"Downloading {description} from {url}...")
    headers = {"User-Agent": "TripGenie-AI-Gazetteer-Builder/1.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def build_places_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    print("=" * 60)
    print("Building TripGenie-AI Worldwide Gazetteer Database")
    print("Source: GeoNames (Creative Commons Attribution 4.0)")
    print("=" * 60)

    # 1. Fetch countryInfo.txt
    country_bytes = download_url(f"{GEONAMES_BASE}/countryInfo.txt", "countryInfo.txt")
    countries = {}
    country_rows = []

    for line in country_bytes.decode("utf-8", errors="replace").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) > 4:
            iso2 = parts[0].strip()
            name = parts[4].strip()
            countries[iso2] = name
            capital = parts[5].strip() if len(parts) > 5 else ""
            country_rows.append((
                name,
                name,
                capital,
                name,
                iso2,
                name,
                "country",
                0,
                0.0,
                0.0,
                "PCLI"
            ))

    print(f"Loaded {len(country_rows)} countries and territories.")

    # 2. Fetch admin1CodesASCII.txt (states/provinces)
    admin_bytes = download_url(f"{GEONAMES_BASE}/admin1CodesASCII.txt", "admin1CodesASCII.txt")
    admins = {}
    admin_rows = []

    for line in admin_bytes.decode("utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            code_key = parts[0].strip() # e.g. "US.TX"
            adm_name = parts[1].strip() # e.g. "Texas"
            adm_ascii = parts[2].strip()
            admins[code_key] = adm_name

            cc = code_key.split(".")[0] if "." in code_key else ""
            c_name = countries.get(cc, cc)
            full = f"{adm_name}, {c_name}" if c_name else adm_name
            admin_rows.append((
                adm_name,
                adm_ascii,
                "",
                c_name,
                cc,
                full,
                "region",
                0,
                0.0,
                0.0,
                "ADM1"
            ))

    print(f"Loaded {len(admin_rows)} administrative regions/states.")

    # 3. Fetch cities5000.zip (all cities >= 5,000 population and all capitals)
    cities_zip_bytes = download_url(f"{GEONAMES_BASE}/cities5000.zip", "cities5000.zip", timeout=60)
    city_rows = []

    with zipfile.ZipFile(io.BytesIO(cities_zip_bytes)) as zf:
        with zf.open("cities5000.txt") as cf:
            for raw_line in cf:
                line = raw_line.decode("utf-8", errors="replace")
                parts = line.split("\t")
                if len(parts) < 15:
                    continue

                name = parts[1].strip()
                ascii_name = parts[2].strip()
                feature_code = parts[7].strip()

                # Exclude PPLX (suburbs/arrondissements like "Paris 15") to keep results clean and distinctive
                if feature_code == "PPLX":
                    continue

                cc = parts[8].strip()
                c_name = countries.get(cc, cc)
                admin_code = f"{cc}.{parts[10].strip()}"
                adm_name = admins.get(admin_code, "")

                # Construct clean, disambiguated full name
                if adm_name and adm_name.lower() != name.lower():
                    full = f"{name}, {adm_name}, {c_name}"
                else:
                    full = f"{name}, {c_name}"

                try:
                    pop = int(parts[14].strip())
                except ValueError:
                    pop = 0
                try:
                    lat = float(parts[4].strip())
                except ValueError:
                    lat = 0.0
                try:
                    lon = float(parts[5].strip())
                except ValueError:
                    lon = 0.0

                city_rows.append((
                    name,
                    ascii_name,
                    adm_name,
                    c_name,
                    cc,
                    full,
                    "city",
                    pop,
                    lat,
                    lon,
                    feature_code
                ))

    print(f"Loaded {len(city_rows)} cities worldwide (pop >= 5,000, excluding suburban sections).")

    # 4. Supplementary destinations
    supp_rows = []
    for s in SUPPLEMENTARY_DESTINATIONS:
        supp_rows.append((
            s["name"],
            s["name_ascii"],
            s["region"],
            s["country"],
            s["country_code"],
            s["full_name"],
            s["place_type"],
            s["population"],
            s["latitude"],
            s["longitude"],
            "TOURIST"
        ))

    print(f"Loaded {len(supp_rows)} supplementary travel destinations.")

    # 5. Populate SQLite
    temp_db_path = DB_PATH.with_suffix(".tmp")
    if temp_db_path.exists():
        temp_db_path.unlink()

    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE places (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ascii TEXT NOT NULL,
        region TEXT DEFAULT '',
        country TEXT NOT NULL,
        country_code TEXT NOT NULL,
        full_name TEXT NOT NULL,
        place_type TEXT NOT NULL,
        population INTEGER DEFAULT 0,
        latitude REAL DEFAULT 0.0,
        longitude REAL DEFAULT 0.0,
        feature_code TEXT DEFAULT ''
    );
    """)

    cur.execute("CREATE INDEX idx_places_name_ascii ON places(name_ascii COLLATE NOCASE);")
    cur.execute("CREATE INDEX idx_places_country ON places(country COLLATE NOCASE);")
    cur.execute("CREATE INDEX idx_places_region ON places(region COLLATE NOCASE);")
    cur.execute("CREATE INDEX idx_places_full_name ON places(full_name COLLATE NOCASE);")
    cur.execute("CREATE INDEX idx_places_pop ON places(population DESC);")

    insert_sql = """
    INSERT INTO places (
        name, name_ascii, region, country, country_code,
        full_name, place_type, population, latitude, longitude, feature_code
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    print("Writing records to SQLite...")
    cur.executemany(insert_sql, country_rows)
    cur.executemany(insert_sql, admin_rows)
    cur.executemany(insert_sql, city_rows)
    cur.executemany(insert_sql, supp_rows)

    conn.commit()
    conn.close()

    # Atomically replace DB file
    if DB_PATH.exists():
        DB_PATH.unlink()
    temp_db_path.rename(DB_PATH)

    total_time = time.time() - start_time
    file_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print("=" * 60)
    print(f"Successfully generated {DB_PATH.name} in {total_time:.2f}s")
    print(f"Total database size: {file_size_mb:.2f} MB")
    print(f"Total records: {len(country_rows) + len(admin_rows) + len(city_rows) + len(supp_rows):,}")
    print("=" * 60)


if __name__ == "__main__":
    build_places_database()
