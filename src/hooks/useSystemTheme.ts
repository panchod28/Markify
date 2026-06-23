import { useEffect } from 'react';
import { useAppStore } from '@/stores/useAppStore';
import type { Theme } from '@/types';

function resolveTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
}

export function useSystemTheme() {
  const theme = useAppStore(state => state.theme);
  const _setResolvedTheme = useAppStore(state => state._setResolvedTheme);

  useEffect(() => {
    const resolved = resolveTheme(theme);
    document.documentElement.setAttribute('data-theme', resolved);
    _setResolvedTheme(resolved);

    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      const newResolved = e.matches ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newResolved);
      _setResolvedTheme(newResolved);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, _setResolvedTheme]);
}
