import random
from typing import List, Dict, Any, Optional
from ..models.schemas import (
    TripRequest,
    TripResponse,
    DayPlan,
    DayActivity,
    BudgetBreakdown,
    RegenerateDayRequest
)

# Multilingual localization dictionaries for realistic mock generation
LOCALIZED_TERMS = {
    "en": {
        "day_prefix": "Day",
        "morning": "Morning",
        "afternoon": "Afternoon",
        "evening": "Evening",
        "per_person": "per person",
        "per_night": "per night",
        "per_day": "per day",
        "total_for": "total for {count} travelers",
        "mock_disclaimer": "[MOCK PREVIEW - FREE MODE] Curated {days}-day {tier} itinerary for {destination} ({count} travelers, {pace} pace). Fully functional without paid APIs.",
        "estimates_disclaimer": "Prices, opening hours, and transport schedules are estimates based on standard regional rates and may vary seasonally. Real-time availability must be verified directly with providers. Live bookings are not confirmed."
    },
    "hi": {
        "day_prefix": "दिन",
        "morning": "सुबह",
        "afternoon": "दोपहर",
        "evening": "शाम",
        "per_person": "प्रति व्यक्ति",
        "per_night": "प्रति रात",
        "per_day": "प्रति दिन",
        "total_for": "{count} यात्रियों के लिए कुल",
        "mock_disclaimer": "[डेमो पूर्वावलोकन - नि:शुल्क मोड] {destination} के लिए {days}-दिवसीय {tier} यात्रा योजना ({count} यात्री, {pace} गति)। बिना किसी सशुल्क API के पूरी तरह कार्यात्मक।",
        "estimates_disclaimer": "कीमतें, खुलने का समय और परिवहन कार्यक्रम मानक क्षेत्रीय दरों पर आधारित अनुमान हैं और मौसम के अनुसार बदल सकते हैं। वास्तविक समय की उपलब्धता सीधे प्रदाताओं से सत्यापित की जानी चाहिए। लाइव बुकिंग की पुष्टि नहीं है।"
    },
    "es": {
        "day_prefix": "Día",
        "morning": "Mañana",
        "afternoon": "Tarde",
        "evening": "Noche",
        "per_person": "por persona",
        "per_night": "por noche",
        "per_day": "por día",
        "total_for": "total para {count} viajeros",
        "mock_disclaimer": "[VISTA PREVIA MOCK - MODO GRATUITO] Itinerario de {days} días ({tier}) para {destination} ({count} viajeros, ritmo {pace}). Completamente funcional sin servicios pagos.",
        "estimates_disclaimer": "Los precios, horarios y rutas de transporte son estimaciones basadas en tarifas promedio y pueden variar según la temporada. La disponibilidad en tiempo real debe confirmarse directamente con los proveedores. No se confirman reservas en vivo."
    },
    "fr": {
        "day_prefix": "Jour",
        "morning": "Matin",
        "afternoon": "Après-midi",
        "evening": "Soirée",
        "per_person": "par personne",
        "per_night": "par nuit",
        "per_day": "par jour",
        "total_for": "total pour {count} voyageurs",
        "mock_disclaimer": "[APERÇU MOCK - MODE GRATUIT] Itinéraire soigné de {days} jours ({tier}) pour {destination} ({count} voyageurs, rythme {pace}). Entièrement fonctionnel sans API payante.",
        "estimates_disclaimer": "Les tarifs, horaires d'ouverture et itinéraires de transport sont des estimations indicatives sujettes à variation saisonnière. Les disponibilités en temps réel doivent être confirmées auprès des prestataires. Aucune réservation en direct n'est confirmée."
    }
}

