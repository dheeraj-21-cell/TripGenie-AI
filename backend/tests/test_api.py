import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.endpoints import (
    health_check,
    generate_itinerary,
    regenerate_day,
    save_trip,
    list_trips,
    get_trip,
    update_trip,
    delete_trip,
    search_destinations_endpoint
)
from app.db.storage import db_storage, SupabaseStorageEngine, SQLiteStorageEngine, DatabaseStorage
from app.core.config import settings
from app.models.schemas import (
    TripRequest,
    TripResponse,
    DayPlan,
    RegenerateDayRequest,
    TripSaveRequest,
    TripRecord,
    TripListResponse,
    DestinationSearchResponse
)

SAMPLE_AI_JSON = {
    "destination": "Kyoto",
    "summary": "An enchanting 3-day exploration of ancient temples, tranquil bamboo groves, and exquisite culinary heritage in Kyoto.",
    "duration_days": 3,
    "budget_tier": "moderate",
    "currency": "USD",
    "estimated_total_cost": "$750 USD (total for 2 travelers)",
    "budget_breakdown": {
        "accommodation": "$120 - $180 per night",
        "food_and_dining": "$60 - $90 per day",
        "activities_and_entry": "$30 - $50 per day",
        "local_transport": "$15 - $25 per day"
    },
    "travel_tips": [
        "Purchase an ICOCA card for seamless metro and bus transit.",
        "Respect quiet zones in traditional Gion streets."
    ],
    "transport_suggestions": [
        "Kyoto City Bus Pass is economical for temple hopping."
    ],
    "accommodation_suggestions": [
        "Hotel Gracery Kyoto Sanjo (Central boutique hotel near subway)",
        "Ryokan Gion Sano (Traditional Japanese inn with tatami rooms)"
    ],
    "disclaimer": "Prices, opening hours, and transport schedules are estimates based on standard regional rates and may vary seasonally. Real-time availability must be verified directly with providers. Live bookings are not confirmed.",
    "days": [
        {
            "day_number": 1,
            "theme": "Historic Shrines and Gion Atmosphere",
            "activities": [
                {
                    "time_of_day": "Morning",
                    "title": "Fushimi Inari Taisha Torii Gates",
                    "description": "Walk through thousands of vibrant vermilion torii gates winding up sacred Mount Inari.",
                    "photo_query": "Fushimi Inari Kyoto torii gates morning",
                    "estimated_cost": "Free admission",
                    "location": "Fushimi Ward",
                    "attraction": "Fushimi Inari Shrine",
                    "food_option": "Inari sushi at the shrine approach"
                },
                {
                    "time_of_day": "Afternoon",
                    "title": "Kiyomizu-dera Temple and Historic Lanes",
                    "description": "Visit the iconic wooden stage overlooking Kyoto.",
                    "photo_query": "Kiyomizudera wooden stage Kyoto",
                    "estimated_cost": "$4 entry per person",
                    "location": "Higashiyama District",
                    "attraction": "Kiyomizu-dera",
                    "food_option": "Matcha parfait at a traditional teahouse"
                },
                {
                    "time_of_day": "Evening",
                    "title": "Gion Lantern Walk & Kaiseki Dining",
                    "description": "Stroll the preserved stone-paved streets of Shirakawa canal in Gion.",
                    "photo_query": "Gion lantern alley Kyoto evening",
                    "estimated_cost": "$45 per person",
                    "location": "Gion District",
                    "attraction": "Shirakawa Canal",
                    "food_option": "Seasonal multi-course Kyoto Kaiseki banquet"
                }
            ]
        }
    ]
}

@pytest.fixture(autouse=True)
def hermetic_test_environment():
    """
    Ensure automated tests never make external network calls or mutate live cloud databases.
    Individual tests that test Supabase integration use explicit inner patches.
    """
    with patch.object(type(settings), "is_supabase_available", new_callable=PropertyMock, return_value=False):
        yield

