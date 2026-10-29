/**
 * Locale mapping for Intl APIs
 */
export const LOCALE_MAP = {
  en: 'en-US',
  hi: 'hi-IN',
  es: 'es-ES',
  fr: 'fr-FR',
};

export const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'es', label: 'Spanish', native: 'Español', flag: '🇪🇸' },
  { code: 'fr', label: 'French', native: 'Français', flag: '🇫🇷' },
];

/**
 * Format a date string (YYYY-MM-DD) according to the active language
 */
export function formatLocaleDate(dateString, lang = 'en') {
  if (!dateString) return '';
  try {
    const locale = LOCALE_MAP[lang] || 'en-US';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat(locale, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(date);
  } catch {
    return dateString;
  }
}

/**
 * Format numbers according to active locale
 */
export function formatLocaleNumber(num, lang = 'en') {
  try {
    const locale = LOCALE_MAP[lang] || 'en-US';
    return new Intl.NumberFormat(locale).format(num);
  } catch {
    return String(num);
  }
}
