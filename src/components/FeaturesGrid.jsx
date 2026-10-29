import React from 'react';
import { Zap, Image, Database, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const FEATURE_ICONS = {
  groq: Zap,
  unsplash: Image,
  supabase: Database,
  pace: Clock
};

export default function FeaturesGrid() {
  const { t } = useTranslation();

  const featureKeys = ['groq', 'unsplash', 'supabase', 'pace'];
  const steps = [
    { num: '01', key: 'step1' },
    { num: '02', key: 'step2' },
    { num: '03', key: 'step3' },
  ];

  return (
    <section id="features" className="py-16 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Section Title */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <span className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/70 px-3 py-1 rounded-full border border-teal-200/60 dark:border-teal-800/60">
            {t('features.badge')}
          </span>
          <h2 className="text-3xl font-bold text-slate-900 dark:text-white mt-3 tracking-tight sm:text-4xl">
            {t('features.title')}
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mt-3 text-base">
            {t('features.subtitle')}
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
          {featureKeys.map((key) => {
            const Icon = FEATURE_ICONS[key];
            const tag = t(`features.cards.${key}.tag`);
            const title = t(`features.cards.${key}.title`);
            const desc = t(`features.cards.${key}.desc`);

            return (
              <div
                key={key}
                className="bg-slate-50/80 dark:bg-slate-900/80 hover:bg-white dark:hover:bg-slate-900 rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 hover:border-teal-500/50 dark:hover:border-teal-500/50 hover:shadow-lg hover:shadow-teal-500/5 transition-all group"
              >
                <div className="w-12 h-12 rounded-xl bg-teal-100 dark:bg-teal-950/80 text-teal-700 dark:text-teal-300 flex items-center justify-center mb-4 group-hover:scale-105 group-hover:bg-teal-600 group-hover:text-white transition-all">
                  <Icon className="w-6 h-6" />
                </div>
                <span className="text-[11px] font-bold text-teal-700 dark:text-teal-400 uppercase tracking-wider">
                  {tag}
                </span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-1 mb-2">
                  {title}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* How It Works Subsection */}
        <div id="how-it-works" className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 dark:from-slate-900 dark:via-slate-950 dark:to-teal-950/80 rounded-3xl p-8 sm:p-12 text-white relative overflow-hidden border border-slate-700/60 dark:border-slate-800">
          <div className="max-w-2xl mb-10">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-400">
              {t('features.workflow.badge')}
            </span>
            <h3 className="text-2xl sm:text-3xl font-bold mt-2">
              {t('features.workflow.title')}
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
            {steps.map((item) => (
              <div key={item.num} className="border-t border-slate-700/80 pt-6">
                <span className="text-3xl font-extrabold text-teal-400/80 block mb-2 font-mono">
                  {item.num}
                </span>
                <h4 className="text-base font-bold text-white mb-2">
                  {t(`features.workflow.${item.key}.title`)}
                </h4>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                  {t(`features.workflow.${item.key}.desc`)}
                </p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </section>
  );
}