def test_health_endpoint():
    """Verify health check returns service information and healthy status."""
    data = health_check()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data
    assert data["storage"] == "local_sqlite_free"
    assert data["supabase_configured"] is False

def test_itinerary_fallback_when_no_groq_key():
    """Verify that if no Groq client is returned, fallback mock itinerary is returned."""
    with patch("app.services.groq_service.get_groq_client", return_value=None):
        payload = TripRequest(
            destination="Goa",
            startDate="2026-11-01",
            endDate="2026-11-04",
            durationDays=3,
            budget="moderate",
            travelerType="friends",
            travelersCount=3,
            interests=["beaches", "nightlife"],
            pace="relaxed",
            language="en"
        )
        data = generate_itinerary(payload)
        assert data.destination == "Goa"
        assert data.duration_days == 3
        assert data.is_mock is True
        assert data.source == "mock_generator"
        assert len(data.days) == 3
        assert data.budget_breakdown is not None
        assert len(data.travel_tips) > 0
        assert len(data.accommodation_suggestions) > 0
        assert data.disclaimer is not None

def test_multilingual_mock_generation():
    """Verify mock generator generates properly in Hindi, Spanish, and French."""
    for lang in ["hi", "es", "fr"]:
        payload = TripRequest(
            destination="Manali",
            startDate="2026-06-01",
            endDate="2026-06-03",
            durationDays=2,
            budget="moderate",
            travelerType="couple",
            travelersCount=2,
            interests=["nature"],
            pace="balanced",
            language=lang
        )
        data = generate_itinerary(payload)
        assert data.language == lang
        assert len(data.days) == 2
        day1_theme = data.days[0].theme
        if lang == "hi":
            assert "दिन" in day1_theme
        elif lang == "es":
            assert "Día" in day1_theme
        elif lang == "fr":
            assert "Jour" in day1_theme

def test_regenerate_day_mock():
    """Verify single-day regeneration generates alternative recommendations."""
    payload = RegenerateDayRequest(
        destination="Bali",
        day_number=2,
        current_theme="Beach Day",
        interests=["nature", "culinary"],
        budget="moderate",
        travelerType="couple",
        pace="balanced",
        language="en",
        custom_instruction="more cultural temple visits and street food"
    )
    day_data = regenerate_day(payload)
    assert day_data.day_number == 2
    assert len(day_data.activities) == 3
    assert "Bali" in day_data.activities[0].description

def test_trips_crud_sqlite():
    """Verify saving, listing, getting, and deleting trips via local SQLite database."""
    # 1. Create a trip
    generate_payload = TripRequest(
        destination="Zurich",
        startDate="2026-09-01",
        endDate="2026-09-04",
        durationDays=3,
        budget="luxury",
        travelerType="solo",
        travelersCount=1,
        interests=["culture", "culinary"],
        pace="relaxed",
        language="en"
    )
    trip_data = generate_itinerary(generate_payload)

    # 2. Save trip
    saved_record = save_trip(TripSaveRequest(trip=trip_data, user_id="test-user"))
    trip_id = saved_record.id
    assert saved_record.destination == "Zurich"
    assert saved_record.user_id == "test-user"

    # 3. List trips
    list_data = list_trips(user_id="test-user")
    assert list_data.total >= 1
    assert any(t.id == trip_id for t in list_data.trips)

    # 4. Get specific trip
    fetched = get_trip(trip_id)
    assert fetched.id == trip_id

    # 5. Delete trip
    del_res = delete_trip(trip_id)
    assert del_res["status"] == "deleted"

    # 6. Verify 404 after deletion
    with pytest.raises(HTTPException) as exc_info:
        get_trip(trip_id)
    assert exc_info.value.status_code == 404

