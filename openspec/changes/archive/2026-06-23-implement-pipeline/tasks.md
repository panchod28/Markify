## 1. Sanitizer Update

- [x] 1.1 Update `src/lib/sanitizer.ts` — use NFD normalization, include dots in step 7, trim dots+underscores in step 9, use fallback `'archivo_sin_nombre'`, extract stem first, match 10-step algorithm exactly

## 2. Validation Order Verification

- [x] 2.1 Verify `useConversionStore.addFiles()` validation order matches spec: too_many_files stops immediately, others continue per-file

## 3. TypeScript Check

- [x] 3.1 Run `npx tsc --noEmit` to verify compilation
