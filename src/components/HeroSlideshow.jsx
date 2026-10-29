import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Compass, Sparkles, MapPin, Calendar, Clock, ChevronRight, Pause, Play } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { CURATED_DESTINATIONS } from '../data/destinations';
import TripPlannerForm from './TripPlannerForm';

export default function HeroSlideshow({ onDestinationSelect }) {
  const { t } = useTranslation();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  const activeDest = CURATED_DESTINATIONS[currentIndex];

  // Auto-advance slideshow with reduced-motion check
  useEffect(() => {
    if (!isPlaying) return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % CURATED_DESTINATIONS.length);
    }, 9000); // 9-second slow cinematic rhythm

    return () => clearInterval(timer);
  }, [isPlaying]);

  const handleSelectDestination = (index) => {
    setCurrentIndex(index);
    if (onDestinationSelect) {
      onDestinationSelect(CURATED_DESTINATIONS[index].fullQuery);
    }
  };

  const handleFormDestinationChange = (query) => {
    const foundIndex = CURATED_DESTINATIONS.findIndex(
      (d) => query.toLowerCase().includes(d.name.toLowerCase()) || d.fullQuery.toLowerCase().includes(query.toLowerCase())
    );
    if (foundIndex !== -1 && foundIndex !== currentIndex) {
      setCurrentIndex(foundIndex);
    }
  };

  return (
    <section className="relative min-h-screen flex flex-col justify-between overflow-hidden">
      {/* 1. Cinematic Background Layer with Ken Burns Zoom */}
      <div className="absolute inset-0 -z-20 overflow-hidden bg-slate-950">
        <AnimatePresence mode="sync">
          <motion.div
            key={activeDest.id}
            initial={{ opacity: 0, scale: 1.0 }}
            animate={{ opacity: 1, scale: 1.06 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.8, ease: [0.16, 1, 0.3, 1] }}
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${activeDest.heroImage})` }}
            aria-hidden="true"
          />
        </AnimatePresence>
      </div>

      {/* 2. Layered Vignette & Theme-Adaptive Contrast Gradient */}
      <div
        className="absolute inset-0 -z-10 pointer-events-none transition-colors duration-300"
        style={{ background: 'var(--hero-overlay)' }}
      />

      {/* 3. Main Hero Content & Layered Planner Composition */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 lg:pt-32 w-full flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">

          {/* Left Column: Editorial Destination Storytelling */}
          <div className="lg:col-span-6 space-y-6 text-white drop-shadow-sm">
            {/* Project / Atelier Kicker */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-teal-300 text-xs font-semibold uppercase tracking-widest">
              <Sparkles className="w-3.5 h-3.5 text-teal-300" />
              <span>Skill Wallet • Generative AI with Google Cloud</span>
            </div>

            {/* Dynamic Destination Kicker & Title */}
            <div>
              <span className="text-xs uppercase tracking-widest text-teal-200/90 font-mono block mb-1">
                {activeDest.kicker}
              </span>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-editorial text-white tracking-tight leading-[1.08] mb-3">
                {activeDest.title}
              </h1>
              <p className="text-base sm:text-lg text-slate-200/90 max-w-xl leading-relaxed font-normal">
                {activeDest.tagline}
              </p>
            </div>

            {/* Curated Field Badges */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs pt-1">
              <div className="px-3 py-1.5 rounded-lg bg-black/35 backdrop-blur-md border border-white/15 text-slate-200 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-teal-400" />
                <span className="font-semibold">{activeDest.name}, {activeDest.country}</span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-black/35 backdrop-blur-md border border-white/15 text-slate-200 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-amber-400" />
                <span>Season: {activeDest.bestSeason}</span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-black/35 backdrop-blur-md border border-white/15 text-slate-200 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                <span>Pace: {activeDest.suggestedDuration}</span>
              </div>
            </div>

            {/* Key Curated Highlights */}
            <div className="pt-2 hidden sm:block">
              <span className="text-[11px] uppercase tracking-wider text-teal-200/80 font-mono block mb-2">
                Field Highlights
              </span>
              <div className="flex flex-wrap gap-2">
                {activeDest.curatedHighlights.map((hl) => (
                  <span
                    key={hl}
                    className="text-xs px-2.5 py-1 rounded-md bg-white/10 backdrop-blur-sm border border-white/15 text-slate-100"
                  >
                    • {hl}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Prominently Layered Trip Planner */}
          <div className="lg:col-span-6 relative z-10">
            <TripPlannerForm
              currentDestinationQuery={activeDest.fullQuery}
              onDestinationChange={handleFormDestinationChange}
            />
          </div>

        </div>
      </div>

      {/* 4. Bottom Destination Slideshow Navigation Bar */}
      <div className="w-full bg-black/40 backdrop-blur-md border-t border-white/10 py-3 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">

          {/* Pause / Play Toggle */}
          <button
            type="button"
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-slate-300 hover:text-white px-2.5 py-1 rounded-md bg-white/5 border border-white/10 transition-colors"
            title={isPlaying ? 'Pause background rotation' : 'Resume background rotation'}
          >
            {isPlaying ? <Pause className="w-3 h-3 text-teal-400" /> : <Play className="w-3 h-3 text-amber-400" />}
            <span className="hidden sm:inline">{isPlaying ? 'Autoplay On' : 'Paused'}</span>
          </button>

          {/* Slide Selection Chips */}
          <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto no-scrollbar py-1">
            {CURATED_DESTINATIONS.map((dest, idx) => {
              const isActive = idx === currentIndex;
              return (
                <button
                  key={dest.id}
                  type="button"
                  onClick={() => handleSelectDestination(idx)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-all whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'bg-teal-600 text-white font-bold shadow-md ring-1 ring-white/30'
                      : 'bg-white/10 hover:bg-white/20 text-slate-200 border border-white/10'
                  }`}
                >
                  <span className="font-mono text-[10px] text-teal-200">0{idx + 1}</span>
                  <span className="tracking-wide">{dest.name}</span>
                </button>
              );
            })}
          </div>

          {/* Slide Counter */}
          <div className="text-xs font-mono text-slate-400 hidden md:block">
            <span className="text-teal-400 font-bold">0{currentIndex + 1}</span> / 0{CURATED_DESTINATIONS.length}
          </div>

        </div>
      </div>
    </section>
  );
}