def test_update_trip_sqlite():
    """Verify updating an existing saved trip with edited activities."""
    # 1. Generate & Save
    gen_payload = TripRequest(
        destination="Vienna",
        startDate="2026-10-01",
        endDate="2026-10-03",
        durationDays=2,
        budget="moderate",
        travelerType="solo",
        travelersCount=1,
        interests=["culture", "history"],
        pace="balanced",
        language="en"
    )
    trip_data = generate_itinerary(gen_payload)
    save_resp = save_trip(TripSaveRequest(trip=trip_data, user_id="editor-user"))
    trip_id = save_resp.id

    # 2. Modify an activity and summary
    trip_data.days[0].activities[0].title = "Custom Coffeehouse Morning in Vienna"
    trip_data.summary = "Updated custom summary."

    # 3. Update via PUT
    updated = update_trip(trip_id, trip_data)
    assert updated.itinerary_data.days[0].activities[0].title == "Custom Coffeehouse Morning in Vienna"
    assert updated.itinerary_data.summary == "Updated custom summary."

    # 4. Clean up
    delete_trip(trip_id)

def test_trip_not_found_handling():
    """Verify 404 responses for non-existent trip IDs."""
    fake_id = "non-existent-uuid-12345"
    with pytest.raises(HTTPException) as exc1:
        get_trip(fake_id)
    assert exc1.value.status_code == 404

    with pytest.raises(HTTPException) as exc2:
        delete_trip(fake_id)
    assert exc2.value.status_code == 404

def test_itinerary_generation_with_mocked_groq_ai():
    """Verify Groq AI inference flow using mocked Groq client (0 tokens consumed)."""
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(SAMPLE_AI_JSON)
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.return_value = mock_completion

    with patch("app.services.groq_service.get_groq_client", return_value=mock_groq_client):
        payload = TripRequest(
            destination="Kyoto",
            startDate="2026-05-10",
            endDate="2026-05-13",
            durationDays=3,
            budget="moderate",
            travelerType="couple",
            travelersCount=2,
            interests=["culture", "photography", "food"],
            pace="balanced",
            language="en"
        )

        data = generate_itinerary(payload)
        assert data.is_mock is False
        assert data.source == "groq_ai"
        assert data.destination == "Kyoto"
        assert len(data.accommodation_suggestions) > 0
        assert data.disclaimer is not None
        assert "estimates" in data.disclaimer.lower()

def test_groq_rate_limit_fallback_resilience():
    """Verify rate-limited Groq API calls fallback gracefully to mock generator with informative notice."""
    from groq import RateLimitError
    res_mock = MagicMock()
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded: 6000 TPM", response=res_mock, body=None)

    with patch("app.services.groq_service.get_groq_client", return_value=mock_groq_client):
        payload = TripRequest(
            destination="Tokyo",
            startDate="2026-07-01",
            endDate="2026-07-04",
            durationDays=3,
            budget="luxury",
            travelerType="solo",
            travelersCount=1,
            interests=["shopping", "culinary"],
            pace="packed",
            language="en"
        )
        data = generate_itinerary(payload)
        assert data.is_mock is True
        assert data.destination == "Tokyo"
        assert "[AI RATE LIMITED" in data.summary
        assert len(data.accommodation_suggestions) > 0
        assert data.disclaimer is not None

def test_groq_auth_error_fallback_resilience():
    """Verify invalid API key falls back gracefully without crashing."""
    from groq import AuthenticationError
    res_mock = MagicMock()
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.side_effect = AuthenticationError("Invalid API Key", response=res_mock, body=None)

    with patch("app.services.groq_service.get_groq_client", return_value=mock_groq_client):
        payload = TripRequest(
            destination="Paris",
            startDate="2026-08-01",
            endDate="2026-08-03",
            durationDays=2,
            budget="moderate",
            travelerType="couple",
            travelersCount=2,
            interests=["art"],
            pace="relaxed",
            language="en"
        )
        data = generate_itinerary(payload)
        assert data.is_mock is True
        assert "[AI AUTHENTICATION ERROR" in data.summary
        assert len(data.accommodation_suggestions) > 0

