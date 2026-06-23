import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enCommon from './locales/en/common.json';
import enMessages from './locales/en/messages.json';
import esCommon from './locales/es/common.json';
import esMessages from './locales/es/messages.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: ['en', 'es'],
    load: 'languageOnly',

    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'markify-i18n-language',
    },

    ns: ['common', 'messages'],
    defaultNS: 'common',

    resources: {
      en: {
        common: enCommon,
        messages: enMessages,
      },
      es: {
        common: esCommon,
        messages: esMessages,
      },
    },

    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
