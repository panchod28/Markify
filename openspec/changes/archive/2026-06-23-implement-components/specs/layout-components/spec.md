## ADDED Requirements

### Requirement: AppShell initialization
The system SHALL provide an `AppShell` component that on mount calls `useAppStore._initialize()`, `useTauriEvents()`, `useSystemTheme()`, and `checkWhisperModel()`, then renders Header + children.

#### Scenario: App mounts
- **WHEN** `AppShell` mounts
- **THEN** preferences SHALL be loaded, Tauri events SHALL be subscribed, theme SHALL be applied, and Whisper model SHALL be checked

### Requirement: Header with macOS padding
The system SHALL render a 48px header with logo, ThemeToggle, and LanguageToggle. On macOS it SHALL apply `pl-[76px]` for traffic lights.

#### Scenario: macOS detected
- **WHEN** `navigator.platform.includes('Mac')` is true
- **THEN** the header SHALL have `pl-[76px]`

### Requirement: ThemeToggle cycle
The system SHALL cycle theme through `light → dark → system → light` on click, showing Sun icon in dark mode and Moon in light mode.

#### Scenario: Click toggles theme
- **WHEN** current theme is `'light'` and user clicks
- **THEN** theme SHALL change to `'dark'` via `useAppStore.setTheme()`

### Requirement: LanguageToggle with i18n sync
The system SHALL toggle language between `'es'` and `'en'` on click, calling both `useAppStore.setLanguage()` and `i18n.changeLanguage()`.

#### Scenario: Switch to Spanish
- **WHEN** user clicks and current language is `'en'`
- **THEN** language SHALL change to `'es'` in both store and i18next