def test_groq_malformed_json_fallback_resilience():
    """Verify that if Groq returns non-JSON or partial text, parse recovery recovers cleanly."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Here is your itinerary: { broken json ... oops"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions.create.return_value = mock_completion

    with patch("app.services.groq_service.get_groq_client", return_value=mock_groq_client):
        payload = TripRequest(
            destination="Rome",
            startDate="2026-09-01",
            endDate="2026-09-04",
            durationDays=3,
            budget="moderate",
            travelerType="friends",
            travelersCount=3,
            interests=["history"],
            pace="balanced",
            language="en"
        )
        data = generate_itinerary(payload)
        assert data.is_mock is True
        assert "[AI PARSE RECOVERY]" in data.summary
        assert len(data.accommodation_suggestions) > 0

def test_regenerate_day_with_mocked_groq_ai():
    """Verify single-day regeneration when Groq AI is mocked."""
    sample_day = {
        "day_number": 2,
        "theme": "Regenerated Classical Music & Palaces",
        "activities": [
            {
                "time_of_day": "Morning",
                "title": "Schonbrunn Palace Gardens",
                "description": "Walk through imperial palace gardens and the Gloriette.",
                "photo_query": "Schonbrunn Palace Vienna morning",
                "estimated_cost": "$20 per person",
                "location": "Hietzing",
                "attraction": "Schonbrunn Palace",
                "food_option": "Apfelstrudel at Cafe Residenz"
            },
            {
                "time_of_day": "Afternoon",
                "title": "State Opera House Tour",
                "description": "Guided architectural tour of the Vienna State Opera.",
                "photo_query": "Vienna State Opera interior",
                "estimated_cost": "$15 per person",
                "location": "Innere Stadt",
                "attraction": "Vienna State Opera",
                "food_option": "Wiener Schnitzel lunch"
            },
            {
                "time_of_day": "Evening",
                "title": "Mozart & Strauss Concert",
                "description": "Evening classical chamber concert in a historic hall.",
                "photo_query": "Vienna concert hall evening",
                "estimated_cost": "$55 per person",
                "location": "Musikverein",
                "attraction": "Golden Hall",
                "food_option": "Tafelspitz dinner"
            }
        ]
    }

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(sample_day)
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value = mock_completion

    with patch("app.services.groq_service.get_groq_client", return_value=mock_groq):
        payload = RegenerateDayRequest(
            destination="Vienna",
            day_number=2,
            current_theme="Old Theme",
            interests=["music", "history"],
            budget="moderate",
            travelerType="solo",
            pace="balanced",
            language="en"
        )
        data = regenerate_day(payload)
        assert data.day_number == 2
        assert data.theme == "Regenerated Classical Music & Palaces"
        assert len(data.activities) == 3

def test_validation_error_on_invalid_input():
    """Verify invalid payloads are caught by Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        TripRequest(
            destination="",
            startDate="2026-06-01",
            endDate="2026-06-05",
            durationDays=0
        )


# =========================================================================
# WORLDWIDE DESTINATION AUTOCOMPLETE TESTS
# =========================================================================

def test_destination_search_country():
    """Verify searching a country returns the country entity prominently."""
    res = search_destinations_endpoint(q="Iceland", limit=5)
    assert isinstance(res, DestinationSearchResponse)
    assert res.total > 0
    top = res.results[0]
    assert top.name == "Iceland"
    assert top.place_type == "country"
    assert top.country_code == "IS"

def test_destination_search_duplicate_names_paris():
    """Verify places sharing names (Paris, France vs Paris, Texas) are both returned and disambiguated."""
    res = search_destinations_endpoint(q="Paris", limit=5)
    assert res.total >= 2
    full_names = [r.full_name for r in res.results]
    # France and Texas should both be represented
    assert any("France" in fn for fn in full_names)
    assert any("Texas" in fn or "United States" in fn for fn in full_names)
    # The primary world metropolis should be first
    assert res.results[0].country == "France"

