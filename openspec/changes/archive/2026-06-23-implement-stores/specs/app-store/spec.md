## ADDED Requirements

### Requirement: AppStore interface
The system SHALL provide an `AppStore` interface with state fields `theme`, `resolvedTheme`, `language`, `resolvedLanguage` and actions `setTheme`, `setLanguage`, `_setResolvedTheme`, `_setResolvedLanguage`, `_initialize`.

#### Scenario: Store shape
- **WHEN** the app store is created
- **THEN** it SHALL expose all 4 state fields and 5 actions

### Requirement: Initial values before initialization
The system SHALL initialize `theme` to `'system'`, `resolvedTheme` to `'light'`, `language` to `'system'`, and `resolvedLanguage` to `'en'` before `_initialize()` loads persisted values.

#### Scenario: Fresh app launch
- **WHEN** the app starts and no persisted preferences exist
- **THEN** theme SHALL be `'system'` and language SHALL be `'system'`

### Requirement: Persist theme via tauri-plugin-store
The system SHALL persist the `theme` preference to `markify-prefs.json` using `tauri-plugin-store` when `setTheme()` is called.

#### Scenario: User changes theme
- **WHEN** `setTheme('dark')` is called
- **THEN** `theme` in state SHALL be `'dark'` AND the value SHALL be saved to disk

#### Scenario: User sets system theme
- **WHEN** `setTheme('system')` is called
- **THEN** `theme` SHALL be `'system'` (resolution happens in `useSystemTheme` hook)

### Requirement: Persist language via tauri-plugin-store
The system SHALL persist the `language` preference to `markify-prefs.json` when `setLanguage()` is called.

#### Scenario: User changes language
- **WHEN** `setLanguage('es')` is called
- **THEN** `language` in state SHALL be `'es'` AND the value SHALL be saved to disk

### Requirement: Internal resolved setters
The system SHALL provide `_setResolvedTheme` and `_setResolvedLanguage` as internal actions that update state without persisting.

#### Scenario: Theme resolution
- **WHEN** `useSystemTheme` detects `prefers-color-scheme: dark`
- **THEN** it SHALL call `_setResolvedTheme('dark')` without triggering persistence

### Requirement: Initialize from disk
The system SHALL load persisted `theme` and `language` from `markify-prefs.json` via `tauri-plugin-store` when `_initialize()` is called. On failure, it SHALL fall back to initial values.

#### Scenario: Restore saved preferences
- **WHEN** `_initialize()` is called and `markify-prefs.json` has `{ theme: 'dark', language: 'es' }`
- **THEN** `theme` SHALL be `'dark'` and `language` SHALL be `'es'`

#### Scenario: First launch or corrupt store
- **WHEN** `_initialize()` is called and the store read fails
- **THEN** `theme` SHALL remain `'system'` and `language` SHALL remain `'system'`
