import json
import logging
from typing import Optional, Dict, Any
from groq import Groq, APIConnectionError, RateLimitError, APIStatusError, AuthenticationError
from ..models.schemas import TripRequest, TripResponse, DayPlan, RegenerateDayRequest
from ..core.config import settings
from .mock_generator import generate_mock_itinerary, regenerate_mock_day

logger = logging.getLogger("tripgenie.groq")

# Officially supported free-tier models on Groq Cloud
SUPPORTED_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"

LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "es": "Spanish (Español)",
    "fr": "French (Français)"
}

def get_groq_client() -> Optional[Groq]:
    """
    Initialize Groq client safely from settings.
    Returns None if GROQ_API_KEY is not configured.
    """
    if not settings.is_groq_available:
        return None
    try:
        return Groq(api_key=settings.GROQ_API_KEY)
    except Exception as exc:
        logger.error(f"Failed to initialize Groq client: {str(exc)}")
        return None

def build_system_prompt(language_code: str) -> str:
    """Construct an engineered system prompt enforcing strict JSON structure and target language."""
    target_lang = LANGUAGE_MAP.get(language_code.lower(), "English")

    return f"""You are TripGenie AI, an elite travel consultant and cultural expert.
Your mission is to generate hyper-personalized, realistic, engaging, and practical travel itineraries.

CRITICAL INSTRUCTIONS:
1. You MUST generate the entire itinerary response strictly in {target_lang}.
2. You MUST output ONLY valid JSON. Do not include markdown code fences (no ```json, no ```), no conversational preamble, and no closing remarks.
3. Strictly follow this exact JSON structure:
{{
  "destination": "Destination Name",
  "summary": "Compelling 2-3 sentence overview highlighting the essence of the journey tailored to the traveler style.",
  "duration_days": 3,
  "budget_tier": "budget | moderate | luxury",
  "currency": "USD",
  "estimated_total_cost": "$X,XXX USD (total for all travelers)",
  "budget_breakdown": {{
    "accommodation": "$XX - $XX per night",
    "food_and_dining": "$XX - $XX per day",
    "activities_and_entry": "$XX - $XX per day",
    "local_transport": "$XX - $XX per day"
  }},
  "travel_tips": [
    "Practical local tip 1 (e.g. currency, etiquette, safety, dress code)",
    "Practical local tip 2",
    "Practical local tip 3"
  ],
  "transport_suggestions": [
    "How to get around locally (walking, metro, taxis, passes)",
    "Airport/transit arrival advice"
  ],
  "accommodation_suggestions": [
    "Recommended lodging option 1 (e.g. boutique hotel, hostel, or resort) matching budget tier",
    "Recommended lodging option 2 with neighborhood context",
    "Recommended lodging option 3"
  ],
  "disclaimer": "Prices, opening hours, and transport schedules are estimates based on standard regional rates and may vary seasonally. Real-time availability must be verified directly with providers. Live bookings are not confirmed.",
  "days": [
    {{
      "day_number": 1,
      "theme": "Captivating theme for the day",
      "activities": [
        {{
          "time_of_day": "Morning",
          "title": "Specific activity name",
          "description": "Engaging description with tips on what to see and do",
          "photo_query": "English keywords for Unsplash photo search (e.g. Manali mountain temple scenic)",
          "estimated_cost": "$XX per person",
          "location": "Neighborhood or district name",
          "attraction": "Exact landmark or spot name",
          "food_option": "Recommended local breakfast spot or dish to savor"
        }},
        {{
          "time_of_day": "Afternoon",
          "title": "Specific activity name",
          "description": "Engaging description with practical guidance",
          "photo_query": "English keywords for Unsplash photo search",
          "estimated_cost": "$XX per person",
          "location": "Neighborhood or district name",
          "attraction": "Exact landmark or spot name",
          "food_option": "Recommended lunch spot or specialty"
        }},
        {{
          "time_of_day": "Evening",
          "title": "Specific activity name",
          "description": "Evening atmosphere, sunset, or dining experience",
          "photo_query": "English keywords for Unsplash photo search",
          "estimated_cost": "$XX per person",
          "location": "Neighborhood or district name",
          "attraction": "Exact landmark or spot name",
          "food_option": "Dinner recommendation or regional delicacy"
        }}
      ]
    }}
  ]
}}

4. For photo_query, ALWAYS keep keywords in English (e.g. "Rome Colosseum sunset") so photo APIs can resolve them reliably.
5. All other text (titles, descriptions, tips, themes, food options) MUST be naturally written in {target_lang}.
6. Ensure each day has exactly 3 structured activities: Morning, Afternoon, and Evening.
7. Tailor recommendations strictly to the traveler's budget, pace, traveler count, and interests.
"""

