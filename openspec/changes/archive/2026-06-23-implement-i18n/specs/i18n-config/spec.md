## ADDED Requirements

### Requirement: i18next initialization
The system SHALL configure i18next with `LanguageDetector` and `initReactI18next`, fallback `'en'`, `supportedLngs: ['en', 'es']`, `load: 'languageOnly'`, `detection.order: ['localStorage', 'navigator']`, and embedded resources.

#### Scenario: User language detected
- **WHEN** the app starts and the user's browser language is `'es-MX'`
- **THEN** i18n SHALL load `'es'` translations

#### Scenario: No saved preference, navigator is English
- **WHEN** localStorage has no saved language and `navigator.language` is `'en-US'`
- **THEN** i18n SHALL use `'en'` translations

### Requirement: Import i18n before React render
The system SHALL import `./i18n/index` in `src/main.tsx` before rendering the app.

#### Scenario: App renders with i18n
- **WHEN** the React app mounts
- **THEN** `useTranslation()` SHALL be available in all components

### Requirement: Common namespace translations
The system SHALL provide `common.json` for ES and EN with keys for: app, dropzone, fileList, processing, results, preview, whisperModal, confirmDialog, theme, language, errors.

#### Scenario: Spanish dropzone title
- **WHEN** `t('dropzone.title')` is called with ES active
- **THEN** it SHALL return `"Arrastra tus archivos aquí"`

### Requirement: Messages namespace translations
The system SHALL provide `messages.json` for ES and EN with error keys: password_protected, file_corrupted, no_text_found, audio_too_short, file_not_found, unknown.

#### Scenario: English conversion error
- **WHEN** `t('conversion.password_protected', { ns: 'messages' })` is called with EN active
- **THEN** it SHALL return `"The file is password protected"`

### Requirement: Pluralization support
The system SHALL support `_one` and `_other` plural forms via react-i18next CLDR.

#### Scenario: Single file translated
- **WHEN** `t('results.successAll', { count: 1 })` is called with ES active
- **THEN** it SHALL return `"1 archivo convertido correctamente"`

#### Scenario: Multiple files translated
- **WHEN** `t('results.successAll', { count: 3 })` is called with ES active
- **THEN** it SHALL return `"3 archivos convertidos correctamente"`
