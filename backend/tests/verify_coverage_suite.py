import json
import sys
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def query_search(q, limit=5):
    url = f"http://127.0.0.1:8000/api/destinations/search?q={urllib.parse.quote(q)}&limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=4) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "results": [], "total": 0}

def run_verification():
    all_passed = True
    print("=" * 65)
    print("DESTINATION GAZETTEER VERIFICATION SUITE")
    print("=" * 65)

    # -------------------------------------------------------------
    # 1. COUNTRIES ACROSS CONTINENTS
    # -------------------------------------------------------------
    print("\n--- 1. Testing Countries Across Continents ---")
    continents_countries = {
        "Asia": ["Japan", "India", "Thailand"],
        "Europe": ["France", "Iceland", "Germany", "Switzerland"],
        "Africa": ["Egypt", "South Africa", "Kenya", "Morocco"],
        "Americas": ["Canada", "Brazil", "Mexico", "Argentina"],
        "Oceania": ["Australia", "New Zealand", "Fiji"]
    }

    country_passes = 0
    country_total = 0
    for cont, countries in continents_countries.items():
        print(f"[{cont}]")
        for c in countries:
            country_total += 1
            res = query_search(c, limit=3)
            results = res.get("results", [])
            # Top match should be the country entity
            is_match = False
            top = results[0] if results else {}
            if top.get("name", "").lower() == c.lower() and top.get("place_type") == "country":
                is_match = True
            elif any(r.get("name", "").lower() == c.lower() and r.get("place_type") == "country" for r in results):
                is_match = True

            status = "PASS" if is_match else "FAIL"
            if is_match:
                country_passes += 1
            else:
                all_passed = False
            print(f"  {c:15} -> {status} (Top: {top.get('name')} | {top.get('place_type')} | {top.get('country_code')})")

    # -------------------------------------------------------------
    # 2. MAJOR CITIES & LESS-FAMOUS TOWNS
    # -------------------------------------------------------------
    print("\n--- 2. Testing Cities and Less-Famous Towns ---")
    places_to_test = {
        "India": [("New Delhi", "major"), ("Mumbai", "major"), ("Manali", "town"), ("Rishikesh", "town"), ("Darjeeling", "town")],
        "Europe": [("London", "major"), ("Rome", "major"), ("Zermatt", "town"), ("Amalfi", "town"), ("Hallstatt", "town")],
        "Asia": [("Tokyo", "major"), ("Bangkok", "major"), ("Kyoto", "major"), ("Pokhara", "town")],
        "Africa": [("Cairo", "major"), ("Nairobi", "major"), ("Cape Town", "major"), ("Arusha", "town")],
        "Americas": [("New York", "major"), ("Buenos Aires", "major"), ("Banff", "town"), ("Whistler", "town")]
    }

    places_passes = 0
    places_total = 0
    for region, places in places_to_test.items():
        print(f"[{region}]")
        for place, p_type in places:
            places_total += 1
            res = query_search(place, limit=5)
            results = res.get("results", [])
            found = any(place.lower() in r.get("name", "").lower() or place.lower() in r.get("full_name", "").lower() for r in results)
            status = "PASS" if found else "FAIL"
            if found:
                places_passes += 1
            else:
                all_passed = False
            top_desc = results[0].get("full_name") if results else "NOT FOUND"
            print(f"  [{p_type.upper():5}] {place:15} -> {status} ({top_desc})")

    # -------------------------------------------------------------
    # 3. DUPLICATE PLACE NAMES DISAMBIGUATION
    # -------------------------------------------------------------
    print("\n--- 3. Testing Duplicate Names Disambiguation ---")
    duplicates = [
        ("Paris", ["France", "United States"]),
        ("Cambridge", ["United Kingdom", "United States"]),
        ("San Jose", ["United States", "Costa Rica"]),
        ("Springfield", ["United States"]),
        ("Santiago", ["Chile", "Philippines"])
    ]

    dup_passes = 0
    for name, expected_countries in duplicates:
        res = query_search(name, limit=6)
        results = res.get("results", [])
        found_countries = {r.get("country") for r in results}
        has_all_expected = all(ec in found_countries for ec in expected_countries)
        status = "PASS" if has_all_expected and len(results) >= 2 else "FAIL"
        if status == "PASS":
            dup_passes += 1
        else:
            all_passed = False
        print(f"  {name:12} -> {status} (Locations found: {len(results)})")
        for r in results[:3]:
            print(f"     • {r.get('name')}, {r.get('region') or 'N/A'}, {r.get('country')}")

    # -------------------------------------------------------------
    # 4. UNLISTED SMALL VILLAGE / ZERO SUGGESTIONS
    # -------------------------------------------------------------
    print("\n--- 4. Testing Unlisted Remote Hamlet ---")
    unlisted_place = "Zorzor Hamlet Nowhere 99"
    res = query_search(unlisted_place, limit=5)
    zero_suggestions = (res.get("total") == 0 and len(res.get("results", [])) == 0)
    unlisted_status = "PASS" if zero_suggestions else "FAIL"
    if not zero_suggestions:
        all_passed = False
    print(f"  \"{unlisted_place}\" -> {unlisted_status} (Returned {res.get('total')} results, expected 0)")

    print("\n" + "=" * 65)
    print("VERIFICATION SUMMARY")
    print(f"  Countries:      {country_passes}/{country_total} passed")
    print(f"  Cities & Towns: {places_passes}/{places_total} passed")
    print(f"  Duplicates:     {dup_passes}/{len(duplicates)} passed")
    print(f"  Unlisted Query: {'PASS' if zero_suggestions else 'FAIL'}")
    print("=" * 65)
    print(f"FINAL RESULT: {'ALL BACKEND CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