def build_user_prompt(request: TripRequest) -> str:
    """Format the trip parameters cleanly for the AI model."""
    interests_str = ", ".join(request.interests) if request.interests else "General sightseeing, culture, nature"

    return f"""Please create a complete {request.durationDays}-day personalized itinerary with the following parameters:
- Destination: {request.destination}
- Dates: {request.startDate} to {request.endDate} ({request.durationDays} days)
- Travelers: {request.travelersCount} ({request.travelerType})
- Budget Tier: {request.budget}
- Travel Pace: {request.pace}
- Primary Interests: {interests_str}
- Language: {request.language}

Plan every day from Day 1 to Day {request.durationDays}. Provide specific local venues, authentic attractions, and realistic costs matching the '{request.budget}' budget. Output ONLY valid JSON matching the requested structure."""

def generate_ai_itinerary(request: TripRequest) -> TripResponse:
    """
    Generate an itinerary using Groq Cloud API with LLaMA 3.3.
    Falls back gracefully to mock generator if API key is missing or on error.
    """
    client = get_groq_client()
    if not client:
        logger.info("GROQ_API_KEY is not configured. Utilizing adaptive fallback mock generator.")
        return generate_mock_itinerary(request)

    system_prompt = build_system_prompt(request.language)
    user_prompt = build_user_prompt(request)

    models_to_try = SUPPORTED_MODELS
    raw_content = None
    last_error = None

    for model_name in models_to_try:
        try:
            logger.info(f"Calling Groq API model='{model_name}' for destination='{request.destination}'...")
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_completion_tokens=4096
            )
            raw_content = completion.choices[0].message.content
            if raw_content:
                logger.info(f"Successfully received response from Groq ({model_name}).")
                break
        except RateLimitError as rle:
            logger.warning(f"Groq RateLimitError on model '{model_name}': {str(rle)}. Trying fallback model...")
            last_error = rle
            continue
        except AuthenticationError as ae:
            logger.error(f"Groq AuthenticationError (invalid GROQ_API_KEY): {str(ae)}")
            last_error = ae
            break
        except (APIConnectionError, APIStatusError) as api_err:
            logger.error(f"Groq API error on model '{model_name}': {str(api_err)}")
            last_error = api_err
            continue
        except Exception as exc:
            logger.error(f"Unexpected error calling Groq on model '{model_name}': {str(exc)}")
            last_error = exc
            break

    if not raw_content:
        logger.warning(f"Could not obtain response from Groq ({last_error}). Falling back to mock generator.")
        fallback_resp = generate_mock_itinerary(request)
        if isinstance(last_error, RateLimitError):
            err_tag = "[AI RATE LIMITED - 429]"
        elif isinstance(last_error, AuthenticationError):
            err_tag = "[AI AUTHENTICATION ERROR - CHECK GROQ_API_KEY]"
        elif isinstance(last_error, APIConnectionError):
            err_tag = "[AI NETWORK CONNECTION ERROR]"
        else:
            err_tag = f"[AI SERVICE NOTICE: {type(last_error).__name__ if last_error else 'Connection Error'}]"

        fallback_resp.summary = (
            f"{err_tag} Showing verified fallback itinerary for {request.destination}."
        )
        return fallback_resp

    try:
        parsed_data = json.loads(raw_content)
        parsed_data["destination"] = parsed_data.get("destination") or request.destination
        parsed_data["duration_days"] = request.durationDays
        parsed_data["start_date"] = request.startDate
        parsed_data["end_date"] = request.endDate
        parsed_data["language"] = request.language
        parsed_data["budget_tier"] = request.budget
        parsed_data["travelers_count"] = request.travelersCount
        parsed_data["traveler_type"] = request.travelerType
        parsed_data["pace"] = request.pace
        parsed_data["interests"] = request.interests
        parsed_data["is_mock"] = False
        parsed_data["source"] = "groq_ai"
        parsed_data["hero_image_url"] = (
            "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80"
        )

        # Ensure Skill Wallet fields are always present
        if not parsed_data.get("accommodation_suggestions"):
            mock_ref = generate_mock_itinerary(request)
            parsed_data["accommodation_suggestions"] = mock_ref.accommodation_suggestions

        if not parsed_data.get("disclaimer"):
            parsed_data["disclaimer"] = (
                "Prices, opening hours, and transport schedules are estimates based on standard regional rates and may vary seasonally. "
                "Real-time availability must be verified directly with providers. Live bookings are not confirmed."
            )

        validated_response = TripResponse.model_validate(parsed_data)
        return validated_response

    except Exception as parse_exc:
        logger.error(f"Failed to parse or validate Groq AI JSON output: {str(parse_exc)}. Raw: {raw_content[:200]}...")
        fallback = generate_mock_itinerary(request)
        fallback.summary = f"[AI PARSE RECOVERY] Showing structured fallback itinerary for {request.destination}."
        return fallback

