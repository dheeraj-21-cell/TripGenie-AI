import React, { useState } from 'react';
import { Sparkles, MapPin, Compass, ShieldCheck, Zap, Globe, Compass as CompassIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { CURATED_DESTINATIONS } from '../data/destinations';
import TripPlannerForm from './TripPlannerForm';

export default function HeroSection({ selectedDestination, onDestinationSelect }) {
  const { t } = useTranslation();
  const [activeDestIndex, setActiveDestIndex] = useState(0);
  const [userTypedPlace, setUserTypedPlace] = useState('');

  const activeDest = CURATED_DESTINATIONS[activeDestIndex];

  const handleDestinationChange = (typedQuery) => {
    setUserTypedPlace(typedQuery);
    const foundIndex = CURATED_DESTINATIONS.findIndex(
      (d) =>
        typedQuery.toLowerCase().includes(d.name.toLowerCase()) ||
        d.fullQuery.toLowerCase().includes(typedQuery.toLowerCase())
    );
    if (foundIndex !== -1) {
      setActiveDestIndex(foundIndex);
    }
    if (onDestinationSelect) {
      onDestinationSelect(typedQuery);
    }
  };

  const handlePillClick = (dest) => {
    setUserTypedPlace(dest.fullQuery);
    const idx = CURATED_DESTINATIONS.findIndex((d) => d.id === dest.id);
    if (idx !== -1) setActiveDestIndex(idx);
    if (onDestinationSelect) onDestinationSelect(dest.fullQuery);
  };

  return (
    <section className="relative min-h-[calc(100vh-4.5rem)] flex items-center py-8 lg:py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">

        {/* Balanced Full-Width Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">

          {/* ========================================================= */}
          {/* LEFT SECTION (5 Cols): Editorial Storytelling & Visuals   */}
          {/* ========================================================= */}
          <div className="lg:col-span-5 space-y-6 text-white pt-2">

            {/* Program Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 dark:bg-black/40 backdrop-blur-md border border-white/20 text-teal-300 text-xs font-semibold uppercase tracking-wider shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-teal-300" />
              <span>Skill Wallet • GenAI with Google Cloud</span>
            </div>

            {/* Editorial Headline */}
            <div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-editorial text-white tracking-tight leading-[1.12] mb-3">
                {t('hero.titlePrefix')}{' '}
                <span className="bg-gradient-to-r from-teal-300 to-emerald-200 bg-clip-text text-transparent underline decoration-teal-400/40 decoration-wavy">
                  {t('hero.titleHighlight')}
                </span>{' '}
                {t('hero.titleSuffix')}
              </h1>
              <p className="text-sm sm:text-base text-slate-200/90 leading-relaxed font-normal">
                {t('hero.subtitle')}
              </p>
            </div>

            {/* Live Destination Spotlight Card */}
            <div className="bg-white/10 dark:bg-black/40 backdrop-blur-md border border-white/15 rounded-2xl p-4 sm:p-5 shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-widest text-teal-300 font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
                  {userTypedPlace && !activeDest.name.toLowerCase().includes(userTypedPlace.toLowerCase())
                    ? 'Custom Explorer Spotlight'
                    : 'Curated Region Spotlight'}
                </span>
                <span className="text-xs text-slate-300 font-medium font-mono">
                  {activeDest.suggestedDuration}
                </span>
              </div>

              <div>
                <h3 className="text-xl font-bold font-editorial text-white">
                  {userTypedPlace ? userTypedPlace : `${activeDest.name}, ${activeDest.country}`}
                </h3>
                <p className="text-xs text-slate-200/80 leading-relaxed mt-0.5">
                  {activeDest.tagline}
                </p>
              </div>

              {/* Small Destination Visual Snapshot Pills */}
              <div className="pt-1">
                <span className="text-[10px] uppercase font-mono tracking-wider text-slate-300 block mb-2">
                  Trip Highlights & Atmosphere
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {activeDest.curatedHighlights.map((hl) => (
                    <span
                      key={hl}
                      className="text-xs px-2.5 py-1 rounded-md bg-white/10 border border-white/15 text-slate-100 flex items-center gap-1"
                    >
                      <span className="text-teal-300">•</span>
                      <span>{hl}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Destination Switcher Pills */}
              <div className="pt-2 border-t border-white/10 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                <span className="text-[10px] uppercase font-mono text-slate-300 shrink-0">Sample:</span>
                {CURATED_DESTINATIONS.map((d, idx) => (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => handlePillClick(d)}
                    className={`text-[11px] px-2.5 py-1 rounded-md transition-all shrink-0 cursor-pointer ${
                      idx === activeDestIndex
                        ? 'bg-teal-500 text-white font-bold'
                        : 'bg-white/10 text-slate-300 hover:bg-white/20'
                    }`}
                  >
                    {d.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Platform Feature Trust Pills */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-200">
              <div className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/15 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-300" />
                <span>{t('hero.groqPill')}</span>
              </div>
              <div className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/15 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-teal-300" />
                <span>{t('hero.unsplashPill')}</span>
              </div>
              <div className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/15 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-300" />
                <span>{t('hero.supabasePill')}</span>
              </div>
            </div>

          </div>

          {/* ========================================================= */}
          {/* RIGHT SECTION (7 Cols): The 3-Step Wizard Planner Form    */}
          {/* ========================================================= */}
          <div className="lg:col-span-7 w-full relative z-10">
            <TripPlannerForm
              initialDestination="Manali, India"
              externalDestination={userTypedPlace || selectedDestination}
              onDestinationChange={handleDestinationChange}
            />
          </div>

        </div>

      </div>
    </section>
  );
}
