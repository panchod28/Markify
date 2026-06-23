## ADDED Requirements

### Requirement: CSS base reset
The system SHALL apply `box-sizing: border-box` globally and set base body styles using CSS custom properties for font, size, color, and background.

#### Scenario: Global box-sizing
- **WHEN** any element is rendered
- **THEN** its box-sizing SHALL be `border-box`

#### Scenario: Body defaults
- **WHEN** the app loads
- **THEN** `body` SHALL use `var(--font-family)`, `var(--text-base)`, `var(--leading-normal)`, `var(--color-text-primary)` for color, and `var(--color-background)` for background

### Requirement: Light mode color tokens
The system SHALL define all color tokens under `:root` with Apple-inspired values: accent `#007AFF`, success `#34C759`, error `#FF3B30`, warning `#FF9500`, and appropriate surface/text/border colors.

#### Scenario: Accent color in light mode
- **WHEN** the theme is light
- **THEN** `--color-accent` SHALL be `#007AFF`

#### Scenario: Background hierarchy in light mode
- **WHEN** the theme is light
- **THEN** `--color-background` SHALL be `#F2F2F7` and `--color-surface` SHALL be `#FFFFFF`

### Requirement: Dark mode color tokens
The system SHALL define dark mode overrides under `[data-theme="dark"]` for all color tokens: accent `#0A84FF`, success `#30D158`, error `#FF453A`, and dark surfaces.

#### Scenario: Accent color in dark mode
- **WHEN** `html` has `data-theme="dark"`
- **THEN** `--color-accent` SHALL be `#0A84FF`

#### Scenario: Background hierarchy in dark mode
- **WHEN** `html` has `data-theme="dark"`
- **THEN** `--color-background` SHALL be `#000000` and `--color-surface` SHALL be `#1C1C1E`

### Requirement: Drop zone color tokens
The system SHALL define drop zone specific color tokens (`--color-dropzone-bg`, `--color-dropzone-border`, `--color-dropzone-bg-active`, `--color-dropzone-border-active`) for both light and dark mode.

#### Scenario: Drop zone idle in light mode
- **WHEN** the theme is light and drop zone is idle
- **THEN** background SHALL be `rgba(0, 122, 255, 0.03)` and border SHALL be `rgba(0, 122, 255, 0.30)`

#### Scenario: Drop zone active during drag
- **WHEN** a file is being dragged over the drop zone
- **THEN** background SHALL transition to `--color-dropzone-bg-active` and border to `--color-dropzone-border-active`

### Requirement: Typography tokens
The system SHALL define system font stacks, Apple HIG font sizes (xs through 3xl in rem), font weights (400-700), and line heights (tight: 1.2, normal: 1.4, relaxed: 1.6).

#### Scenario: System font stack
- **WHEN** text is rendered
- **THEN** it SHALL use `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Ubuntu', 'Helvetica Neue', Arial, sans-serif` with no Google Fonts loaded

#### Scenario: Font size scale
- **WHEN** `--text-base` is referenced
- **THEN** it SHALL equal `0.9375rem` (15px)

### Requirement: Spacing grid tokens
The system SHALL define spacing variables from `--space-1` (4px) to `--space-16` (64px), all multiples of 4px, preferably 8px.

#### Scenario: Spacing values
- **WHEN** `--space-2` is referenced
- **THEN** it SHALL be `8px`

#### Scenario: Gap between elements
- **WHEN** designing component layout
- **THEN** spacing SHALL use `var(--space-*)` tokens, never hardcoded values

### Requirement: Border radius tokens
The system SHALL define 4 radius levels: `--radius-sm` (6px), `--radius-md` (10px), `--radius-lg` (14px), `--radius-xl` (20px).

#### Scenario: Button radius
- **WHEN** a button is rendered
- **THEN** it SHALL use `var(--radius-md)` (10px)

#### Scenario: Modal radius
- **WHEN** a modal is displayed
- **THEN** it SHALL use `var(--radius-xl)` (20px)

### Requirement: Shadow tokens
The system SHALL define 4 shadow levels (`--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-modal`) with dark mode overrides that use darker, more opaque shadows.

#### Scenario: Modal shadow in light mode
- **WHEN** a modal opens in light mode
- **THEN** it SHALL use `var(--shadow-modal)` with translucent black

#### Scenario: Modal shadow in dark mode
- **WHEN** a modal opens in dark mode
- **THEN** it SHALL use a more opaque shadow suitable for dark backgrounds

### Requirement: Animation duration and easing tokens
The system SHALL define `--duration-fast` (100ms), `--duration-base` (200ms), `--duration-slow` (350ms) and easing curves: default, out, in, spring.

#### Scenario: Hover transition
- **WHEN** a user hovers over an interactive element
- **THEN** the transition SHALL use `var(--duration-fast)` and `var(--ease-default)`

#### Scenario: Modal entrance
- **WHEN** a modal appears
- **THEN** the animation SHALL use `var(--duration-base)` and `var(--ease-spring)`

### Requirement: Reduced motion support
The system SHALL respect `prefers-reduced-motion: reduce` by disabling all animations and transitions globally.

#### Scenario: User has reduced motion preference
- **WHEN** the OS has `prefers-reduced-motion: reduce`
- **THEN** all animation/transition durations SHALL be forced to `0.01ms` and scroll behavior SHALL be `auto`

### Requirement: Custom scrollbar styling
The system SHALL style Webkit scrollbars with a 6px width, transparent track, and themed thumb using `--color-scrollbar-thumb`.

#### Scenario: Scrollbar appearance
- **WHEN** a scrollable area renders
- **THEN** the scrollbar thumb SHALL use `var(--color-scrollbar-thumb)` with `border-radius: 99px`

### Requirement: Progress shimmer keyframe
The system SHALL define a `@keyframes shimmer` animation that sweeps a gradient from -200% to 200% background position for indeterminate progress bars.

#### Scenario: Indeterminate progress
- **WHEN** a file is being processed
- **THEN** the progress bar SHALL use the `progress-shimmer` class with the shimmer animation

### Requirement: Slide-in animation keyframe
The system SHALL define `@keyframes slideInUp` that translates elements 8px up while fading in, with a reusable `.animate-slide-in-up` class.

#### Scenario: File item appears in list
- **WHEN** a file is added to the list
- **THEN** it SHALL animate in using `.animate-slide-in-up`

### Requirement: Fade and scale keyframes
The system SHALL define `@keyframes fadeIn` and `@keyframes scaleIn` with reusable `.animate-fade-in` and `.animate-scale-in` classes for modals and overlays.

#### Scenario: Modal entrance
- **WHEN** a modal opens
- **THEN** it SHALL use `.animate-scale-in` for the panel and `.animate-fade-in` for the overlay

### Requirement: Markdown preview styles
The system SHALL provide `.markdown-preview` CSS class with typography, headings, lists, code blocks, tables, blockquotes, links, and horizontal rules styling using design tokens.

#### Scenario: Code block in preview
- **WHEN** markdown contains a code block
- **THEN** it SHALL render with `var(--font-family-mono)`, `var(--color-surface-secondary)` background, and `var(--radius-md)` border radius

#### Scenario: Link in preview
- **WHEN** markdown contains a link
- **THEN** it SHALL render with `var(--color-accent)` color and underline on hover