def regenerate_ai_day(request: RegenerateDayRequest) -> DayPlan:
    """
    Regenerate a single day itinerary using Groq AI.
    Falls back gracefully to mock day generator if key is missing or on error.
    """
    client = get_groq_client()
    if not client:
        return regenerate_mock_day(request)

    target_lang = LANGUAGE_MAP.get(request.language.lower(), "English")
    custom_inst = f"\nUser Instruction: {request.custom_instruction}" if request.custom_instruction else ""

    prompt = f"""You are TripGenie AI. Regenerate Day {request.day_number} of a trip to {request.destination}.
Parameters:
- Budget Tier: {request.budget}
- Traveler Type: {request.travelerType}
- Pace: {request.pace}
- Interests: {', '.join(request.interests) if request.interests else 'General'}{custom_inst}

Output ONLY valid JSON with this exact schema in {target_lang}:
{{
  "day_number": {request.day_number},
  "theme": "Fresh alternative day theme",
  "activities": [
    {{
      "time_of_day": "Morning",
      "title": "Title",
      "description": "Description",
      "photo_query": "English keywords for photo",
      "estimated_cost": "$XX per person",
      "location": "Location",
      "attraction": "Attraction name",
      "food_option": "Food spot / dish"
    }},
    {{
      "time_of_day": "Afternoon",
      "title": "Title",
      "description": "Description",
      "photo_query": "English keywords for photo",
      "estimated_cost": "$XX per person",
      "location": "Location",
      "attraction": "Attraction name",
      "food_option": "Food spot / dish"
    }},
    {{
      "time_of_day": "Evening",
      "title": "Title",
      "description": "Description",
      "photo_query": "English keywords for photo",
      "estimated_cost": "$XX per person",
      "location": "Location",
      "attraction": "Attraction name",
      "food_option": "Food spot / dish"
    }}
  ]
}}"""

    for model_name in SUPPORTED_MODELS:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": f"You are a travel assistant outputting JSON in {target_lang}."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_completion_tokens=2048
            )
            raw = completion.choices[0].message.content
            data = json.loads(raw)
            data["day_number"] = request.day_number
            return DayPlan.model_validate(data)
        except Exception as exc:
            logger.warning(f"Error regenerating day with Groq model '{model_name}' ({exc}). Trying fallback...")
            continue

    logger.warning("All Groq models exhausted for day regeneration. Falling back to mock day generator.")
    return regenerate_mock_day(request)