def test_destination_search_cambridge():
    """Verify Cambridge UK and Cambridge USA are clearly distinguished by region/country."""
    res = search_destinations_endpoint(q="Cambridge", limit=5)
    assert res.total >= 2
    countries = {r.country for r in res.results}
    assert "United Kingdom" in countries
    assert "United States" in countries

def test_destination_search_towns():
    """Verify smaller famous tourist towns (Banff, Zermatt, Manali) are found."""
    banff = search_destinations_endpoint(q="Banff", limit=3)
    assert banff.total >= 1
    assert any("Alberta" in r.region and "Canada" in r.country for r in banff.results)

    manali = search_destinations_endpoint(q="Manali", limit=3)
    assert manali.total >= 1
    assert any("India" in r.country for r in manali.results)

    zermatt = search_destinations_endpoint(q="Zermatt", limit=3)
    assert zermatt.total >= 1
    assert any("Switzerland" in r.country for r in zermatt.results)

def test_destination_search_empty():
    """Verify empty or whitespace query returns 0 results cleanly without errors."""
    res = search_destinations_endpoint(q="   ", limit=5)
    assert res.total == 0
    assert len(res.results) == 0

def test_manual_destination_entry_allowed():
    """Verify manual entry of any obscure or custom place succeeds end-to-end without requiring autocomplete."""
    custom_dest = "Little Uncharted Valley 99"
    payload = TripRequest(
        destination=custom_dest,
        startDate="2026-09-01",
        endDate="2026-09-03",
        durationDays=3,
        budget="moderate",
        travelerType="solo",
        travelersCount=1,
        interests=["nature"],
        pace="balanced",
        language="en"
    )
    with patch("app.services.groq_service.get_groq_client", return_value=None):
        result = generate_itinerary(payload)
        assert result.destination == custom_dest
        assert result.duration_days == 3
        assert len(result.days) == 3


# =========================================================================
# SUPABASE CLOUD & HYBRID STORAGE TESTS (MOCKED - 100% Free / ₹0 Spending)
# =========================================================================

def test_health_endpoint_with_supabase_configured():
    """Verify health check reflects Supabase Cloud active when configured."""
    with patch.object(type(settings), "is_supabase_available", new_callable=PropertyMock, return_value=True):
        data = health_check()
        assert data["storage"] == "supabase_cloud"
        assert data["supabase_configured"] is True

def test_supabase_storage_engine_crud_mocked():
    """Verify SupabaseStorageEngine save, get, list, update, delete with mocked Supabase client."""
    mock_client = MagicMock()
    engine = SupabaseStorageEngine(client=mock_client)

    sample_trip = TripResponse(
        destination="Rome",
        summary="A cultural journey through ancient Rome.",
        duration_days=2,
        days=[]
    )

    # 1. Test save_trip (upsert)
    mock_upsert = MagicMock()
    mock_client.table.return_value.upsert.return_value = mock_upsert
    mock_upsert.execute.return_value = MagicMock(data=[])

    record = engine.save_trip(sample_trip, user_id="guest-123")
    assert record.destination == "Rome"
    assert record.user_id == "guest-123"
    mock_client.table.assert_called_with("trips")
    mock_client.table().upsert.assert_called_once()

    # 2. Test get_trip
    mock_select = MagicMock()
    mock_client.table.return_value.select.return_value = mock_select
    mock_select.eq.return_value = mock_select
    mock_select.execute.return_value = MagicMock(data=[{
        "id": record.id,
        "user_id": "guest-123",
        "destination": "Rome",
        "duration_days": 2,
        "created_at": record.created_at,
        "itinerary_data": sample_trip.model_dump(mode="json")
    }])

    fetched = engine.get_trip(record.id)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.destination == "Rome"

    # 3. Test list_trips
    mock_order = MagicMock()
    mock_select.order.return_value = mock_order
    mock_order.execute.return_value = MagicMock(data=[{
        "id": record.id,
        "user_id": "guest-123",
        "destination": "Rome",
        "duration_days": 2,
        "created_at": record.created_at,
        "itinerary_data": sample_trip.model_dump(mode="json")
    }])

    trips = engine.list_trips(user_id="guest-123")
    assert len(trips) == 1
    assert trips[0].destination == "Rome"

    # 4. Test update_trip
    mock_update = MagicMock()
    mock_client.table.return_value.update.return_value = mock_update
    mock_update.eq.return_value = mock_update
    mock_update.execute.return_value = MagicMock(data=[])

    sample_trip.summary = "Updated Rome summary"
    updated = engine.update_trip(record.id, sample_trip)
    assert updated is not None
    assert updated.itinerary_data.summary == "Updated Rome summary"

    # 5. Test delete_trip
    mock_delete = MagicMock()
    mock_client.table.return_value.delete.return_value = mock_delete
    mock_delete.eq.return_value = mock_delete
    mock_delete.execute.return_value = MagicMock(data=[])

    deleted = engine.delete_trip(record.id)
    assert deleted is True

