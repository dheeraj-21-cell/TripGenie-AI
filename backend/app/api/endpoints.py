import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Header
from ..models.schemas import (
    TripRequest,
    TripResponse,
    DayPlan,
    RegenerateDayRequest,
    TripSaveRequest,
    TripRecord,
    TripListResponse,
    DestinationSearchResponse
)
from ..services.groq_service import generate_ai_itinerary, regenerate_ai_day
from ..services.places_service import search_destinations
from ..db.storage import db_storage
from ..core.config import settings

logger = logging.getLogger("tripgenie.api")
router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
def health_check():
    """
    Health check endpoint to verify backend operational readiness.
    Provides current service status and indicates whether Groq AI and Supabase are configured.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "groq_configured": settings.is_groq_available,
        "mode": "live_ai" if settings.is_groq_available else "mock_preview",
        "storage": db_storage.active_storage,
        "supabase_configured": settings.is_supabase_available
    }

@router.post(
    "/itinerary/generate",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
    tags=["Itinerary"]
)
def generate_itinerary(request: TripRequest):
    """
    Generate a personalized travel itinerary based on user preferences.
    Accepts ANY custom destination worldwide (e.g. Manali, Goa, Bali, Tokyo, Paris, etc.).

    If GROQ_API_KEY is configured, this queries Groq Cloud (LLaMA 3.3 70B) in strict JSON mode.
    If GROQ_API_KEY is missing or fails, it gracefully falls back to a structured mock preview.
    """
    try:
        logger.info(
            f"Received itinerary request for destination='{request.destination}' "
            f"duration={request.durationDays}d budget={request.budget} "
            f"travelers={request.travelersCount} lang={request.language}"
        )
        response = generate_ai_itinerary(request)
        return response
    except Exception as exc:
        logger.error(f"Error generating itinerary: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate travel itinerary: {str(exc)}"
        )

@router.post(
    "/itinerary/regenerate-day",
    response_model=DayPlan,
    status_code=status.HTTP_200_OK,
    tags=["Itinerary"]
)
def regenerate_day(request: RegenerateDayRequest):
    """
    Regenerate a specific single day's plan with alternative recommendations.
    Accepts optional custom user instructions without recalculating the entire trip.
    """
    try:
        logger.info(f"Regenerating Day {request.day_number} for destination='{request.destination}'")
        return regenerate_ai_day(request)
    except Exception as exc:
        logger.error(f"Error regenerating day: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate day {request.day_number}: {str(exc)}"
        )

# =========================================================================
# TRIP PERSISTENCE ENDPOINTS (Zero-cost local SQLite storage)
# =========================================================================

@router.post(
    "/trips",
    response_model=TripRecord,
    status_code=status.HTTP_201_CREATED,
    tags=["Trips"]
)
def save_trip(request: TripSaveRequest):
    """Save an itinerary to the local SQLite database."""
    try:
        record = db_storage.save_trip(request.trip, user_id=request.user_id or "local-guest")
        logger.info(f"Successfully saved trip id='{record.id}' destination='{record.destination}'")
        return record
    except Exception as exc:
        logger.error(f"Failed to save trip: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save trip: {str(exc)}"
        )

@router.get(
    "/trips",
    response_model=TripListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Trips"]
)
def list_trips(
    user_id: Optional[str] = Query("local-guest", description="User ID for listing itineraries"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="User ID header")
):
    """List all saved itineraries for the active user."""
    try:
        active_user = (x_user_id if isinstance(x_user_id, str) else None) or (user_id if isinstance(user_id, str) else None) or "local-guest"
        trips = db_storage.list_trips(user_id=active_user)
        return TripListResponse(trips=trips, total=len(trips))
    except Exception as exc:
        logger.error(f"Failed to list trips: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list saved trips: {str(exc)}"
        )

@router.get(
    "/trips/{trip_id}",
    response_model=TripRecord,
    status_code=status.HTTP_200_OK,
    tags=["Trips"]
)
def get_trip(
    trip_id: str,
    user_id: Optional[str] = Query(None, description="Optional user ID for ownership validation"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional user ID header")
):
    """
    Retrieve a specific saved itinerary by its ID.
    Enforces user isolation if user_id or X-User-Id is provided.
    """
    active_user = (x_user_id if isinstance(x_user_id, str) else None) or (user_id if isinstance(user_id, str) else None)
    if active_user:
        existing = db_storage.get_trip(trip_id)
        if existing and existing.user_id != active_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: cannot view trip owned by another user"
            )
    record = db_storage.get_trip(trip_id, user_id=active_user)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return record

@router.put(
    "/trips/{trip_id}",
    response_model=TripRecord,
    status_code=status.HTTP_200_OK,
    tags=["Trips"]
)
def update_trip(
    trip_id: str,
    request: TripResponse,
    user_id: Optional[str] = Query(None, description="Optional user ID for ownership validation"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional user ID header")
):
    """
    Update an existing saved trip with edited activities or parameters.
    Enforces user isolation if user_id or X-User-Id is provided.
    """
    active_user = (x_user_id if isinstance(x_user_id, str) else None) or (user_id if isinstance(user_id, str) else None)
    if active_user:
        existing = db_storage.get_trip(trip_id)
        if existing and existing.user_id != active_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: cannot modify trip owned by another user"
            )
    record = db_storage.update_trip(trip_id, request, user_id=active_user)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return record

@router.delete(
    "/trips/{trip_id}",
    status_code=status.HTTP_200_OK,
    tags=["Trips"]
)
def delete_trip(
    trip_id: str,
    user_id: Optional[str] = Query(None, description="Optional user ID for ownership validation"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id", description="Optional user ID header")
):
    """
    Delete a saved itinerary.
    Enforces user isolation if user_id or X-User-Id is provided.
    """
    active_user = (x_user_id if isinstance(x_user_id, str) else None) or (user_id if isinstance(user_id, str) else None)
    if active_user:
        existing = db_storage.get_trip(trip_id)
        if existing and existing.user_id != active_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: cannot delete trip owned by another user"
            )
    success = db_storage.delete_trip(trip_id, user_id=active_user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return {"status": "deleted", "id": trip_id}


# =========================================================================
# DESTINATION AUTOCOMPLETE ENDPOINT (Worldwide Free GeoNames Gazetteer)
# =========================================================================

@router.get(
    "/destinations/search",
    response_model=DestinationSearchResponse,
    status_code=status.HTTP_200_OK,
    tags=["Destinations"]
)
def search_destinations_endpoint(q: str = "", limit: int = 8):
    """
    Search worldwide destinations across all countries, states/regions, and cities.
    Powered by a free, local GeoNames gazetteer database (CC BY 4.0).
    Zero external API calls, zero cost, sub-5ms query times.
    """
    cleaned_q = (q or "").strip()
    limit = max(1, min(limit, 20))
    if not cleaned_q:
        return DestinationSearchResponse(query="", total=0, results=[])

    results = search_destinations(cleaned_q, limit=limit)
    return DestinationSearchResponse(
        query=cleaned_q,
        total=len(results),
        results=results
    )
