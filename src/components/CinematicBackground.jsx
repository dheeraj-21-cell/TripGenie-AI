import React, { useState, useEffect } from 'react';

const SCENIC_SLIDES = [
  {
    url: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1920&q=80',
    location: 'Kyoto, Japan',
    caption: 'Arashiyama Bamboo Forest & Pagodas'
  },
  {
    url: 'https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=1920&q=80',
    location: 'Amalfi Coast, Italy',
    caption: 'Cliffside Mediterranean Villas'
  },
  {
    url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=1920&q=80',
    location: 'Swiss Alps, Switzerland',
    caption: 'Alpine Peaks & Valley Glaciers'
  },
  {
    url: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1920&q=80',
    location: 'Agra, India',
    caption: 'Taj Mahal at Golden Sunrise'
  },
  {
    url: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1920&q=80',
    location: 'Bali, Indonesia',
    caption: 'Emerald Rice Terraces & Water Temples'
  }
];

export default function CinematicBackground() {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    // Respect reduced motion: do not auto-rotate if user requested reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % SCENIC_SLIDES.length);
    }, 8000); // 8-second cinematic pace

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
      {/* Background Slides */}
      {SCENIC_SLIDES.map((slide, index) => (
        <div
          key={slide.url}
          className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 transform scale-105 motion-safe:transition-transform motion-safe:duration-[10000ms] ${
            index === currentSlide ? 'opacity-30 scale-100' : 'opacity-0 scale-105'
          }`}
          style={{ backgroundImage: `url(${slide.url})` }}
          aria-hidden="true"
        />
      ))}

      {/* Adaptive Theme Overlay Gradient (guarantees high contrast in both Light & Dark modes) */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/95 via-white/85 to-slate-50/95 dark:from-slate-950/95 dark:via-slate-950/85 dark:to-slate-950/95 backdrop-blur-[2px] transition-colors duration-300" />

      {/* Subtle bottom location tag */}
      <div className="absolute bottom-4 right-4 hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/70 dark:bg-slate-900/80 backdrop-blur-md border border-slate-200/60 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-300 shadow-sm pointer-events-auto">
        <span className="w-2 h-2 rounded-full bg-teal-500 animate-ping" />
        <span className="font-semibold text-slate-800 dark:text-slate-100">
          {SCENIC_SLIDES[currentSlide].location}
        </span>
        <span className="text-slate-400 dark:text-slate-500">|</span>
        <span className="text-slate-500 dark:text-slate-400">
          {SCENIC_SLIDES[currentSlide].caption}
        </span>
      </div>
    </div>
  );
}