def test_database_storage_automatic_fallback_on_supabase_error():
    """
    CRITICAL RESILIENCE TEST:
    Verify that if Supabase throws an exception (network outage, schema mismatch, timeout),
    DatabaseStorage catches it safely and falls back to local SQLite without raising an error.
    """
    sample_trip = TripResponse(
        destination="Florence",
        summary="Artistic renaissance tour.",
        duration_days=2,
        days=[]
    )

    with patch.object(type(settings), "is_supabase_available", new_callable=PropertyMock, return_value=True):
        # Force Supabase engine to throw an error
        with patch.object(db_storage.supabase_engine, "save_trip", side_effect=Exception("Supabase network timeout")):
            saved = db_storage.save_trip(sample_trip, user_id="fallback-user")
            assert saved.destination == "Florence"
            assert saved.id is not None
            trip_id = saved.id

            # Verify it was saved in SQLite fallback
            sqlite_record = db_storage.sqlite_engine.get_trip(trip_id)
            assert sqlite_record is not None
            assert sqlite_record.destination == "Florence"

        # Force Supabase get_trip to throw an error
        with patch.object(db_storage.supabase_engine, "get_trip", side_effect=Exception("Supabase 500 server error")):
            fetched = db_storage.get_trip(trip_id)
            assert fetched is not None
            assert fetched.id == trip_id
            assert fetched.destination == "Florence"

        # Force Supabase list_trips to throw an error
        with patch.object(db_storage.supabase_engine, "list_trips", side_effect=Exception("Supabase connection refused")):
            trip_list = db_storage.list_trips(user_id="fallback-user")
            assert any(t.id == trip_id for t in trip_list)

        # Clean up
        db_storage.sqlite_engine.delete_trip(trip_id)

def test_database_storage_fallback_when_unconfigured():
    """Verify that when Supabase is unconfigured, SQLite is used directly."""
    with patch.object(type(settings), "is_supabase_available", new_callable=PropertyMock, return_value=False):
        assert db_storage.active_storage == "local_sqlite_free"
        sample_trip = TripResponse(
            destination="Oslo",
            summary="Fjord adventure.",
            duration_days=2,
            days=[]
        )
        saved = db_storage.save_trip(sample_trip, user_id="oslo-user")
        assert saved.destination == "Oslo"
        assert db_storage.get_trip(saved.id) is not None
        db_storage.delete_trip(saved.id)


# =========================================================================
# USER ISOLATION & UNAUTHORIZED ACCESS TESTS
# =========================================================================

