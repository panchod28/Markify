import { create } from 'zustand';
import i18n from '@/i18n';
import { Store } from '@tauri-apps/plugin-store';
import type { Theme, ResolvedTheme, Language, ResolvedLanguage } from '@/types';

interface AppStore {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  language: Language;
  resolvedLanguage: ResolvedLanguage;

  setTheme: (theme: Theme) => Promise<void>;
  setLanguage: (lang: Language) => Promise<void>;

  _setResolvedTheme: (theme: ResolvedTheme) => void;
  _setResolvedLanguage: (lang: ResolvedLanguage) => void;

  _initialize: () => Promise<void>;
}

const INITIAL_STATE = {
  theme: 'system' as Theme,
  resolvedTheme: 'light' as ResolvedTheme,
  language: 'system' as Language,
  resolvedLanguage: 'en' as ResolvedLanguage,
};

export const useAppStore = create<AppStore>((set) => ({
  ...INITIAL_STATE,

  setTheme: async (theme) => {
    set({ theme });
    const store = await Store.load('markify-prefs.json');
    await store.set('theme', theme);
    await store.save();
  },

  setLanguage: async (lang) => {
    const resolved = lang === 'system'
      ? (navigator.language.startsWith('es') ? 'es' : 'en')
      : lang as ResolvedLanguage;
    set({ language: lang, resolvedLanguage: resolved });
    await i18n.changeLanguage(resolved);
    const store = await Store.load('markify-prefs.json');
    await store.set('language', lang);
    await store.save();
  },

  _setResolvedTheme: (resolvedTheme) => set({ resolvedTheme }),
  _setResolvedLanguage: (resolvedLanguage) => set({ resolvedLanguage }),

  _initialize: async () => {
    try {
      const store = await Store.load('markify-prefs.json');
      const savedTheme = await store.get<Theme>('theme');
      const savedLang = await store.get<Language>('language');
      set({
        theme: savedTheme ?? 'system',
        language: savedLang ?? 'system',
      });
      const langToApply = savedLang ?? 'system';
      const resolved = langToApply === 'system'
        ? (navigator.language.startsWith('es') ? 'es' : 'en')
        : langToApply as ResolvedLanguage;
      set({ resolvedLanguage: resolved });
      await i18n.changeLanguage(resolved);
    } catch {
      // Si falla la lectura del store, usar valores iniciales
      // (primera ejecución o archivo corrupto)
    }
  },
}));
