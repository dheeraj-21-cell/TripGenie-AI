"""
Service for searching worldwide destinations using the local SQLite gazetteer.
Source: GeoNames (Creative Commons Attribution 4.0)
License: Free, zero cost, no billing, no paid APIs.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "places.db"

# In-memory query cache for instant responses to frequent keystrokes
_CACHE: Dict[str, List[Dict[str, Any]]] = {}
_MAX_CACHE_SIZE = 500


def get_db_connection() -> Optional[sqlite3.Connection]:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_destinations(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """
    Search worldwide places by name, region, country, or composite query.
    Returns structured matches with name, region, country, full_name, and type.
    """
    cleaned = (query or "").strip()
    if not cleaned or len(cleaned) < 1:
        return []

    cache_key = f"{cleaned.lower()}:{limit}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    conn = get_db_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        prefix = f"{cleaned}%"
        contains = f"%{cleaned}%"

        # SQL ranking:
        # 1. Exact match on place name or country
        # 2. Place name starts with query
        # 3. Country starts with query
        # 4. Region starts with query
        # 5. Full name contains query
        # Secondary: (place_type == 'country') DESC, then population DESC
        sql = """
        SELECT name, region, country, country_code, full_name, place_type, population, latitude, longitude
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
           (place_type = 'destination') DESC,
           population DESC
        LIMIT ?
        """

        # Request up to limit * 2 to deduplicate slight spelling variants (e.g. Manali vs Manāli)
        fetch_limit = min(limit * 2, 40)
        rows = cur.execute(sql, (
            prefix, prefix, prefix, contains,
            cleaned, cleaned, prefix, prefix, prefix,
            fetch_limit
        )).fetchall()

        results = []
        seen_keys = set()

        for r in rows:
            name = r["name"]
            region = r["region"] or ""
            country = r["country"] or ""
            country_code = r["country_code"] or ""
            full_name = r["full_name"] or f"{name}, {country}"
            place_type = r["place_type"] or "city"
            population = r["population"] or 0
            lat = r["latitude"] or 0.0
            lon = r["longitude"] or 0.0

            # Deduplication key to prevent duplicates (e.g. ASCII vs Unicode duplicate rows)
            dedup_key = f"{name.lower().replace('ā', 'a').replace('é', 'e').replace('í', 'i')}|{region.lower()}|{country.lower()}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            results.append({
                "name": name,
                "region": region,
                "country": country,
                "country_code": country_code,
                "full_name": full_name,
                "place_type": place_type,
                "population": population,
                "latitude": lat,
                "longitude": lon,
            })

            if len(results) >= limit:
                break

        if len(_CACHE) > _MAX_CACHE_SIZE:
            _CACHE.clear()
        _CACHE[cache_key] = results

        return results
    except Exception as e:
        print(f"Error querying places database: {e}")
        return []
    finally:
        conn.close()