ACCOMMODATION_TEMPLATES = {
    "en": {
        "budget": [
            "{dest} Backpacker & Eco-Hostel (Dorm beds & private pods near central transit)",
            "{dest} Heritage Guesthouse (Cozy family-run B&B with complimentary local breakfast)",
            "Green Haven Pods {dest} (Modern compact rooms with shared traveler lounge & fast WiFi)"
        ],
        "moderate": [
            "Grand Central Boutique Hotel {dest} (Stylish 3-star property with breakfast included)",
            "{dest} Heritage Inn & Suites (Character-rich rooms walking distance to cultural quarter)",
            "The Vista Riverfront Hotel {dest} (Comfortable midscale lodging with panoramic city views)"
        ],
        "luxury": [
            "The Royal Oasis Luxury Resort & Spa {dest} (5-star suites with private plunge pool and fine dining)",
            "Palazzo {dest} Boutique Residences (Opulent heritage restoration with concierge service)",
            "Celestial Panorama Resort {dest} (Exclusive hillside suites with infinity pool and spa treatments)"
        ]
    },
    "hi": {
        "budget": [
            "{dest} बैकपैकर व ईको-हॉस्टल (केंद्रीय परिवहन के पास किफायती बेड और निजी पॉड्स)",
            "{dest} हेरिटेज गेस्टहाउस (स्थानीय नाश्ते के साथ आरामदायक पारिवारिक होमस्टे)",
            "ग्रीन हेवन पॉड्स {dest} (मुफ्त वाईफाई और लाउंज के साथ आधुनिक कमरे)"
        ],
        "moderate": [
            "ग्रैंड सेंट्रल बुटीक होटल {dest} (नाश्ते सहित आकर्षक 3-सितारा होटल)",
            "{dest} हेरिटेज इन एंड सुइट्स (सांस्कृतिक क्षेत्र के पास ऐतिहासिक सुंदर कमरे)",
            "द विस्टा रिवरफ्रंट होटल {dest} (मनोरम दृश्यों के साथ आरामदायक होटल)"
        ],
        "luxury": [
            "द रॉयल ओएसिस लक्जरी रिसॉर्ट एंड स्पा {dest} (निजी पूल और बढ़िया भोजन के साथ 5-सितारा रिसॉर्ट)",
            "पलाज़ो {dest} बुटीक रेजिडेंस (शाही अनुभव और कंसीयज सेवा के साथ हेरिटेज पैलेस)",
            "सेलेस्टियल पैनोरमा रिसॉर्ट {dest} (इन्फिनिटी पूल और स्पा के साथ पहाड़ी सुइट्स)"
        ]
    },
    "es": {
        "budget": [
            "{dest} Backpacker & Eco-Hostel (Camas compartidas y cápsulas cerca del transporte)",
            "{dest} Heritage Casa de Huéspedes (B&B familiar acogedor con desayuno típico)",
            "Green Haven Pods {dest} (Habitaciones compactas modernas con wifi de alta velocidad)"
        ],
        "moderate": [
            "Grand Central Hotel Boutique {dest} (Elegante hotel 3 estrellas con desayuno)",
            "{dest} Heritage Inn & Suites (Habitaciones tradicionales cerca del casco histórico)",
            "The Vista Hotel Fluvial {dest} (Alojamiento cómodo con vistas panorámicas)"
        ],
        "luxury": [
            "The Royal Oasis Luxury Resort & Spa {dest} (Suites 5 estrellas con piscina privada y alta cocina)",
            "Palacio {dest} Residencias Boutique (Lujo histórico restaurado con servicio de conserjería)",
            "Celestial Panorama Resort {dest} (Exclusivas suites con piscina infinita y spa)"
        ]
    },
    "fr": {
        "budget": [
            "{dest} Backpacker & Auberge Éco (Lits en dortoir et capsules proches des transports)",
            "{dest} Maison d'Hôtes Historique (B&B familial chaleureux avec petit-déjeuner local)",
            "Green Haven Pods {dest} (Chambres compactes modernes avec salon partagé et WiFi)"
        ],
        "moderate": [
            "Grand Central Hôtel Boutique {dest} (Établissement élégant 3 étoiles avec petit-déjeuner)",
            "{dest} Heritage Hôtel & Suites (Chambres de caractère à deux pas du quartier culturel)",
            "The Vista Hôtel Panoramique {dest} (Hébergement de charme avec vue imprenable)"
        ],
        "luxury": [
            "The Royal Oasis Hôtel Resort & Spa {dest} (Suites 5 étoiles avec piscine privée et haute gastronomie)",
            "Palais {dest} Résidences d'Exception (Demeure historique somptueuse avec conciergerie)",
            "Celestial Panorama Resort {dest} (Suites exclusives à flanc de colline avec piscine à débordement)"
        ]
    }
}

