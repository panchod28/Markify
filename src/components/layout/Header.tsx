import { ThemeToggle } from './ThemeToggle';
import { LanguageToggle } from './LanguageToggle';

function isMacOS(): boolean {
  return typeof navigator !== 'undefined' && /Mac/i.test(navigator.platform);
}

export function Header() {
  return (
    <header
      className="h-12 flex items-center justify-between px-4 border-b border-border bg-surface"
      style={isMacOS() ? { paddingLeft: '76px' } : undefined}
    >
      <div className="flex items-center gap-2">
        <span className="text-base font-semibold text-text-primary">Markify</span>
      </div>

      <div className="flex items-center gap-1">
        <ThemeToggle />
        <div className="w-px h-4 bg-border mx-1" />
        <LanguageToggle />
      </div>
    </header>
  );
}