def test_user_isolation_cannot_view_other_user_trip():
    """Verify User B cannot view User A's private trip (returns 403 Forbidden)."""
    alice_trip = TripResponse(
        destination="Kyoto",
        summary="Alice's private Kyoto trip",
        duration_days=3,
        days=[]
    )
    saved = save_trip(TripSaveRequest(trip=alice_trip, user_id="alice"))
    trip_id = saved.id

    # Alice can view her own trip
    alice_view = get_trip(trip_id, user_id="alice")
    assert alice_view.id == trip_id
    assert alice_view.user_id == "alice"

    # Bob attempting to view Alice's trip via query parameter -> 403 Forbidden
    with pytest.raises(HTTPException) as exc1:
        get_trip(trip_id, user_id="bob")
    assert exc1.value.status_code == 403
    assert "Access denied" in exc1.value.detail

    # Bob attempting to view Alice's trip via X-User-Id header -> 403 Forbidden
    with pytest.raises(HTTPException) as exc2:
        get_trip(trip_id, x_user_id="bob")
    assert exc2.value.status_code == 403

    # Clean up
    delete_trip(trip_id, user_id="alice")

def test_user_isolation_cannot_update_other_user_trip():
    """Verify User B cannot modify User A's private trip (returns 403 Forbidden)."""
    alice_trip = TripResponse(
        destination="Paris",
        summary="Alice's Paris trip",
        duration_days=2,
        days=[]
    )
    saved = save_trip(TripSaveRequest(trip=alice_trip, user_id="alice"))
    trip_id = saved.id

    malicious_update = TripResponse(
        destination="Hacked Paris",
        summary="Tampered by Bob",
        duration_days=2,
        days=[]
    )

    # Bob attempts to overwrite Alice's trip -> 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        update_trip(trip_id, malicious_update, user_id="bob")
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail

    # Verify Alice's trip was not modified
    intact = get_trip(trip_id, user_id="alice")
    assert intact.destination == "Paris"
    assert intact.itinerary_data.summary == "Alice's Paris trip"

    # Clean up
    delete_trip(trip_id, user_id="alice")

def test_user_isolation_cannot_delete_other_user_trip():
    """Verify User B cannot delete User A's private trip (returns 403 Forbidden)."""
    alice_trip = TripResponse(
        destination="London",
        summary="Alice's London trip",
        duration_days=3,
        days=[]
    )
    saved = save_trip(TripSaveRequest(trip=alice_trip, user_id="alice"))
    trip_id = saved.id

    # Bob attempts to delete Alice's trip -> 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        delete_trip(trip_id, user_id="bob")
    assert exc.value.status_code == 403
    assert "Access denied" in exc.value.detail

    # Verify Alice's trip still exists
    assert get_trip(trip_id, user_id="alice") is not None

    # Alice can delete her own trip
    del_res = delete_trip(trip_id, user_id="alice")
    assert del_res["status"] == "deleted"

def test_user_isolation_list_trips_strictly_segregated():
    """Verify list_trips strictly isolates trips per user without data leakage."""
    trip_x = save_trip(TripSaveRequest(trip=TripResponse(destination="Berlin", summary="X", duration_days=1, days=[]), user_id="user-x"))
    trip_y = save_trip(TripSaveRequest(trip=TripResponse(destination="Madrid", summary="Y", duration_days=1, days=[]), user_id="user-y"))

    list_x = list_trips(user_id="user-x")
    list_y = list_trips(user_id="user-y")

    # User X only sees Berlin
    x_ids = [t.id for t in list_x.trips]
    assert trip_x.id in x_ids
    assert trip_y.id not in x_ids

    # User Y only sees Madrid
    y_ids = [t.id for t in list_y.trips]
    assert trip_y.id in y_ids
    assert trip_x.id not in y_ids

    # Clean up
    delete_trip(trip_x.id, user_id="user-x")
    delete_trip(trip_y.id, user_id="user-y")

