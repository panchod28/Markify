## ADDED Requirements

### Requirement: Tailwind dark mode via data-theme attribute
The system SHALL configure Tailwind's `darkMode` as `['attribute', '[data-theme="dark"]']` to match the app's theme mechanism instead of Tailwind's default `class` strategy.

#### Scenario: Dark mode applied
- **WHEN** `<html>` has `data-theme="dark"`
- **THEN** Tailwind's `dark:` variant SHALL activate

#### Scenario: Light mode (default)
- **WHEN** `<html>` has no `data-theme` or `data-theme="light"`
- **THEN** light mode colors SHALL apply

### Requirement: Color mapping to CSS variables
The system SHALL map all CSS custom property colors to Tailwind's `colors` config under semantic names: `accent`, `success`, `error`, `warning`, `bg`, `surface`, `text`, `border`.

#### Scenario: Using accent color in component
- **WHEN** a component uses `bg-accent` Tailwind class
- **THEN** it SHALL resolve to `var(--color-accent)`

#### Scenario: Using text secondary in component
- **WHEN** a component uses `text-text-secondary` Tailwind class
- **THEN** it SHALL resolve to `var(--color-text-secondary)`

### Requirement: Font family mapping
The system SHALL map `font-sans` to `var(--font-family)` and `font-mono` to `var(--font-family-mono)` in Tailwind config.

#### Scenario: Default text
- **WHEN** a component uses `font-sans`
- **THEN** it SHALL render with the system font stack

#### Scenario: Code text
- **WHEN** a component uses `font-mono`
- **THEN** it SHALL render with the monospace font stack

### Requirement: Font size mapping
The system SHALL map all text size tokens (`--text-xs` through `--text-3xl`) to Tailwind's `fontSize` config with appropriate line heights.

#### Scenario: Base text size
- **WHEN** a component uses `text-base`
- **THEN** it SHALL render at `0.9375rem` with `var(--leading-relaxed)` line height

#### Scenario: Heading size
- **WHEN** a component uses `text-3xl`
- **THEN** it SHALL render at `2.125rem` with `var(--leading-tight)` line height

### Requirement: Border radius mapping
The system SHALL map `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl` to Tailwind's `borderRadius` config.

#### Scenario: Rounded button
- **WHEN** a component uses `rounded-md`
- **THEN** it SHALL have `var(--radius-md)` (10px) border radius

### Requirement: Box shadow mapping
The system SHALL map `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-modal` to Tailwind's `boxShadow` config.

#### Scenario: Card shadow
- **WHEN** a panel uses `shadow-lg`
- **THEN** it SHALL render with `var(--shadow-lg)`

### Requirement: Transition duration mapping
The system SHALL map `--duration-fast`, `--duration-base`, `--duration-slow` to Tailwind's `transitionDuration` config.

#### Scenario: Fast transition
- **WHEN** a component uses `duration-fast`
- **THEN** transitions SHALL complete in `var(--duration-fast)` (100ms)

### Requirement: Transition timing function mapping
The system SHALL map `--ease-default` and `--ease-spring` to Tailwind's `transitionTimingFunction` config.

#### Scenario: Spring easing
- **WHEN** a component uses `ease-spring`
- **THEN** it SHALL use the cubic-bezier curve with subtle bounce

### Requirement: Content paths configuration
The system SHALL configure Tailwind to scan `./index.html` and `./src/**/*.{ts,tsx}` for class usage.

#### Scenario: Class purging in production
- **WHEN** building for production
- **THEN** only classes used in source files SHALL be included in the CSS bundle
