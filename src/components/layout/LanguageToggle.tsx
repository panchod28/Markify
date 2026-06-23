import { useAppStore } from '@/stores/useAppStore';
import type { Language } from '@/types';

export function LanguageToggle() {
  const resolvedLanguage = useAppStore(s => s.resolvedLanguage);
  const setLanguage = useAppStore(s => s.setLanguage);

  const toggle = () => {
    const next: Language = resolvedLanguage === 'es' ? 'en' : 'es';
    setLanguage(next);
  };

  return (
    <button
      onClick={toggle}
      className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-surface-secondary transition-colors duration-fast"
    >
      <span className="text-sm font-medium text-text-primary">
        {resolvedLanguage === 'es' ? 'ES' : 'EN'}
      </span>
    </button>
  );
}