# Thematic templates per language
THEME_POOLS = {
    "en": [
        ("Arrival & Old Town Exploration", "Stroll the historic core and sample regional cafes", "Old Town Quarter", "Artisan bakery breakfast"),
        ("Iconic Heritage & Landmark Tour", "Visit primary architectural wonders and cultural treasures", "Grand Heritage Plaza", "Traditional market specialty"),
        ("Scenic Nature & Mountain Views", "Panoramic overlook, serene walking trails and nature reserves", "High Vista Point", "Scenic terrace picnic lunch"),
        ("Culinary Traditions & Local Markets", "Taste fresh seasonal street foods and farm-fresh produce", "Central Farmers Bazaar", "Handmade regional tasting menu"),
        ("Artisan Crafts & Hidden Alleys", "Discover hidden courtyards, local painters and bespoke shops", "Craftsman Quarter", "Courtyard tea and pastries"),
        ("Active Adventure & Outdoor Trek", "Invigorating hiking trail with majestic photographic vantage points", "Wilderness Ridge Trail", "Energy trail snack & fresh juices"),
        ("Wellness, Leisure & Thermal Springs", "Relax in tranquil public gardens and soothing wellness retreats", "Thermal Springs Park", "Healthy organic farm-to-table lunch"),
        ("Sunset Panorama & Festive Farewell", "Celebrate with sunset views, live folk music and celebratory banquet", "Harbor / Sky Terrace", "Festive multi-course dinner")
    ],
    "hi": [
        ("आगमन और पुराने शहर का भ्रमण", "ऐतिहासिक गलियों में टहलें और स्थानीय चाय-नाश्ते का आनंद लें", "पुराना शहर चौराहा", "स्थानीय पारंपरिक नाश्ता"),
        ("सांस्कृतिक धरोहर और प्रमुख स्थल", "प्रसिद्ध स्मारकों और वास्तुकला की भव्यता का अनुभव करें", "ऐतिहासिक धरोहर परिसर", "पारंपरिक भोजन थाली"),
        ("प्राकृतिक सौंदर्य और मनोरम दृश्य", "पहाड़ी चोटियों और शांत प्राकृतिक उद्यानों की सैर", "पैनोरमा व्यू प्वाइंट", "प्रकृति के बीच अल्पाहार"),
        ("खान-पान और स्थानीय बाज़ार", "ताज़ा मौसमी व्यंजन और प्रसिद्ध स्ट्रीट फ़ूड का स्वाद", "केंद्रीय बाज़ार", "क्षेत्रीय विशेष मिठाइयाँ और व्यंजन"),
        ("कला और कारीगरी की खोज", "पारंपरिक हस्तशिल्प और स्थानीय कारीगरों की कार्यशालाएँ", "शिल्पकार मोहल्ला", "स्थानीय हर्बल चाय और नमकीन"),
        ("रोमांच और ट्रैकिंग अभियान", "सुंदर घाटियों और पगडंडियों पर रोमांचक पदयात्रा", "नेचर ट्रेल मार्ग", "ऊर्जावर्धक ताज़ा पेय"),
        ("विश्राम और शांतिपूर्ण अनुभव", "शांत उद्यानों में ध्यान और सुकून भरे पल", "शांति उद्यान", "शुद्ध सात्विक दोपहर का भोजन"),
        ("सूर्यास्त दर्शन और विदाई भोज", "सुंदर सूर्यास्त के साथ पारंपरिक संगीत और भव्य विदाई रात्रिभोज", "सूर्यास्त दृष्टिकोण", "पारंपरिक उत्सव भोज")
    ],
    "es": [
        ("Llegada y Casco Antiguo", "Paseo por las calles históricas y cafés tradicionales", "Plaza Histórica Central", "Desayuno artesanal y café de origen"),
        ("Patrimonio y Monumentos", "Recorrido por los monumentos y museos emblemáticos", "Distrito Monumental", "Menú del día tradicional"),
        ("Naturaleza y Miradores", "Senderismo ligero hacia los miradores panorámicos", "Mirador de las Alturas", "Picnic campestre con productos locales"),
        ("Ruta Gastronómica y Mercados", "Degustación de tapas y productos frescos del mercado", "Mercado Central", "Selección de tapas regionales"),
        ("Arte y Rincones Ocultos", "Descubrimiento de talleres artesanales y callejones floridos", "Barrio de los Artesanos", "Café y repostería típica"),
        ("Aventura y Senderos Vivos", "Caminata activa con vistas espectaculares para fotografía", "Sendero de la Colina", "Almuerzo energizante al aire libre"),
        ("Relajación y Parques Naturales", "Tarde de descanso en jardines botánicos y aguas termales", "Parque Termal", "Cocina orgánica y ligera"),
        ("Puesta de Sol y Cena de Despedida", "Espectacular atardecer y cena con música en vivo", "Terraza Panorámica", "Banquete tradicional de despedida")
    ],
    "fr": [
        ("Arrivée et Vieux Quartier", "Flânerie dans le centre historique et cafés pittoresques", "Place du Vieux Marché", "Café torréfié et viennoiseries"),
        ("Patrimoine et Monuments", "Visite des joyaux architecturaux et musées culturels", "Quartier Historique", "Plat du jour traditionnel"),
        ("Nature et Panoramas", "Balade revigorante vers les belvédères panoramiques", "Belvédère des Cimes", "Pique-nique de terroir"),
        ("Saveurs et Marchés Locaux", "Dégustation de spécialités régionales et étals de marché", "Marché des Halles", "Assortiment de spécialités locales"),
        ("Artisanat et Ruelle Secrète", "Exploration des ateliers d'artistes et cours secrètes", "Cour des Artisans", "Thé parfumé et pâtisseries"),
        ("Aventure et Sentiers Sauvages", "Randonnée stimulante et paysages spectaculaires", "Sentier des Crêtes", "En-cas énergétique et jus frais"),
        ("Détente et Sérénité", "Après-midi de repos dans les parcs arborés et thermes", "Jardin des Sources", "Déjeuner équilibré du terroir"),
        ("Coucher de Soleil et Dîner Festif", "Dépaisement au crépuscule et dîner gastronomique de départ", "Terrasse Panoramique", "Dîner gastronomique festif")
    ]
}

