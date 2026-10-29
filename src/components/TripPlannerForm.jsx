import React, { useState, useEffect, useRef } from 'react';
import {
  MapPin,
  Calendar,
  DollarSign,
  Users,
  Compass,
  Sparkles,
  Heart,
  Coffee,
  Trees,
  Landmark,
  Camera,
  ShoppingBag,
  Flame,
  Clock,
  ArrowRight,
  ArrowLeft,
  Globe,
  Check,
  Edit3,
  X,
  Loader2,
  AlertCircle,
  Bus,
  Lightbulb,
  Utensils,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Bookmark,
  Printer,
  FolderHeart,
  Trash2,
  Hotel,
  Bed,
  Info
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { formatLocaleDate, LANGUAGE_OPTIONS } from '../utils/formatters';
import { getOrCreateGuestId } from '../utils/guestIdentity';
import { POPULAR_GLOBAL_DESTINATIONS as SUGGESTED_DESTINATIONS } from '../data/popularDestinations';

const INTEREST_ITEMS = [
  { id: 'culinary', icon: Coffee },
  { id: 'history', icon: Landmark },
  { id: 'nature', icon: Trees },
  { id: 'culture', icon: Camera },
  { id: 'adventure', icon: Flame },
  { id: 'relaxation', icon: Heart },
  { id: 'shopping', icon: ShoppingBag },
];

const BUDGET_KEYS = [
  { id: 'budget', tier: '$' },
  { id: 'moderate', tier: '$$' },
  { id: 'luxury', tier: '$$$' }
];

export default function TripPlannerForm({ initialDestination = '', externalDestination, onDestinationChange }) {
  const { t, i18n } = useTranslation();

  // Wizard Step: 1, 2, or 3
  const [currentStep, setCurrentStep] = useState(1);

  // Form State: Owns destination independently
  const [destination, setDestination] = useState(initialDestination || '');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [budget, setBudget] = useState('moderate');
  const [travelerType, setTravelerType] = useState('couple');
  const [travelersCount, setTravelersCount] = useState(2);
  const [selectedInterests, setSelectedInterests] = useState(['culinary', 'history']);
  const [pace, setPace] = useState('balanced');

  // Autocomplete dropdown state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [isSearchingDestinations, setIsSearchingDestinations] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [searchFailed, setSearchFailed] = useState(false);
  const suggestionBoxRef = useRef(null);

  // Generation & Results State
  const [validationError, setValidationError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState(null);
  const [generatedItinerary, setGeneratedItinerary] = useState(null);
  const [expandedDay, setExpandedDay] = useState(1);
  const [savedTrips, setSavedTrips] = useState([]);
  const [showSavedModal, setShowSavedModal] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [regeneratingDay, setRegeneratingDay] = useState(null);
  const [editingActivity, setEditingActivity] = useState(null);

  const fetchSavedTrips = async () => {
    try {
      const guestId = getOrCreateGuestId();
      const res = await fetch(`http://localhost:8000/api/trips?user_id=${encodeURIComponent(guestId)}`, {
        headers: { 'X-User-Id': guestId }
      });
      if (res.ok) {
        const data = await res.json();
        setSavedTrips(data.trips || []);
      }
    } catch {
      // Graceful fallback if backend is temporarily offline
    }
  };

  useEffect(() => {
    fetchSavedTrips();
  }, []);

  const handleSaveTrip = async () => {
    if (!generatedItinerary || isSaving) return;
    setIsSaving(true);
    try {
      const guestId = getOrCreateGuestId();
      const res = await fetch('http://localhost:8000/api/trips', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': guestId
        },
        body: JSON.stringify({ trip: generatedItinerary, user_id: guestId })
      });
      if (res.ok) {
        const saved = await res.json();
        setIsSaved(true);
        setGeneratedItinerary(saved.itinerary_data);
        fetchSavedTrips();
      }
    } catch (err) {
      console.error('Failed to save trip:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteTrip = async (tripId, e) => {
    if (e) e.stopPropagation();
    try {
      const guestId = getOrCreateGuestId();
      const res = await fetch(`http://localhost:8000/api/trips/${encodeURIComponent(tripId)}?user_id=${encodeURIComponent(guestId)}`, {
        method: 'DELETE',
        headers: { 'X-User-Id': guestId }
      });
      if (res.ok) {
        setSavedTrips((prev) => prev.filter((t) => t.id !== tripId));
        if (generatedItinerary?.id === tripId) {
          setIsSaved(false);
        }
      }
    } catch (err) {
      console.error('Failed to delete trip:', err);
    }
  };

  const handleLoadSavedTrip = (record) => {
    setGeneratedItinerary(record.itinerary_data);
    setDestination(record.destination);
    setIsSaved(true);
    setShowSavedModal(false);
    setCurrentStep(3);
  };

  const handleRegenerateDay = async (dayNumber) => {
    if (regeneratingDay) return;
    setRegeneratingDay(dayNumber);
    try {
      const res = await fetch('http://localhost:8000/api/itinerary/regenerate-day', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination: generatedItinerary.destination,
          day_number: dayNumber,
          budget: generatedItinerary.budget_tier || 'moderate',
          travelerType: generatedItinerary.traveler_type || 'couple',
          pace: generatedItinerary.pace || 'balanced',
          language: i18n.language,
          interests: generatedItinerary.interests || []
        })
      });
      if (res.ok) {
        const newDayPlan = await res.json();
        setGeneratedItinerary((prev) => ({
          ...prev,
          days: prev.days.map((d) => (d.day_number === dayNumber ? newDayPlan : d))
        }));
        setIsSaved(false);
      }
    } catch (err) {
      console.error('Failed to regenerate day:', err);
    } finally {
      setRegeneratingDay(null);
    }
  };

  const handleSaveActivityEdit = (e) => {
    e.preventDefault();
    if (!editingActivity) return;
    const { dayNumber, actIdx, title, description, location, attraction, food_option, estimated_cost } = editingActivity;

    setGeneratedItinerary((prev) => ({
      ...prev,
      days: prev.days.map((d) => {
        if (d.day_number !== dayNumber) return d;
        const newActs = [...d.activities];
        newActs[actIdx] = {
          ...newActs[actIdx],
          title,
          description,
          location,
          attraction,
          food_option,
          estimated_cost
        };
        return { ...d, activities: newActs };
      })
    }));
    setIsSaved(false);
    setEditingActivity(null);
  };

  // Update destination ONLY when externalDestination explicitly changes from an intentional external click
  const lastExternalRef = useRef(externalDestination);
  useEffect(() => {
    if (externalDestination && externalDestination !== lastExternalRef.current) {
      lastExternalRef.current = externalDestination;
      setDestination(externalDestination);
    }
  }, [externalDestination]);

  // Dismiss suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (suggestionBoxRef.current && !suggestionBoxRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search against backend /api/destinations/search (Free GeoNames gazetteer)
  useEffect(() => {
    const trimmed = destination.trim();
    if (!trimmed || trimmed.length < 2) {
      setSuggestions([]);
      setIsSearchingDestinations(false);
      setHighlightedIndex(-1);
      return;
    }

    setIsSearchingDestinations(true);
    setSearchFailed(false);

    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/destinations/search?q=${encodeURIComponent(trimmed)}&limit=8`);
        if (!res.ok) throw new Error('Search failed');
        const data = await res.json();
        setSuggestions(data.results || []);
        setHighlightedIndex(-1);
      } catch (err) {
        console.warn('Destination search offline fallback:', err);
        setSearchFailed(true);
        const fallback = SUGGESTED_DESTINATIONS.filter(
          (s) =>
            s.name.toLowerCase().includes(trimmed.toLowerCase()) ||
            s.country.toLowerCase().includes(trimmed.toLowerCase()) ||
            s.full.toLowerCase().includes(trimmed.toLowerCase())
        ).map((s) => ({
          name: s.name,
          region: '',
          country: s.country,
          country_code: '',
          full_name: s.full,
          place_type: 'destination'
        }));
        setSuggestions(fallback);
      } finally {
        setIsSearchingDestinations(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [destination]);

  // Calculate duration
  const getDays = () => {
    if (!startDate || !endDate) return null;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = end - start;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return diffDays > 0 ? diffDays : null;
  };

  const tripDays = getDays();

  const toggleInterest = (id) => {
    if (selectedInterests.includes(id)) {
      if (selectedInterests.length > 1) {
        setSelectedInterests(selectedInterests.filter((item) => item !== id));
      }
    } else {
      setSelectedInterests([...selectedInterests, id]);
    }
  };

  const handleDestinationInputChange = (e) => {
    const val = e.target.value;
    setDestination(val);
    setShowSuggestions(true);
    setValidationError('');
    if (onDestinationChange) {
      onDestinationChange(val);
    }
  };

  const handleSelectSuggestion = (fullQuery) => {
    setDestination(fullQuery);
    setShowSuggestions(false);
    setValidationError('');
    if (onDestinationChange) {
      onDestinationChange(fullQuery);
    }
  };

  const handleDestinationKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      if (showSuggestions && suggestions.length > 0) {
        e.preventDefault();
        setHighlightedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
      }
    } else if (e.key === 'ArrowUp') {
      if (showSuggestions && suggestions.length > 0) {
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
      }
    } else if (e.key === 'Enter') {
      e.preventDefault(); // NEVER erase typed text or refresh page
      if (showSuggestions && highlightedIndex >= 0 && suggestions[highlightedIndex]) {
        handleSelectSuggestion(suggestions[highlightedIndex].full_name);
      } else {
        setShowSuggestions(false);
        if (validateStep1()) {
          setCurrentStep(2);
        }
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setHighlightedIndex(-1);
    }
  };

  // Step 1 Validation: Only requires non-empty string! Never rejects custom places
  const validateStep1 = () => {
    setValidationError('');
    if (!destination || !destination.trim()) {
      setValidationError(t('planner.errors.destination'));
      return false;
    }
    if (!startDate || !endDate) {
      setValidationError(t('planner.errors.dates'));
      return false;
    }
    if (tripDays === null || tripDays <= 0) {
      setValidationError(t('planner.errors.invalidDates'));
      return false;
    }
    return true;
  };

  const handleNextToStep2 = () => {
    if (validateStep1()) {
      setCurrentStep(2);
    }
  };

  const handleNextToStep3 = () => {
    setValidationError('');
    setCurrentStep(3);
  };

  const handleFinalSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!validateStep1()) {
      setCurrentStep(1);
      return;
    }

    const payload = {
      destination: destination.trim(),
      startDate,
      endDate,
      durationDays: tripDays,
      budget,
      travelerType,
      travelersCount,
      interests: selectedInterests,
      pace,
      language: i18n.language,
      languageName: LANGUAGE_OPTIONS.find((l) => l.code === i18n.language)?.native || 'English'
    };

    setIsGenerating(true);
    setGenerationError(null);
    setGeneratedItinerary(null);

    try {
      const response = await fetch('http://localhost:8000/api/itinerary/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      setGeneratedItinerary(data);
      setExpandedDay(1);
    } catch (err) {
      console.error('Error generating itinerary:', err);
      setGenerationError(err.message || 'Could not connect to FastAPI server at http://localhost:8000');
    } finally {
      setIsGenerating(false);
    }
  };

  const STEPS_CONFIG = [
    { num: 1, title: t('planner.wizard.step1Title'), icon: MapPin },
    { num: 2, title: t('planner.wizard.step2Title'), icon: Users },
    { num: 3, title: t('planner.wizard.step3Title'), icon: Sparkles },
  ];

  return (
    <div id="planner" className="w-full">
      {/* Form Card Container */}
      <div className="bg-app-surface/95 dark:bg-slate-900/95 backdrop-blur-xl border border-edge-subtle rounded-3xl shadow-2xl overflow-hidden transition-all duration-300">

        {/* Step Indicator Header */}
        <div className="px-5 sm:px-8 py-4 border-b border-edge-subtle bg-app-elevated/40">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white shadow-xs">
                <Compass className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-teal-600 dark:text-teal-400 font-bold block">
                  {t('planner.wizard.stepOf', { step: currentStep })}
                </span>
                <h2 className="text-base sm:text-lg font-bold font-editorial text-content-main leading-none">
                  {STEPS_CONFIG[currentStep - 1].title}
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  fetchSavedTrips();
                  setShowSavedModal(true);
                }}
                className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 text-[11px] font-semibold text-teal-700 dark:text-teal-300 transition-colors cursor-pointer"
                title="View Saved Trips in Local Database"
              >
                <FolderHeart className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                <span>Saved ({savedTrips.length})</span>
              </button>

              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-app-elevated border border-edge-subtle text-[11px] font-semibold text-content-muted">
                <Globe className="w-3 h-3 text-teal-600 dark:text-teal-400" />
                <span>{LANGUAGE_OPTIONS.find((l) => l.code === i18n.language)?.flag}</span>
                <span>{LANGUAGE_OPTIONS.find((l) => l.code === i18n.language)?.code.toUpperCase()}</span>
              </div>
            </div>
          </div>

          {/* Progress Bar with 3 Step Pills */}
          <div className="grid grid-cols-3 gap-2">
            {STEPS_CONFIG.map((s) => {
              const isPast = currentStep > s.num;
              const isCurrent = currentStep === s.num;

              return (
                <button
                  key={s.num}
                  type="button"
                  onClick={() => {
                    if (isPast || (s.num === 1)) {
                      setCurrentStep(s.num);
                    } else if (s.num === 2 && validateStep1()) {
                      setCurrentStep(2);
                    }
                  }}
                  className={`flex items-center gap-2 py-1.5 px-2.5 rounded-lg text-xs font-semibold transition-all text-left ${
                    isCurrent
                      ? 'bg-teal-600 text-white shadow-xs'
                      : isPast
                      ? 'bg-teal-500/15 text-teal-700 dark:text-teal-300 hover:bg-teal-500/25 cursor-pointer'
                      : 'bg-app-elevated text-content-subtle opacity-70 cursor-not-allowed'
                  }`}
                >
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isCurrent ? 'bg-white text-teal-700' : isPast ? 'bg-teal-600 text-white' : 'bg-slate-300 dark:bg-slate-700 text-slate-700 dark:text-slate-200'
                  }`}>
                    {isPast ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : s.num}
                  </div>
                  <span className="hidden sm:inline truncate">{s.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Validation Error Banner */}
        {validationError && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-300 text-xs font-semibold">
            ⚠️ {validationError}
          </div>
        )}

        {/* ========================================================= */}
        {/* STEP 1: Destination, Dates & Budget                       */}
        {/* ========================================================= */}
        {currentStep === 1 && (
          <div className="p-6 sm:p-8 space-y-6 animate-in fade-in duration-200">
            {/* 1. Destination Input with Free Typing + Optional Autocomplete */}
            <div className="relative" ref={suggestionBoxRef}>
              <label htmlFor="destination" className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-2 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                  {t('planner.destinationLabel')}
                </span>
                <span className="text-[10px] font-normal text-content-subtle lowercase">
                  (type any city, country, or region)
                </span>
              </label>

              <div className="relative">
                <input
                  id="destination"
                  type="text"
                  autoComplete="off"
                  value={destination}
                  onChange={handleDestinationInputChange}
                  onKeyDown={handleDestinationKeyDown}
                  onFocus={() => {
                    if (destination.trim().length > 0) setShowSuggestions(true);
                  }}
                  placeholder="e.g. Manali, Goa, Bali, Paris, Kyoto..."
                  className="w-full px-4 py-3 pl-11 pr-10 text-base text-content-main bg-app-input border border-edge-strong rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-edge-active transition-all placeholder:text-content-subtle"
                />
                <MapPin className="absolute left-3.5 top-3.5 w-5 h-5 text-content-subtle" />

                {destination && (
                  <button
                    type="button"
                    onClick={() => {
                      setDestination('');
                      if (onDestinationChange) onDestinationChange('');
                    }}
                    className="absolute right-3.5 top-3.5 text-content-subtle hover:text-content-main p-0.5 rounded-full"
                    title="Clear destination"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Optional Autocomplete Dropdown (Worldwide Free GeoNames Gazetteer) */}
              {showSuggestions && destination.trim().length >= 2 && (
                <div id="destination-autocomplete-dropdown" className="absolute left-0 right-0 top-full mt-1.5 bg-app-surface border border-edge-strong rounded-xl shadow-2xl py-1.5 z-50 max-h-64 overflow-y-auto animate-in fade-in duration-150">
                  {isSearchingDestinations ? (
                    <div className="px-3.5 py-3 text-xs text-content-muted flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-teal-600 dark:text-teal-400" />
                      <span>Searching worldwide destinations...</span>
                    </div>
                  ) : suggestions.length === 0 ? (
                    <div className="px-3.5 py-3 text-xs text-content-muted">
                      <div className="font-semibold text-content-main mb-0.5">No catalog match found</div>
                      <div className="text-[11px] text-content-subtle">
                        You can still type and plan a trip to "{destination}" anywhere in the world.
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="px-3 py-1 text-[10px] font-mono uppercase tracking-wider text-content-subtle border-b border-edge-subtle flex items-center justify-between">
                        <span>{searchFailed ? 'Offline Mode (Curated Places)' : `Worldwide Places (${suggestions.length})`}</span>
                        <span className="text-[9px] lowercase opacity-75 hidden sm:inline">Use ↑↓ keys & Enter</span>
                      </div>
                      {suggestions.map((item, idx) => (
                        <button
                          key={`${item.full_name}-${idx}`}
                          type="button"
                          onClick={() => handleSelectSuggestion(item.full_name)}
                          onMouseEnter={() => setHighlightedIndex(idx)}
                          className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between transition-colors cursor-pointer ${
                            highlightedIndex === idx
                              ? 'bg-teal-500/15 text-teal-700 dark:text-teal-300'
                              : 'hover:bg-app-elevated text-content-main'
                          }`}
                        >
                          <span className="flex items-center gap-2 min-w-0">
                            {item.place_type === 'country' ? (
                              <Globe className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                            ) : (
                              <MapPin className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
                            )}
                            <span className="truncate">
                              <span className="font-semibold text-content-main">{item.name}</span>
                              {item.region ? (
                                <span className="text-content-subtle ml-1.5 font-normal">
                                  {item.region}, {item.country}
                                </span>
                              ) : item.country && item.place_type !== 'country' ? (
                                <span className="text-content-subtle ml-1.5 font-normal">
                                  {item.country}
                                </span>
                              ) : null}
                            </span>
                          </span>
                          <span className="flex items-center gap-1.5 shrink-0 ml-2">
                            {item.place_type && (
                              <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase bg-app-elevated text-content-subtle border border-edge-subtle">
                                {item.place_type}
                              </span>
                            )}
                            <span className="text-[10px] text-content-subtle font-mono hidden sm:inline">Select</span>
                          </span>
                        </button>
                      ))}
                      <div className="px-3 py-1 text-[9px] text-content-subtle border-t border-edge-subtle text-right bg-app-elevated/30">
                        GeoNames Index (CC BY 4.0)
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Quick Pick Chips */}
              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-medium text-content-subtle">{t('planner.popular')}</span>
                {['Manali', 'Goa', 'Bali', 'Kyoto', 'Paris', 'Swiss Alps'].map((place) => (
                  <button
                    key={place}
                    type="button"
                    onClick={() => handleSelectSuggestion(place)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${
                      destination.toLowerCase().includes(place.toLowerCase())
                        ? 'bg-teal-600 text-white border-teal-600 font-semibold shadow-xs'
                        : 'bg-app-elevated hover:bg-app-surface text-content-muted border-edge-subtle'
                    }`}
                  >
                    {place}
                  </button>
                ))}
              </div>
            </div>

            {/* 2. Travel Dates Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="startDate" className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                  {t('planner.departureLabel')}
                </label>
                <input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-sm text-content-main bg-app-input border border-edge-strong rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-edge-active transition-all"
                />
              </div>

              <div>
                <label htmlFor="endDate" className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                  {t('planner.returnLabel')}
                </label>
                <input
                  id="endDate"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 text-sm text-content-main bg-app-input border border-edge-strong rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-edge-active transition-all"
                />
              </div>

              {tripDays !== null && tripDays > 0 && (
                <div className="sm:col-span-2 bg-teal-500/10 border border-teal-500/30 rounded-xl px-4 py-2 text-xs font-medium text-teal-700 dark:text-teal-300 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  <span>{t('planner.durationNotice', { days: tripDays })}</span>
                </div>
              )}
            </div>

            {/* 3. Budget Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-2 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                {t('planner.budgetLabel')}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {BUDGET_KEYS.map((opt) => {
                  const isSelected = budget === opt.id;
                  const label = t(`planner.budgetOptions.${opt.id}.label`);
                  const desc = t(`planner.budgetOptions.${opt.id}.desc`);
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setBudget(opt.id)}
                      className={`text-left p-3.5 rounded-2xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'border-teal-600 dark:border-teal-400 bg-teal-500/10 shadow-xs ring-1 ring-teal-500/30'
                          : 'border-edge-subtle bg-app-elevated/40 hover:bg-app-elevated'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-content-main text-xs">{label}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isSelected ? 'bg-teal-600 text-white' : 'bg-app-elevated text-content-muted border border-edge-subtle'
                        }`}>
                          {opt.tier}
                        </span>
                      </div>
                      <p className="text-[11px] text-content-subtle leading-tight">{desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Step 1 Actions */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleNextToStep2}
                className="w-full py-3.5 px-6 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm tracking-wide shadow-md shadow-teal-600/25 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>{t('planner.wizard.continueBtn')}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* STEP 2: Travelers, Interests & Pace                       */}
        {/* ========================================================= */}
        {currentStep === 2 && (
          <div className="p-6 sm:p-8 space-y-6 animate-in fade-in duration-200">
            {/* 1. Travellers & Group Type */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-2 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                {t('planner.travelersLabel')}
              </label>
              <div className="flex flex-wrap items-center gap-2 mb-2.5">
                {[
                  { id: 'solo', defaultCount: 1 },
                  { id: 'couple', defaultCount: 2 },
                  { id: 'family', defaultCount: 4 },
                  { id: 'friends', defaultCount: 4 },
                ].map((type) => (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => {
                      setTravelerType(type.id);
                      setTravelersCount(type.defaultCount);
                    }}
                    className={`py-2 px-3.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                      travelerType === type.id
                        ? 'border-teal-600 bg-teal-600 text-white shadow-xs'
                        : 'border-edge-subtle bg-app-elevated/50 text-content-muted hover:bg-app-elevated'
                    }`}
                  >
                    {t(`planner.travelerTypes.${type.id}`)}
                  </button>
                ))}

                {/* Exact Count Stepper */}
                <div className="flex items-center gap-2 bg-app-input border border-edge-strong rounded-xl px-3 py-1.5 ml-auto">
                  <span className="text-[11px] text-content-subtle font-medium">{t('planner.travelersCount')}</span>
                  <button
                    type="button"
                    onClick={() => setTravelersCount(Math.max(1, travelersCount - 1))}
                    className="w-6 h-6 rounded-lg bg-app-elevated border border-edge-subtle flex items-center justify-center text-content-main font-bold hover:bg-app-surface text-xs"
                  >
                    -
                  </button>
                  <span className="text-xs font-bold text-content-main w-4 text-center">{travelersCount}</span>
                  <button
                    type="button"
                    onClick={() => setTravelersCount(Math.min(20, travelersCount + 1))}
                    className="w-6 h-6 rounded-lg bg-app-elevated border border-edge-subtle flex items-center justify-center text-content-main font-bold hover:bg-app-surface text-xs"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>

            {/* 2. Interests Multi-Select */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-2 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                {t('planner.interestsLabel')}
              </label>
              <div className="flex flex-wrap gap-2">
                {INTEREST_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const isSelected = selectedInterests.includes(item.id);
                  const label = t(`planner.interests.${item.id}`);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => toggleInterest(item.id)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all cursor-pointer ${
                        isSelected
                          ? 'border-teal-600 bg-teal-500/10 text-teal-700 dark:text-teal-300 font-semibold shadow-xs ring-1 ring-teal-500/30'
                          : 'border-edge-subtle bg-app-elevated/40 text-content-muted hover:bg-app-elevated'
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-teal-600 dark:text-teal-400' : 'text-content-subtle'}`} />
                      <span>{label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 3. Travel Pace */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-content-muted mb-2 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                {t('planner.paceLabel')}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {['relaxed', 'balanced', 'packed'].map((pKey) => {
                  const isSelected = pace === pKey;
                  const label = t(`planner.paceOptions.${pKey}.label`);
                  const desc = t(`planner.paceOptions.${pKey}.desc`);
                  return (
                    <button
                      key={pKey}
                      type="button"
                      onClick={() => setPace(pKey)}
                      className={`p-2.5 text-center rounded-xl border text-xs font-medium transition-all cursor-pointer ${
                        isSelected
                          ? 'border-teal-600 bg-teal-500/10 text-teal-700 dark:text-teal-300 font-bold ring-1 ring-teal-500/30'
                          : 'border-edge-subtle bg-app-elevated/40 text-content-muted hover:bg-app-elevated'
                      }`}
                    >
                      <div>{label}</div>
                      <div className="text-[10px] text-content-subtle font-normal mt-0.5">{desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Step 2 Actions */}
            <div className="pt-2 flex items-center gap-3">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="py-3 px-4 rounded-xl border border-edge-subtle bg-app-elevated hover:bg-app-surface text-content-muted font-semibold text-xs tracking-wide transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>{t('planner.wizard.backBtn')}</span>
              </button>
              <button
                type="button"
                onClick={handleNextToStep3}
                className="flex-1 py-3.5 px-6 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm tracking-wide shadow-md shadow-teal-600/25 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>{t('planner.wizard.continueToReview')}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* STEP 3: Review & Generate Itinerary                       */}
        {/* ========================================================= */}
        {currentStep === 3 && (
          <div className="p-6 sm:p-8 space-y-6 animate-in fade-in duration-200">
            <div className="bg-app-elevated/60 border border-edge-subtle rounded-2xl p-4 sm:p-5">
              <div className="flex items-center justify-between pb-3 border-b border-edge-subtle">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                  <span className="font-bold text-base text-content-main">{destination}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="text-xs text-teal-600 dark:text-teal-400 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>Edit Destination / Dates</span>
                </button>
              </div>

              {/* Data Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 text-xs">
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Duration</span>
                  <span className="font-semibold text-content-main">{tripDays} Days</span>
                </div>
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Dates</span>
                  <span className="font-semibold text-content-main">
                    {formatLocaleDate(startDate, i18n.language)} – {formatLocaleDate(endDate, i18n.language)}
                  </span>
                </div>
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Budget</span>
                  <span className="font-semibold text-teal-600 dark:text-teal-400 capitalize">
                    {t(`planner.budgetOptions.${budget}.label`)}
                  </span>
                </div>
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Travelers</span>
                  <span className="font-semibold text-content-main">
                    {travelersCount} ({t(`planner.travelerTypes.${travelerType}`)})
                  </span>
                </div>
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Pace</span>
                  <span className="font-semibold text-content-main capitalize">{pace}</span>
                </div>
                <div className="col-span-2 sm:col-span-3">
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Target AI Language</span>
                  <span className="font-semibold text-teal-600 dark:text-teal-400">
                    {LANGUAGE_OPTIONS.find((l) => l.code === i18n.language)?.native} ({i18n.language.toUpperCase()})
                  </span>
                </div>
              </div>

              <div className="pt-3 mt-3 border-t border-edge-subtle flex flex-wrap gap-1.5 items-center">
                <span className="text-[11px] text-content-subtle font-medium">Interests:</span>
                {selectedInterests.map((id) => (
                  <span key={id} className="text-[10px] px-2 py-0.5 rounded-md bg-teal-500/10 text-teal-700 dark:text-teal-300 border border-teal-500/20 font-medium">
                    {t(`planner.interests.${id}`)}
                  </span>
                ))}
              </div>
            </div>

            {/* Notice about Groq / FastAPI integration */}
            <div className="p-3 rounded-xl bg-app-elevated border border-edge-subtle text-xs text-content-subtle leading-relaxed flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
              <span>
                Ready to synthesize day-by-day routes and Unsplash photography via our Python FastAPI Groq pipeline.
              </span>
            </div>

            {/* Step 3 Actions */}
            <div className="pt-1 flex items-center gap-3">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="py-3 px-4 rounded-xl border border-edge-subtle bg-app-elevated hover:bg-app-surface text-content-muted font-semibold text-xs tracking-wide transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>{t('planner.wizard.backBtn')}</span>
              </button>
              <button
                type="button"
                disabled={isGenerating}
                onClick={handleFinalSubmit}
                className="flex-1 py-4 px-6 rounded-xl bg-gradient-to-r from-teal-600 via-teal-500 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-bold text-sm tracking-wide shadow-lg shadow-teal-600/30 hover:shadow-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-75 disabled:cursor-wait"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Synthesizing with Groq AI...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate Itinerary with Groq AI</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Loading State Banner */}
        {isGenerating && (
          <div className="border-t border-edge-subtle bg-slate-900/90 text-white p-6 sm:p-8 animate-in fade-in duration-300">
            <div className="flex flex-col items-center justify-center text-center py-4 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
              <h3 className="text-base font-bold text-white font-editorial">
                Consulting Groq LLaMA 3.3 for {destination}...
              </h3>
              <p className="text-xs text-slate-300 max-w-md leading-relaxed">
                Analyzing regional culture, daily routes, {budget} budget tier, and {pace} pace via our FastAPI backend pipeline.
              </p>
            </div>
          </div>
        )}

        {/* Error Notice Banner */}
        {generationError && !isGenerating && (
          <div className="border-t border-rose-500/30 bg-rose-950/40 text-white p-5 sm:p-6 animate-in fade-in">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1.5 flex-1 text-xs">
                <h4 className="font-bold text-sm text-rose-200">Connection Notice</h4>
                <p className="text-slate-300">{generationError}</p>
                <p className="text-[11px] text-slate-400">
                  Ensure the FastAPI backend is running on <code className="bg-rose-500/20 px-1 py-0.5 rounded text-rose-200">http://localhost:8000</code>.
                </p>
                <button
                  type="button"
                  onClick={handleFinalSubmit}
                  className="mt-2 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry Generation</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Validated Itinerary Results View */}
        {generatedItinerary && !isGenerating && (
          <div className="border-t border-edge-subtle bg-slate-900 text-white p-6 sm:p-8 animate-in fade-in duration-300 space-y-6">

            {/* Header & Source Badge */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wide flex items-center gap-1.5 ${
                    generatedItinerary.is_mock
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }`}>
                    {generatedItinerary.is_mock ? (
                      <>
                        <Compass className="w-3 h-3" />
                        <span>Fallback Preview (Mock Generator)</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3 h-3" />
                        <span>Live Groq AI (LLaMA 3.3 70B)</span>
                      </>
                    )}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {generatedItinerary.language.toUpperCase()} • {generatedItinerary.duration_days} Days
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold font-editorial text-white">
                  {generatedItinerary.destination}
                </h3>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {generatedItinerary.estimated_total_cost && (
                  <div className="bg-slate-800/80 border border-slate-700 px-3.5 py-1.5 rounded-xl text-right">
                    <span className="text-[9px] text-slate-400 uppercase tracking-wider block font-semibold">Total Budget</span>
                    <span className="text-xs sm:text-sm font-bold text-teal-400">{generatedItinerary.estimated_total_cost}</span>
                  </div>
                )}

                <button
                  type="button"
                  onClick={handleSaveTrip}
                  disabled={isSaving}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                    isSaved
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-teal-600 hover:bg-teal-700 text-white shadow-sm'
                  }`}
                  title="Save to local SQLite database (100% Free)"
                >
                  {isSaved ? <Check className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                  <span>{isSaved ? 'Saved Locally' : 'Save Itinerary'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
                  title="Print or export to PDF"
                >
                  <Printer className="w-3.5 h-3.5 text-teal-400" />
                  <span className="hidden sm:inline">Print / PDF</span>
                </button>
              </div>
            </div>

            {/* AI Status / Notification Banner if fallback triggered */}
            {generatedItinerary.is_mock && generatedItinerary.summary.startsWith('[AI') && (
              <div className="bg-amber-500/15 border border-amber-500/30 rounded-xl p-3 flex items-start gap-2.5 text-xs text-amber-200">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block text-[11px] text-amber-300">Live AI Notification</span>
                  <p className="text-[11px] text-amber-100/90">
                    Groq AI is running in adaptive fallback mode. A complete verified itinerary has been generated for your trip.
                  </p>
                </div>
              </div>
            )}

            {/* Itinerary Summary */}
            <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4 text-xs text-slate-200 leading-relaxed">
              <p>{generatedItinerary.summary}</p>
            </div>

            {/* Budget Breakdown (if provided) */}
            {generatedItinerary.budget_breakdown && (
              <div className="space-y-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-teal-400" />
                  <span>Estimated Cost Breakdown ({generatedItinerary.budget_tier} Tier)</span>
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="bg-slate-800/60 border border-slate-700/60 p-2.5 rounded-xl">
                    <span className="text-[10px] text-slate-400 block font-semibold">Lodging</span>
                    <span className="text-xs font-bold text-teal-300">{generatedItinerary.budget_breakdown.accommodation || 'Variable'}</span>
                  </div>
                  <div className="bg-slate-800/60 border border-slate-700/60 p-2.5 rounded-xl">
                    <span className="text-[10px] text-slate-400 block font-semibold">Food & Dining</span>
                    <span className="text-xs font-bold text-teal-300">{generatedItinerary.budget_breakdown.food_and_dining || 'Variable'}</span>
                  </div>
                  <div className="bg-slate-800/60 border border-slate-700/60 p-2.5 rounded-xl">
                    <span className="text-[10px] text-slate-400 block font-semibold">Sightseeing & Entry</span>
                    <span className="text-xs font-bold text-teal-300">{generatedItinerary.budget_breakdown.activities_and_entry || 'Variable'}</span>
                  </div>
                  <div className="bg-slate-800/60 border border-slate-700/60 p-2.5 rounded-xl">
                    <span className="text-[10px] text-slate-400 block font-semibold">Local Transit</span>
                    <span className="text-xs font-bold text-teal-300">{generatedItinerary.budget_breakdown.local_transport || 'Variable'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Accommodation Recommendations (Skill Wallet Specification) */}
            {generatedItinerary.accommodation_suggestions?.length > 0 && (
              <div className="space-y-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Hotel className="w-3.5 h-3.5 text-teal-400" />
                  <span>Curated Accommodation Suggestions ({generatedItinerary.budget_tier} Tier)</span>
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {generatedItinerary.accommodation_suggestions.map((stay, idx) => (
                    <div key={idx} className="bg-slate-800/60 border border-slate-700/60 p-3 rounded-xl flex items-start gap-2.5">
                      <Bed className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                      <span className="text-xs text-slate-200 leading-snug">{stay}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Day by Day Accordion */}
            <div className="space-y-3 pt-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-teal-400" />
                <span>Day-by-Day Route & Activities</span>
              </span>

              <div className="space-y-2.5">
                {generatedItinerary.days.map((day) => {
                  const isExpanded = expandedDay === day.day_number;
                  const isRegenerating = regeneratingDay === day.day_number;
                  return (
                    <div
                      key={day.day_number}
                      className="border border-slate-700 rounded-xl overflow-hidden bg-slate-800/40 transition-colors print:border-slate-300 print:bg-white print-avoid-break"
                    >
                      <div
                        onClick={() => setExpandedDay(isExpanded ? null : day.day_number)}
                        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-slate-800/80 transition-colors cursor-pointer print:bg-slate-100 print:text-slate-900"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="w-6 h-6 rounded-md bg-teal-600 text-white flex items-center justify-center text-xs font-bold">
                            {day.day_number}
                          </span>
                          <span className="text-xs sm:text-sm font-bold text-slate-100 print:text-slate-900">
                            {day.theme}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 text-slate-400">
                          <button
                            type="button"
                            disabled={isRegenerating}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRegenerateDay(day.day_number);
                            }}
                            className="px-2 py-1 rounded-md bg-slate-700/70 hover:bg-teal-600 text-slate-200 hover:text-white transition-colors cursor-pointer text-[10px] font-semibold flex items-center gap-1 print:hidden"
                            title="Regenerate this specific day with alternative activities"
                          >
                            <RefreshCw className={`w-3 h-3 ${isRegenerating ? 'animate-spin text-teal-400' : ''}`} />
                            <span className="hidden sm:inline">Regenerate</span>
                          </button>
                          <span className="text-[10px] hidden sm:inline">{day.activities.length} recommendations</span>
                          {isExpanded ? <ChevronUp className="w-4 h-4 print:hidden" /> : <ChevronDown className="w-4 h-4 print:hidden" />}
                        </div>
                      </div>

                      <div className={`p-4 pt-2 border-t border-slate-700/60 space-y-3 bg-slate-900/60 print:bg-white print:border-slate-300 ${isExpanded ? 'block' : 'hidden print:block'}`}>
                          {day.activities.map((act, actIdx) => (
                            <div
                              key={actIdx}
                              className="p-3 rounded-lg bg-slate-800/70 border border-slate-700/50 space-y-2 text-xs"
                            >
                              <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2">
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-teal-500/20 text-teal-300">
                                    {act.time_of_day}
                                  </span>
                                  <h4 className="font-bold text-slate-100 text-xs sm:text-sm">
                                    {act.title}
                                  </h4>
                                </div>
                                <div className="flex items-center gap-2">
                                  {act.estimated_cost && (
                                    <span className="text-[11px] text-teal-300 font-semibold shrink-0">
                                      {act.estimated_cost}
                                    </span>
                                  )}
                                  <button
                                    type="button"
                                    onClick={() => setEditingActivity({
                                      dayNumber: day.day_number,
                                      actIdx,
                                      title: act.title,
                                      description: act.description,
                                      location: act.location || '',
                                      attraction: act.attraction || '',
                                      food_option: act.food_option || '',
                                      estimated_cost: act.estimated_cost || ''
                                    })}
                                    className="p-1 rounded text-slate-400 hover:text-teal-300 hover:bg-slate-700/50 transition-colors cursor-pointer"
                                    title="Edit activity"
                                  >
                                    <Edit3 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>

                              <p className="text-slate-300 leading-relaxed text-[11px]">
                                {act.description}
                              </p>

                              {(act.attraction || act.food_option || act.location) && (
                                <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-700/40 text-[10px]">
                                  {act.location && (
                                    <span className="flex items-center gap-1 text-slate-400">
                                      <MapPin className="w-3 h-3 text-teal-400" />
                                      <span>{act.location}</span>
                                    </span>
                                  )}
                                  {act.attraction && (
                                    <span className="flex items-center gap-1 text-slate-300">
                                      <Landmark className="w-3 h-3 text-amber-400" />
                                      <span>{act.attraction}</span>
                                    </span>
                                  )}
                                  {act.food_option && (
                                    <span className="flex items-center gap-1 text-slate-300">
                                      <Utensils className="w-3 h-3 text-emerald-400" />
                                      <span>{act.food_option}</span>
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Travel Tips & Commuting */}
            {(generatedItinerary.travel_tips?.length > 0 || generatedItinerary.transport_suggestions?.length > 0) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                {generatedItinerary.travel_tips?.length > 0 && (
                  <div className="bg-slate-800/60 border border-slate-700/60 p-3.5 rounded-xl space-y-2">
                    <span className="font-bold text-[11px] text-teal-300 flex items-center gap-1.5 uppercase tracking-wider">
                      <Lightbulb className="w-3.5 h-3.5" />
                      <span>Local Tips & Etiquette</span>
                    </span>
                    <ul className="space-y-1.5 text-slate-300 text-[11px]">
                      {generatedItinerary.travel_tips.map((tip, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <Check className="w-3 h-3 text-teal-400 shrink-0 mt-0.5" />
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {generatedItinerary.transport_suggestions?.length > 0 && (
                  <div className="bg-slate-800/60 border border-slate-700/60 p-3.5 rounded-xl space-y-2">
                    <span className="font-bold text-[11px] text-teal-300 flex items-center gap-1.5 uppercase tracking-wider">
                      <Bus className="w-3.5 h-3.5" />
                      <span>Transit & Commuting</span>
                    </span>
                    <ul className="space-y-1.5 text-slate-300 text-[11px]">
                      {generatedItinerary.transport_suggestions.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <Compass className="w-3 h-3 text-teal-400 shrink-0 mt-0.5" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Estimates & Real-time Booking Disclaimer (Skill Wallet Specification) */}
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-start gap-3 text-xs text-amber-200/90 leading-relaxed">
              <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-bold uppercase tracking-wider text-[10px] text-amber-300 block">
                  Pricing & Availability Disclaimer
                </span>
                <p className="text-[11px] text-amber-100/80">
                  {generatedItinerary.disclaimer || "Prices, opening hours, and transport schedules are estimates based on standard regional rates and may vary seasonally. Real-time availability must be verified directly with providers. Live bookings are not confirmed."}
                </p>
              </div>
            </div>

            {/* Reset / Edit Action */}
            <div className="pt-2 flex items-center justify-between border-t border-slate-800 text-xs">
              <span className="text-slate-400">Want to explore another destination or adjust dates?</span>
              <button
                type="button"
                onClick={() => {
                  setGeneratedItinerary(null);
                  setCurrentStep(1);
                }}
                className="text-teal-400 hover:text-teal-300 underline font-semibold cursor-pointer"
              >
                Modify Trip Parameters
              </button>
            </div>

          </div>
        )}

        {/* Activity Edit Modal */}
        {editingActivity && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 text-white">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-teal-400" />
                  <h3 className="font-bold text-base text-white">Edit Activity (Day {editingActivity.dayNumber})</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setEditingActivity(null)}
                  className="p-1 text-slate-400 hover:text-white rounded-lg cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSaveActivityEdit} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Title</label>
                  <input
                    type="text"
                    value={editingActivity.title}
                    onChange={(e) => setEditingActivity({ ...editingActivity, title: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-hidden focus:border-teal-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Description</label>
                  <textarea
                    rows={3}
                    value={editingActivity.description}
                    onChange={(e) => setEditingActivity({ ...editingActivity, description: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-hidden focus:border-teal-500 resize-none"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Attraction</label>
                    <input
                      type="text"
                      value={editingActivity.attraction}
                      onChange={(e) => setEditingActivity({ ...editingActivity, attraction: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-hidden focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Food / Dining</label>
                    <input
                      type="text"
                      value={editingActivity.food_option}
                      onChange={(e) => setEditingActivity({ ...editingActivity, food_option: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-hidden focus:border-teal-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Location / District</label>
                    <input
                      type="text"
                      value={editingActivity.location}
                      onChange={(e) => setEditingActivity({ ...editingActivity, location: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-hidden focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Estimated Cost</label>
                    <input
                      type="text"
                      value={editingActivity.estimated_cost}
                      onChange={(e) => setEditingActivity({ ...editingActivity, estimated_cost: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-hidden focus:border-teal-500"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setEditingActivity(null)}
                    className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold cursor-pointer"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Saved Trips Modal */}
        {showSavedModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 text-white">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <FolderHeart className="w-5 h-5 text-teal-400" />
                  <h3 className="font-bold text-base text-white">Saved Itineraries (Local SQLite DB)</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setShowSavedModal(false)}
                  className="p-1 text-slate-400 hover:text-white rounded-lg cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {savedTrips.length === 0 ? (
                <div className="py-8 text-center text-slate-400 space-y-2">
                  <Bookmark className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-sm font-semibold">No Saved Itineraries Yet</p>
                  <p className="text-xs text-slate-500">
                    Generate an itinerary and click "Save Itinerary" to store it locally in your free SQLite database.
                  </p>
                </div>
              ) : (
                <div className="max-h-80 overflow-y-auto space-y-2.5 pr-1">
                  {savedTrips.map((record) => (
                    <div
                      key={record.id}
                      className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-between gap-3 hover:border-teal-500/50 transition-colors"
                    >
                      <div>
                        <h4 className="font-bold text-sm text-white">{record.destination}</h4>
                        <p className="text-[11px] text-slate-400">
                          {record.duration_days} Days • {record.created_at ? record.created_at.split('T')[0] : 'Saved'}
                        </p>
                        <span className="text-[10px] text-teal-400 font-semibold block mt-0.5">
                          {record.itinerary_data.estimated_total_cost || 'Budget: ' + record.itinerary_data.budget_tier}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => handleLoadSavedTrip(record)}
                          className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition-colors cursor-pointer"
                        >
                          Load
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteTrip(record.id, e)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
                          title="Delete saved trip"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 text-center">
                Stored locally in <code className="text-teal-300">backend/data/tripgenie.db</code> (100% Free, zero external setup).
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
