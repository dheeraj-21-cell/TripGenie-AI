import React from 'react';
import { motion } from 'motion/react';
import { Compass, MapPin, Calendar, Clock, DollarSign, ArrowUpRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { CURATED_DESTINATIONS } from '../data/destinations';

export default function EditorialDestinations({ onSelectDestination }) {
  const { t } = useTranslation();

  const handlePick = (fullQuery) => {
    if (onSelectDestination) {
      onSelectDestination(fullQuery);
    }
    const plannerElement = document.getElementById('planner');
    if (plannerElement) {
      plannerElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const lead = CURATED_DESTINATIONS[0]; // Kyoto
  const secondary = [CURATED_DESTINATIONS[1], CURATED_DESTINATIONS[2]]; // Amalfi, Zermatt

  return (
    <section id="destinations" className="py-24 bg-app-base border-t border-edge-subtle transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Editorial Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400 font-mono block mb-2">
              Curated Field Archives
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-editorial text-content-main tracking-tight">
              Remarkable Expeditions, Rooted in Place
            </h2>
          </div>
          <p className="max-w-md text-sm text-content-muted leading-relaxed">
            Journeys crafted to balance cultural wonder, unhurried pacing, and culinary immersion. Selected by travel writers and synthesized by AI.
          </p>
        </div>

        {/* Asymmetric Editorial Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">

          {/* 1. Large Lead Feature (7 Columns) */}
          <div className="lg:col-span-7 group flex flex-col justify-between bg-app-surface border border-edge-subtle rounded-3xl overflow-hidden shadow-lg transition-all duration-300 hover:border-edge-active">
            {/* Lead Image with Subtle Zoom on Hover */}
            <div className="relative h-80 sm:h-96 overflow-hidden">
              <img
                src={lead.heroImage}
                alt={lead.name}
                className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

              <div className="absolute top-4 left-4">
                <span className="px-3 py-1 rounded-full bg-black/50 backdrop-blur-md border border-white/20 text-white text-xs font-mono">
                  {lead.kicker}
                </span>
              </div>

              <div className="absolute bottom-4 left-4 right-4 text-white">
                <div className="flex items-center gap-2 text-teal-300 text-xs font-semibold mb-1">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>{lead.region}, {lead.country}</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold font-editorial leading-snug">
                  {lead.title}
                </h3>
              </div>
            </div>

            {/* Lead Story Content */}
            <div className="p-6 sm:p-8 flex-1 flex flex-col justify-between space-y-6">
              <p className="text-sm text-content-muted leading-relaxed">
                {lead.tagline} Experience the quiet dawn light through bamboo canopies, book a private tea ceremony in an 18th-century machiya, and explore the ancient capital at a meditative pace.
              </p>

              {/* Data Strip */}
              <div className="grid grid-cols-3 gap-3 py-3 border-y border-edge-subtle text-xs">
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Duration</span>
                  <span className="font-semibold text-content-main">{lead.suggestedDuration}</span>
                </div>
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Ideal Season</span>
                  <span className="font-semibold text-content-main">{lead.bestSeason}</span>
                </div>
                <div>
                  <span className="text-content-subtle block text-[10px] uppercase font-semibold">Budget Tier</span>
                  <span className="font-semibold text-teal-600 dark:text-teal-400">{lead.budgetTier}</span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex flex-wrap gap-1.5">
                  {lead.curatedHighlights.slice(0, 3).map((hl) => (
                    <span key={hl} className="text-[11px] px-2.5 py-1 rounded-lg bg-app-elevated border border-edge-subtle text-content-muted">
                      {hl}
                    </span>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => handlePick(lead.fullQuery)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold uppercase tracking-wider text-white bg-teal-600 hover:bg-teal-700 rounded-xl transition-all cursor-pointer shadow-sm hover:shadow"
                >
                  <span>Plan This</span>
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* 2. Secondary Staggered Vignettes (5 Columns) */}
          <div className="lg:col-span-5 flex flex-col gap-8 justify-between">
            {secondary.map((dest) => (
              <div
                key={dest.id}
                className="group bg-app-surface border border-edge-subtle rounded-3xl overflow-hidden shadow-md hover:border-edge-active transition-all duration-300 flex flex-col"
              >
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={dest.heroImage}
                    alt={dest.name}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                  <div className="absolute bottom-3 left-4 text-white">
                    <span className="text-xs font-mono text-teal-300 block">{dest.region}, {dest.country}</span>
                    <h4 className="text-lg font-bold font-editorial">{dest.name}</h4>
                  </div>
                </div>

                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <p className="text-xs text-content-muted leading-relaxed">
                    {dest.tagline}
                  </p>

                  <div className="flex items-center justify-between text-xs pt-2 border-t border-edge-subtle">
                    <span className="text-content-subtle font-medium">
                      {dest.suggestedDuration} • {dest.budgetTier}
                    </span>
                    <button
                      type="button"
                      onClick={() => handlePick(dest.fullQuery)}
                      className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>Explore</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

        </div>

      </div>
    </section>
  );
}