COST_ESTIMATES = {
    "budget": {
        "morning": "$5 - $12",
        "afternoon": "$10 - $20",
        "evening": "$15 - $30",
        "daily_total": 45,
        "accommodation": "$25 - $50 per night",
        "food_and_dining": "$20 - $35 per day",
        "activities_and_entry": "$8 - $18 per day",
        "local_transport": "$5 - $12 per day"
    },
    "moderate": {
        "morning": "$15 - $25",
        "afternoon": "$25 - $50",
        "evening": "$40 - $75",
        "daily_total": 115,
        "accommodation": "$80 - $160 per night",
        "food_and_dining": "$45 - $85 per day",
        "activities_and_entry": "$25 - $45 per day",
        "local_transport": "$15 - $30 per day"
    },
    "luxury": {
        "morning": "$40 - $80",
        "afternoon": "$80 - $160",
        "evening": "$120 - $250",
        "daily_total": 340,
        "accommodation": "$250 - $600 per night",
        "food_and_dining": "$120 - $250 per day",
        "activities_and_entry": "$80 - $180 per day",
        "local_transport": "$50 - $120 per day"
    }
}

def generate_mock_itinerary(request: TripRequest) -> TripResponse:
    """
    Generate an engaging, highly realistic mock itinerary in the user's requested language.
    Does NOT require any external paid API or network connection.
    """
    dest = request.destination.strip()
    lang = request.language.lower() if request.language.lower() in LOCALIZED_TERMS else "en"
    terms = LOCALIZED_TERMS[lang]
    tier = request.budget if request.budget in COST_ESTIMATES else "moderate"
    costs = COST_ESTIMATES[tier]

    themes = THEME_POOLS.get(lang, THEME_POOLS["en"])
    days: List[DayPlan] = []

    for day_idx in range(1, request.durationDays + 1):
        theme_item = themes[(day_idx - 1) % len(themes)]
        theme_title = f"{terms['day_prefix']} {day_idx}: {theme_item[0]}"
        theme_desc = theme_item[1]
        location_name = f"{dest} {theme_item[2]}"
        food_name = theme_item[3]

        # Build 3 structured activities
        morning = DayActivity(
            time_of_day=terms["morning"],
            title=f"{theme_item[0]} - {terms['morning']}",
            description=f"{theme_desc} in {dest}. Tailored for {request.travelersCount} travelers at a {request.pace} pace.",
            photo_query=f"{dest} morning landmark scenic",
            estimated_cost=f"{costs['morning']} {terms['per_person']}",
            location=location_name,
            attraction=f"{dest} {theme_item[2]}",
            food_option=food_name
        )

        afternoon = DayActivity(
            time_of_day=terms["afternoon"],
            title=f"{theme_item[0]} - {terms['afternoon']}",
            description=f"Deep-dive exploration through cultural and scenic highlights of {dest}.",
            photo_query=f"{dest} afternoon historic street architecture",
            estimated_cost=f"{costs['afternoon']} {terms['per_person']}",
            location=f"{dest} Historic Center",
            attraction=f"{dest} Cultural Site",
            food_option=f"Specialty lunch in {dest}"
        )

        evening = DayActivity(
            time_of_day=terms["evening"],
            title=f"{theme_item[0]} - {terms['evening']}",
            description=f"Sunset views and twilight atmosphere, followed by dinner in {dest}.",
            photo_query=f"{dest} sunset evening dinner illuminated",
            estimated_cost=f"{costs['evening']} {terms['per_person']}",
            location=f"{dest} Sunset Promenade",
            attraction=f"{dest} Twilight Vista Point",
            food_option=f"Evening culinary specialty in {dest}"
        )

        days.append(DayPlan(day_number=day_idx, theme=theme_title, activities=[morning, afternoon, evening]))

    estimated_total = costs["daily_total"] * request.durationDays * request.travelersCount
    total_text = terms["total_for"].format(count=request.travelersCount)

    summary = terms["mock_disclaimer"].format(
        days=request.durationDays,
        tier=tier,
        destination=dest,
        count=request.travelersCount,
        pace=request.pace
    )

    budget_breakdown = BudgetBreakdown(
        accommodation=f"{costs['accommodation']}",
        food_and_dining=f"{costs['food_and_dining']}",
        activities_and_entry=f"{costs['activities_and_entry']}",
        local_transport=f"{costs['local_transport']}"
    )

    travel_tips = [
        f"Download offline maps for {dest} to navigate smoothly without roaming data.",
        f"Keep local currency or small change handy for artisanal markets and transit.",
        f"Dress in comfortable walking shoes to enjoy pedestrian exploration in {dest}.",
        f"Check local seasonal weather before heading out for morning activities."
    ]

    transport_suggestions = [
        f"Walking is the best way to discover the central quarters of {dest}.",
        f"Local public transit (bus or metro) is reliable and cost-effective.",
        f"Official metered taxis or rideshare apps are recommended for late evenings."
    ]

    # Curate accommodation options tailored to destination, budget tier, and language
    acc_pool = ACCOMMODATION_TEMPLATES.get(lang, ACCOMMODATION_TEMPLATES["en"]).get(
        tier, ACCOMMODATION_TEMPLATES["en"]["moderate"]
    )
    accommodation_suggestions = [template.format(dest=dest) for template in acc_pool]
    estimates_disclaimer = terms.get(
        "estimates_disclaimer",
        "Prices, opening hours, and transport schedules are estimates based on standard regional rates and may vary seasonally. Real-time availability must be verified directly with providers. Live bookings are not confirmed."
    )

    return TripResponse(
        destination=dest,
        summary=summary,
        duration_days=request.durationDays,
        start_date=request.startDate,
        end_date=request.endDate,
        language=lang,
        budget_tier=tier,
        currency="USD",
        estimated_total_cost=f"${estimated_total:,} USD ({total_text})",
        budget_breakdown=budget_breakdown,
        travel_tips=travel_tips,
        transport_suggestions=transport_suggestions,
        accommodation_suggestions=accommodation_suggestions,
        disclaimer=estimates_disclaimer,
        travelers_count=request.travelersCount,
        traveler_type=request.travelerType,
        pace=request.pace,
        interests=request.interests,
        days=days,
        hero_image_url="https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80",
        is_mock=True,
        source="mock_generator"
    )

