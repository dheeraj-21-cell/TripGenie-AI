import React from 'react';
import { Compass, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="bg-app-surface text-content-muted py-14 border-t border-edge-subtle transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Top Header Row */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-10 border-b border-edge-subtle">

          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-bold font-editorial text-content-main tracking-tight">
                TripGenie AI
              </span>
              <span className="text-xs text-content-subtle block font-mono">
                {t('footer.tagline')}
              </span>
            </div>
          </div>

          <div className="text-left md:text-right">
            <span className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-teal-600 dark:text-teal-400 bg-teal-500/10 border border-teal-500/30 px-3 py-1.5 rounded-full">
              <Sparkles className="w-3.5 h-3.5" />
              <span>{t('footer.attribution')}</span>
            </span>
          </div>
        </div>

        {/* Bottom Details Row */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-content-subtle">
          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="font-mono uppercase text-[11px] text-content-subtle">{t('footer.stackLabel')}</span>
            {['React + Vite', 'Tailwind CSS', 'Python FastAPI', 'Groq LLaMA 3.3', 'Supabase', 'Unsplash API'].map((tech) => (
              <span key={tech} className="bg-app-elevated border border-edge-subtle px-2.5 py-1 rounded-md text-content-muted text-[11px]">
                {tech}
              </span>
            ))}
          </div>

          <div className="text-center font-mono text-[11px]">
            {t('footer.copyright')}
          </div>
        </div>

      </div>
    </footer>
  );
}
