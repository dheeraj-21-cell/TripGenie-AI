import React, { useState, useRef, useEffect } from 'react';
import { Compass, Sparkles, Menu, X, Sun, Moon, Globe, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import { LANGUAGE_OPTIONS } from '../utils/formatters';

export default function Navbar() {
  const { t, i18n } = useTranslation();
  const { theme, toggleTheme, isDark } = useTheme();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const langMenuRef = useRef(null);

  const currentLang = LANGUAGE_OPTIONS.find((l) => l.code === i18n.language) || LANGUAGE_OPTIONS[0];

  const handleLanguageChange = (code) => {
    i18n.changeLanguage(code);
    setLangDropdownOpen(false);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (langMenuRef.current && !langMenuRef.current.contains(event.target)) {
        setLangDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-app-surface/85 backdrop-blur-md border-b border-edge-subtle transition-colors duration-250">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18">

          {/* Editorial Brand Mark */}
          <a href="#" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-md shadow-teal-600/25 group-hover:scale-105 transition-transform">
              <Compass className="w-5 h-5" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl font-bold font-editorial text-content-main tracking-tight">
                TripGenie
              </span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-teal-600 dark:text-teal-400 font-bold">
                AI
              </span>
            </div>
          </a>

          {/* Desktop Navigation Links & Controls */}
          <div className="hidden md:flex items-center gap-6">
            <a href="#planner" className="text-xs font-semibold uppercase tracking-wider text-content-muted hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
              {t('nav.planItinerary')}
            </a>
            <a href="#destinations" className="text-xs font-semibold uppercase tracking-wider text-content-muted hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
              Destinations
            </a>
            <a href="#methodology" className="text-xs font-semibold uppercase tracking-wider text-content-muted hover:text-teal-600 dark:hover:text-teal-400 transition-colors">
              {t('nav.features')}
            </a>

            <div className="h-4 w-px bg-edge-subtle" />

            {/* Language Selector Dropdown */}
            <div className="relative" ref={langMenuRef}>
              <button
                type="button"
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-content-main bg-app-elevated hover:bg-app-surface rounded-lg border border-edge-subtle transition-all cursor-pointer"
                aria-label={t('nav.language')}
              >
                <Globe className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                <span>{currentLang.flag}</span>
                <span className="hidden lg:inline">{currentLang.native}</span>
                <ChevronDown className="w-3 h-3 text-content-subtle" />
              </button>

              {langDropdownOpen && (
                <div className="absolute right-0 mt-2 w-44 rounded-xl bg-app-surface border border-edge-strong shadow-xl py-1.5 z-50">
                  <div className="px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-content-subtle">
                    {t('nav.language')}
                  </div>
                  {LANGUAGE_OPTIONS.map((item) => (
                    <button
                      key={item.code}
                      type="button"
                      onClick={() => handleLanguageChange(item.code)}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-app-elevated transition-colors cursor-pointer ${
                        i18n.language === item.code
                          ? 'text-teal-600 dark:text-teal-400 font-bold bg-teal-500/10'
                          : 'text-content-main'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <span>{item.flag}</span>
                        <span>{item.native}</span>
                      </span>
                      {i18n.language === item.code && (
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-600 dark:text-teal-400" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Working Light / Dark Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-lg text-content-muted hover:text-content-main bg-app-elevated hover:bg-app-surface border border-edge-subtle transition-all cursor-pointer"
              title={isDark ? t('nav.themeLight') : t('nav.themeDark')}
              aria-label={isDark ? t('nav.themeLight') : t('nav.themeDark')}
            >
              {isDark ? (
                <Sun className="w-4 h-4 text-amber-400 transition-transform rotate-0 hover:rotate-45" />
              ) : (
                <Moon className="w-4 h-4 text-slate-700 transition-transform hover:-rotate-12" />
              )}
            </button>

            {/* Sign In Mock Modal */}
            <button
              type="button"
              onClick={() => alert(t('nav.authNotice'))}
              className="text-xs font-semibold uppercase tracking-wider text-content-muted hover:text-teal-600 dark:hover:text-teal-400 transition-colors cursor-pointer"
            >
              {t('nav.signIn')}
            </button>

            {/* CTA Button */}
            <a
              href="#planner"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold uppercase tracking-wider text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm shadow-teal-600/30 transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{t('nav.startPlanning')}</span>
            </a>
          </div>

          {/* Mobile Right Controls: Theme + Hamburger */}
          <div className="md:hidden flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-lg text-content-main bg-app-elevated border border-edge-subtle cursor-pointer"
              aria-label={isDark ? t('nav.themeLight') : t('nav.themeDark')}
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
            </button>

            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-content-main hover:bg-app-elevated cursor-pointer"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-edge-subtle bg-app-surface px-4 pt-3 pb-6 space-y-4 shadow-xl">
          {/* Mobile Language Switcher */}
          <div className="flex items-center justify-between pb-3 border-b border-edge-subtle">
            <span className="text-xs font-mono uppercase tracking-wider text-content-subtle flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              {t('nav.language')}:
            </span>
            <div className="flex items-center gap-1">
              {LANGUAGE_OPTIONS.map((item) => (
                <button
                  key={item.code}
                  type="button"
                  onClick={() => handleLanguageChange(item.code)}
                  className={`px-2 py-1 text-xs rounded-md font-semibold border ${
                    i18n.language === item.code
                      ? 'bg-teal-600 text-white border-teal-600'
                      : 'bg-app-elevated text-content-main border-edge-subtle'
                  }`}
                >
                  {item.flag} {item.code.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <a
            href="#planner"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-semibold text-content-main hover:text-teal-600 dark:hover:text-teal-400"
          >
            {t('nav.planItinerary')}
          </a>
          <a
            href="#destinations"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-semibold text-content-main hover:text-teal-600 dark:hover:text-teal-400"
          >
            Destinations
          </a>
          <a
            href="#methodology"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-sm font-semibold text-content-main hover:text-teal-600 dark:hover:text-teal-400"
          >
            {t('nav.features')}
          </a>

          <div className="pt-2 border-t border-edge-subtle flex flex-col gap-2">
            <button
              type="button"
              onClick={() => {
                setMobileMenuOpen(false);
                alert(t('nav.authNotice'));
              }}
              className="w-full text-center py-2 text-xs font-bold uppercase tracking-wider text-content-main hover:text-teal-600"
            >
              {t('nav.signIn')}
            </button>
            <a
              href="#planner"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full text-center py-2.5 text-xs font-bold uppercase tracking-wider text-white bg-teal-600 rounded-lg"
            >
              {t('nav.startPlanning')}
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
