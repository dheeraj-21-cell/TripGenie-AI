import React, { useState, useEffect, useRef } from 'react';
import { TRAVEL_PHOTOS } from '../data/travelPhotos';
import { MapPin, Compass } from 'lucide-react';

export default function FullScreenBackground() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [nextIndex, setNextIndex] = useState(1);
  const [activeLayer, setActiveLayer] = useState('A'); // 'A' or 'B'
  const [reducedMotion, setReducedMotion] = useState(false);

  const photoA = useRef(TRAVEL_PHOTOS[0]);
  const photoB = useRef(TRAVEL_PHOTOS[1]);
  const lastIndexRef = useRef(0);

  // Check reduced-motion preference
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);

    const handler = (e) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // 2-Second Random Non-Repeating Crossfade Rotation
  useEffect(() => {
    if (reducedMotion) return;

    const interval = setInterval(() => {
      // Pick random index different from current
      let newIdx;
      do {
        newIdx = Math.floor(Math.random() * TRAVEL_PHOTOS.length);
      } while (newIdx === lastIndexRef.current && TRAVEL_PHOTOS.length > 1);

      lastIndexRef.current = newIdx;
      const nextPhoto = TRAVEL_PHOTOS[newIdx];

      // Preload next image before swapping layers
      const img = new Image();
      img.src = nextPhoto.url;
      img.onload = () => {
        if (activeLayer === 'A') {
          photoB.current = nextPhoto;
          setActiveLayer('B');
        } else {
          photoA.current = nextPhoto;
          setActiveLayer('A');
        }
        setCurrentIndex(newIdx);
      };
      img.onerror = () => {
        // Fallback: cycle to next if an image fails
        setCurrentIndex((prev) => (prev + 1) % TRAVEL_PHOTOS.length);
      };
    }, 2000); // Transitions every 2 seconds

    return () => clearInterval(interval);
  }, [activeLayer, reducedMotion]);

  const currentPhoto = activeLayer === 'A' ? photoA.current : photoB.current;

  return (
    <div className="fixed inset-0 pointer-events-none -z-20 overflow-hidden select-none">

      {/* Layer A */}
      <div
        className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-in-out transform ${
          reducedMotion ? 'scale-100' : 'scale-105 transition-transform duration-[12000ms]'
        } ${activeLayer === 'A' ? 'opacity-100 z-10' : 'opacity-0 z-0'}`}
        style={{ backgroundImage: `url(${photoA.current?.url})` }}
        aria-hidden="true"
      />

      {/* Layer B */}
      <div
        className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-in-out transform ${
          reducedMotion ? 'scale-100' : 'scale-105 transition-transform duration-[12000ms]'
        } ${activeLayer === 'B' ? 'opacity-100 z-10' : 'opacity-0 z-0'}`}
        style={{ backgroundImage: `url(${photoB.current?.url})` }}
        aria-hidden="true"
      />

      {/* Carefully Balanced Theme-Adaptive Dark Gradient Overlay */}
      {/* Guarantees high readability in both Light and Dark themes */}
      <div
        className="absolute inset-0 z-20 transition-colors duration-300"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(15, 23, 42, 0.55) 0%, rgba(15, 23, 42, 0.82) 65%, rgba(2, 6, 23, 0.95) 100%)',
          backdropFilter: 'blur(1px)'
        }}
        aria-hidden="true"
      />

      {/* Discreet Live Photo Location Tag */}
      <div className="absolute bottom-4 left-4 z-30 hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/10 text-white text-[11px] font-mono shadow-md">
        <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
        <span className="text-teal-300 font-semibold">{currentPhoto?.category}:</span>
        <span className="text-slate-200">{currentPhoto?.title}</span>
        <span className="text-slate-400">({currentPhoto?.location})</span>
      </div>

    </div>
  );
}
