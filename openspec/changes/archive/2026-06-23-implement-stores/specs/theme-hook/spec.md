## MODIFIED Requirements

### Requirement: Theme initialization on mount
The system SHALL provide a `useSystemTheme` hook that reads the stored theme preference from `useAppStore` on mount and applies it to `document.documentElement` via the `data-theme` attribute.

#### Scenario: App starts with saved light theme
- **WHEN** the app loads and `useAppStore.state.theme === 'light'`
- **THEN** `document.documentElement` SHALL have `data-theme="light"`

#### Scenario: App starts with saved dark theme
- **WHEN** the app loads and `useAppStore.state.theme === 'dark'`
- **THEN** `document.documentElement` SHALL have `data-theme="dark"`

### Requirement: System theme listener
The system SHALL listen for `prefers-color-scheme` changes when `theme === 'system'` and update the resolved theme via `useAppStore._setResolvedTheme()`.

#### Scenario: System switches to dark mode
- **WHEN** `theme === 'system'` and the OS switches to dark mode
- **THEN** `data-theme` SHALL change to `"dark"` and `_setResolvedTheme('dark')` SHALL be called

#### Scenario: System switches to light mode
- **WHEN** `theme === 'system'` and the OS switches to light mode
- **THEN** `data-theme` SHALL change to `"light"` and `_setResolvedTheme('light')` SHALL be called

### Requirement: Manual theme override
The system SHALL apply the theme directly when `theme` is `'light'` or `'dark'` via `_setResolvedTheme()` without listening to system changes.

#### Scenario: User selects dark from theme toggle
- **WHEN** user calls `setTheme('dark')` in the store
- **THEN** `data-theme` SHALL be set to `"dark"`, `_setResolvedTheme('dark')` SHALL be called, and system listener SHALL NOT be active

### Requirement: Cleanup on unmount
The system SHALL remove the `prefers-color-scheme` media query listener when the component using `useSystemTheme` unmounts.

#### Scenario: Component unmounts
- **WHEN** the component that mounted `useSystemTheme` is removed
- **THEN** the `matchMedia` listener SHALL be removed to prevent memory leaks

### Requirement: NUNCA usar clase 'dark' de Tailwind
The system SHALL use ONLY the `data-theme` attribute on `<html>`. It SHALL NEVER add or remove the `dark` CSS class.

#### Scenario: Dark mode applied
- **WHEN** dark mode is active
- **THEN** `<html>` SHALL have `data-theme="dark"` and SHALL NOT have a `dark` class