def test_supabase_storage_engine_user_isolation_mocked():
    """Verify SupabaseStorageEngine enforces user_id filtering in chained queries."""
    mock_client = MagicMock()
    engine = SupabaseStorageEngine(client=mock_client)

    # 1. get_trip with user_id filters by user_id
    mock_select = MagicMock()
    mock_client.table.return_value.select.return_value = mock_select
    mock_select.eq.return_value = mock_select
    mock_select.execute.return_value = MagicMock(data=[])

    engine.get_trip("trip-123", user_id="user-xyz")
    mock_select.eq.assert_any_call("id", "trip-123")
    mock_select.eq.assert_any_call("user_id", "user-xyz")

    # 2. update_trip with user_id filters by user_id
    mock_update = MagicMock()
    mock_client.table.return_value.update.return_value = mock_update
    mock_update.eq.return_value = mock_update
    mock_update.execute.return_value = MagicMock(data=[])
    # Setup select to return 1 existing row owned by user-xyz
    mock_select.execute.return_value = MagicMock(data=[{"id": "trip-123", "user_id": "user-xyz", "created_at": "2026-01-01T00:00:00Z"}])

    dummy_trip = TripResponse(destination="Rome", summary="Test", duration_days=1, days=[])
    engine.update_trip("trip-123", dummy_trip, user_id="user-xyz")
    mock_update.eq.assert_any_call("id", "trip-123")
    mock_update.eq.assert_any_call("user_id", "user-xyz")

    # 3. delete_trip with user_id filters by user_id
    mock_delete = MagicMock()
    mock_client.table.return_value.delete.return_value = mock_delete
    mock_delete.eq.return_value = mock_delete
    mock_delete.execute.return_value = MagicMock(data=[])

    engine.delete_trip("trip-123", user_id="user-xyz")
    mock_delete.eq.assert_any_call("id", "trip-123")
    mock_delete.eq.assert_any_call("user_id", "user-xyz")

def test_anonymous_guest_isolation_between_visitors():
    """
    CRITICAL GUEST ISOLATION TEST:
    Verify that two independent unauthenticated visitors (Visitor 1 with guest-uuid-1
    and Visitor 2 with guest-uuid-2) cannot view, modify, or delete each other's trips.
    """
    guest1_id = "guest-a1111111-2222-3333-4444-555555555555"
    guest2_id = "guest-b2222222-3333-4444-5555-666666666666"

    trip1 = save_trip(TripSaveRequest(
        trip=TripResponse(destination="Kyoto", summary="Visitor 1 Trip", duration_days=2, days=[]),
        user_id=guest1_id
    ))
    trip2 = save_trip(TripSaveRequest(
        trip=TripResponse(destination="Prague", summary="Visitor 2 Trip", duration_days=3, days=[]),
        user_id=guest2_id
    ))

    # 1. Visitor 2 cannot view Visitor 1's trip
    with pytest.raises(HTTPException) as exc_view:
        get_trip(trip1.id, user_id=guest2_id)
    assert exc_view.value.status_code == 403

    # 2. Visitor 2 cannot update Visitor 1's trip
    with pytest.raises(HTTPException) as exc_update:
        update_trip(trip1.id, TripResponse(destination="Hacked", summary="Hacked", duration_days=2, days=[]), user_id=guest2_id)
    assert exc_update.value.status_code == 403

    # 3. Visitor 2 cannot delete Visitor 1's trip
    with pytest.raises(HTTPException) as exc_delete:
        delete_trip(trip1.id, user_id=guest2_id)
    assert exc_delete.value.status_code == 403

    # 4. Visitor 1's list only contains trip1; Visitor 2's list only contains trip2
    list_g1 = list_trips(user_id=guest1_id)
    list_g2 = list_trips(user_id=guest2_id)
    assert any(t.id == trip1.id for t in list_g1.trips)
    assert not any(t.id == trip2.id for t in list_g1.trips)
    assert any(t.id == trip2.id for t in list_g2.trips)
    assert not any(t.id == trip1.id for t in list_g2.trips)

    # Clean up
    delete_trip(trip1.id, user_id=guest1_id)
    delete_trip(trip2.id, user_id=guest2_id)
