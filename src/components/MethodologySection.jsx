import React from 'react';
import { Zap, Image, Database, Compass, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function MethodologySection() {
  const { t } = useTranslation();

  const PILLARS = [
    {
      num: '01',
      title: 'Groq LPU Acceleration',
      tech: 'Fast LPU Hardware • LLaMA 3.3 70B',
      desc: 'Traditional travel planning takes hours of disjointed searches. We leverage Groq’s tensor processing units to generate full multi-day itineraries in sub-two-second JSON mode.',
      icon: Zap
    },
    {
      num: '02',
      title: 'Visual Grounding with Unsplash',
      tech: 'Editorial Photography API',
      desc: 'Every neighborhood, heritage landmark, and dining reservation is visually paired with real-world photography, giving you an immediate sense of scale, atmosphere, and light.',
      icon: Image
    },
    {
      num: '03',
      title: 'Supabase Cloud Vault',
      tech: 'PostgreSQL • Row Level Security',
      desc: 'Save and synchronize your journeys securely. Edit plans on desktop, access day schedules on mobile, and bookmark hidden gems with persistent cloud authentication.',
      icon: Database
    }
  ];

  return (
    <section id="methodology" className="py-24 bg-app-surface border-t border-edge-subtle transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Editorial Section Header */}
        <div className="max-w-3xl mb-16">
          <span className="text-xs font-bold uppercase tracking-widest text-teal-600 dark:text-teal-400 font-mono block mb-2">
            The Atelier Method
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold font-editorial text-content-main tracking-tight mb-4">
            Where Machine Precision Meets Travel Wisdom
          </h2>
          <p className="text-sm sm:text-base text-content-muted leading-relaxed">
            Designed for the Skill Wallet Generative AI program. We combine cutting-edge cloud infrastructure with human-centered travel principles.
          </p>
        </div>

        {/* Minimalist Editorial 3-Column Strip */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 border-t border-edge-subtle pt-10">
          {PILLARS.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.num} className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-2xl font-bold text-teal-600 dark:text-teal-400">
                    {item.num}
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                <div className="text-[11px] font-mono text-content-subtle uppercase tracking-wider">
                  {item.tech}
                </div>

                <h3 className="text-lg font-bold text-content-main font-editorial">
                  {item.title}
                </h3>

                <p className="text-xs text-content-muted leading-relaxed">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
