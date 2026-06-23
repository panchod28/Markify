## ADDED Requirements

### Requirement: components.json configuration
The system SHALL provide a `components.json` file at project root configuring shadcn/ui with TypeScript, CSS variables, neutral base color, and correct path aliases matching the project structure.

#### Scenario: shadcn paths
- **WHEN** shadcn generates a component
- **THEN** it SHALL use `@/components/ui` for UI components, `@/lib/cn` for utils, `@/hooks` for hooks

#### Scenario: Tailwind and CSS config
- **WHEN** shadcn reads the config
- **THEN** it SHALL reference `tailwind.config.ts` for Tailwind and `src/index.css` for CSS with `cssVariables: true`

### Requirement: shadcn CSS variable mapping in light mode
The system SHALL map shadcn/ui required CSS variables (`--background`, `--foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--border`, `--ring`, `--destructive`) to HSL equivalents of Markify tokens under `:root`.

#### Scenario: shadcn button uses primary color
- **WHEN** a shadcn `Button` component renders with `variant="default"`
- **THEN** it SHALL use `--primary` which resolves to `211 100% 50%` (Apple Blue `#007AFF`)

#### Scenario: shadcn destructive button
- **WHEN** a shadcn `Button` renders with `variant="destructive"`
- **THEN** it SHALL use `--destructive` which resolves to `4 90% 58%` (Apple Red `#FF3B30`)

### Requirement: shadcn CSS variable mapping in dark mode
The system SHALL override shadcn/ui CSS variables under `[data-theme="dark"]` with dark-appropriate HSL values.

#### Scenario: Dark mode background
- **WHEN** `data-theme="dark"` is active
- **THEN** `--background` SHALL resolve to `0 0% 11%` and `--foreground` to `0 0% 100%`

#### Scenario: Dark mode primary
- **WHEN** `data-theme="dark"` is active
- **THEN** `--primary` SHALL resolve to `211 100% 53%` (Apple Dark Blue `#0A84FF`)

### Requirement: shadcn radius consistency
The system SHALL set shadcn's `--radius` to `0.625rem` (10px) matching `var(--radius-md)`.

#### Scenario: shadcn component border radius
- **WHEN** a shadcn component uses the `--radius` variable
- **THEN** it SHALL render with 10px border radius

### Requirement: Install base shadcn components
The system SHALL include the following shadcn/ui components installed via CLI: `button`, `progress`, `badge`, `dialog`, `scroll-area`, `tooltip`.

#### Scenario: Component availability
- **WHEN** the project builds
- **THEN** all 6 shadcn components SHALL be available in `src/components/ui/`