def regenerate_mock_day(request: RegenerateDayRequest) -> DayPlan:
    """
    Regenerate a single day with alternative themes and activities.
    Supports user custom instructions (e.g. 'more nature', 'street food focus').
    """
    dest = request.destination.strip()
    lang = request.language.lower() if request.language.lower() in LOCALIZED_TERMS else "en"
    terms = LOCALIZED_TERMS[lang]
    tier = request.budget if request.budget in COST_ESTIMATES else "moderate"
    costs = COST_ESTIMATES[tier]

    themes = THEME_POOLS.get(lang, THEME_POOLS["en"])
    # Pick an alternative index distinct from day_number to ensure variation
    alt_idx = (request.day_number + 2) % len(themes)
    theme_item = themes[alt_idx]

    instruction_note = f" [{request.custom_instruction}]" if request.custom_instruction else ""
    theme_title = f"{terms['day_prefix']} {request.day_number}: {theme_item[0]}{instruction_note}"

    morning = DayActivity(
        time_of_day=terms["morning"],
        title=f"{theme_item[0]} (Alternative Option)",
        description=f"Fresh morning recommendation for {dest}: {theme_item[1]}.{instruction_note}",
        photo_query=f"{dest} scenic morning outdoor exploration",
        estimated_cost=f"{costs['morning']} {terms['per_person']}",
        location=f"{dest} {theme_item[2]}",
        attraction=f"{dest} Alternative Spot",
        food_option=theme_item[3]
    )

    afternoon = DayActivity(
        time_of_day=terms["afternoon"],
        title=f"Afternoon Discovery in {dest}",
        description=f"Curated afternoon itinerary based on your updated preferences.{instruction_note}",
        photo_query=f"{dest} afternoon cultural market",
        estimated_cost=f"{costs['afternoon']} {terms['per_person']}",
        location=f"{dest} Discovery Quarter",
        attraction=f"{dest} Artisan Workshop",
        food_option=f"Regional chef specialty in {dest}"
    )

    evening = DayActivity(
        time_of_day=terms["evening"],
        title=f"Evening Atmosphere & Dining",
        description=f"Relaxing evening itinerary tailored for a {request.pace} pace.{instruction_note}",
        photo_query=f"{dest} evening twilight restaurant",
        estimated_cost=f"{costs['evening']} {terms['per_person']}",
        location=f"{dest} Panorama Viewpoint",
        attraction=f"{dest} Night Sky Overlook",
        food_option=f"Traditional culinary feast in {dest}"
    )

    return DayPlan(
        day_number=request.day_number,
        theme=theme_title,
        activities=[morning, afternoon, evening]
    )
