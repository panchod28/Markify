import { useTranslation } from 'react-i18next';
import { Sun, Moon } from 'lucide-react';
import { useAppStore } from '@/stores/useAppStore';
import type { Theme } from '@/types';

const THEME_CYCLE: Theme[] = ['light', 'dark', 'system'];

export function ThemeToggle() {
  const { t } = useTranslation();
  const theme = useAppStore(s => s.theme);
  const resolvedTheme = useAppStore(s => s.resolvedTheme);
  const setTheme = useAppStore(s => s.setTheme);

  const nextIndex = (THEME_CYCLE.indexOf(theme) + 1) % THEME_CYCLE.length;
  const nextTheme = THEME_CYCLE[nextIndex];

  return (
    <button
      onClick={() => setTheme(nextTheme)}
      className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-secondary transition-colors duration-fast"
      title={t('theme.tooltip', { mode: t(`theme.${theme}`) })}
      aria-label={t(`theme.${theme}`)}
    >
      <span className="transition-opacity duration-150">
        {resolvedTheme === 'dark' ? (
          <Sun size={18} className="text-text-primary" />
        ) : (
          <Moon size={18} className="text-text-primary" />
        )}
      </span>
    </button>
  );
}
