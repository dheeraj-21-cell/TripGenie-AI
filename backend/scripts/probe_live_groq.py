import urllib.request
import json
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

payload = {
    "destination": "Jaipur, Rajasthan, India",
    "startDate": "2026-11-15",
    "endDate": "2026-11-17",
    "durationDays": 3,
    "budget": "moderate",
    "travelerType": "couple",
    "travelersCount": 2,
    "interests": ["history", "culture", "culinary"],
    "pace": "balanced",
    "language": "en"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/itinerary/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Dispatching request to http://127.0.0.1:8000/api/itinerary/generate ...")
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=60) as res:
        elapsed = time.time() - t0
        data = json.loads(res.read().decode("utf-8"))
        print(f"HTTP_STATUS: {res.status}")
        print(f"ELAPSED_SEC: {elapsed:.2f}")
        print(f"SOURCE: {data.get('source')}")
        print(f"IS_MOCK: {data.get('is_mock')}")
        print(f"DESTINATION: {data.get('destination')}")
        print(f"DURATION_DAYS: {data.get('duration_days')}")
        print(f"BUDGET_TIER: {data.get('budget_tier')}")
        print(f"TOTAL_COST: {data.get('estimated_total_cost')}")
        print(f"SUMMARY: {data.get('summary')}")
        print(f"DAYS_COUNT: {len(data.get('days', []))}")
        for day in data.get("days", []):
            print(f"  Day {day.get('day_number')}: {day.get('theme')}")
            for act in day.get("activities", []):
                print(f"    [{act.get('time_of_day')}] {act.get('title')} ({act.get('attraction')} | {act.get('food_option')}) - {act.get('estimated_cost')}")
        print(f"ACCOMMODATIONS: {data.get('accommodation_suggestions')}")
        print(f"TRAVEL_TIPS_COUNT: {len(data.get('travel_tips', []))}")
        print(f"TRANSPORT_COUNT: {len(data.get('transport_suggestions', []))}")
        print(f"DISCLAIMER: {data.get('disclaimer')}")
except Exception as e:
    print(f"ERROR: {type(e).__name__} - {e}")
    sys.exit(1)
