import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import hi from './locales/hi.json';
import es from './locales/es.json';
import fr from './locales/fr.json';

const SUPPORTED_LANGUAGES = ['en', 'hi', 'es', 'fr'];

const getInitialLanguage = () => {
  try {
    const saved = localStorage.getItem('tripgenie-lang');
    if (saved && SUPPORTED_LANGUAGES.includes(saved)) {
      return saved;
    }
    const browserLang = navigator.language?.split('-')[0];
    if (browserLang && SUPPORTED_LANGUAGES.includes(browserLang)) {
      return browserLang;
    }
  } catch {
    // Fallback if storage access is restricted
  }
  return 'en';
};

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
      es: { translation: es },
      fr: { translation: fr },
    },
    lng: getInitialLanguage(),
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

// Automatically persist on change
i18n.on('languageChanged', (lng) => {
  try {
    localStorage.setItem('tripgenie-lang', lng);
    document.documentElement.lang = lng;
  } catch {
    // Ignore storage errors
  }
});

export default i18n;
