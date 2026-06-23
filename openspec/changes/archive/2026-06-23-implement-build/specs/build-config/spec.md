## ADDED Requirements

### Requirement: Vite config with path aliases
The system SHALL configure Vite with `@` → `./src` alias, port 1420, strict port, and ignore `src-tauri` in watch.

#### Scenario: Import from @/types
- **WHEN** a component imports `import { ConversionFile } from '@/types'`
- **THEN** Vite SHALL resolve to `./src/types/index.ts`

### Requirement: TypeScript strict config
The system SHALL configure TypeScript with `strict: true`, `noUnusedLocals: true`, `noUnusedParameters: true`, `paths: { "@/*": ["./src/*"] }`, target ES2020, and `moduleResolution: "bundler"`.

#### Scenario: Type checking
- **WHEN** `tsc --noEmit` runs
- **THEN** all files under `src/` SHALL be checked with strict rules

### Requirement: package.json scripts
The system SHALL provide scripts: `dev` (tauri dev), `build` (tauri build), `build:sidecar` (sidecar build), `build:all` (both), `preview`, `lint`, `type-check`, `test`.

#### Scenario: Full build
- **WHEN** `npm run build:all` is executed
- **THEN** the sidecar SHALL be compiled first, then the Tauri app
