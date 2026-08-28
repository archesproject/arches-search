# Arches Vue Style Guide

Source: https://arches.readthedocs.io/en/latest/developing/vue/arches-vue-styleguide/

Rules for writing/reviewing Vue code in this repo. Builds on the official Vue.js and TypeScript style guides.

## Directory & file naming

- Arches entity dirs: plural, lowercase (`cards/`, `widgets/`, `reports/`).
- Vue component dirs: PascalCase, one folder per component (`CustomComponent/`).
- Non-Vue utility dirs: kebab-case (`custom-utility/`, `date-utils/`).
- Vue component files: PascalCase + `.vue` (`UserCard.vue`).
- Utilities/helpers: kebab-case + `.js`/`.ts` (`fetch-api.ts`, `format-date.js`).
- Shared types: `types.ts`, placed next to the files that share them, or at app root if global.
- Component sub-components live in a `components/` subfolder of the parent; components shared by multiple parents move up to `components/` at the nearest common ancestor.

Example layout:
```
src/
└── project_name/
    ├── plugins/
    ├── reports/
    │   └── CustomReport/
    │       ├── components/
    │       └── CustomReport.vue
    ├── widgets/
    ├── types/
    └── utils.ts
```

## Component structure

- Single-File Components only (`<script>` + `<template>` + `<style>`).
- Single responsibility per component; decompose large components rather than overload one.
- Slots: scoped slots when the consumer needs slot data, plain named slots for simple content projection. Name slots by purpose. Shorthand (`#header`, `#row="{ row }"`) is fine.

## Data flow & state — escalate only as needed

1. **Props & emits** — default for parent/child, shallow trees.
2. **provide/inject** — deep trees, avoids prop drilling; the providing component owns the state.
3. **Composables** — shared fetch logic / reactive utilities across unrelated components. Each call site gets its own reactive instance unless explicitly shared.
4. **Pinia** — only for genuinely global state, state needed outside components, required persistence, or multi-tree access.

Other rules:

- Fetch data as close to the consumer as possible; lift shared fetch logic into a composable rather than a store.
- Pass primitives, not whole objects (`label="selectedResource.displayName"`, not `resource="selectedResource"`).
- If a component's only job is deriving/summarizing data, pass it raw data and compute internally. If multiple children need the same computed value, compute once in the parent and pass primitives down.
- Emit semantic, kebab-case event names with typed payloads via `defineEmits`:

```typescript
const ROW_SELECTED_EVENT = 'row-selected' as const;
interface RowSelectedEvent { rowId: number }
const emit = defineEmits<{
    (event: typeof ROW_SELECTED_EVENT, payload: RowSelectedEvent): void
}>();
```

## `<script>` tag

- `<script setup lang="ts">` always; all logic scoped to the component.
- Named `function` declarations for methods; arrow functions only for inline callbacks (`setTimeout`, `.then`, `.filter`, `onMounted`, `computed`, etc.).
- `SCREAMING_SNAKE_CASE` for fixed values; extract magic numbers and repeated/non-obvious string literals as named constants.
- Descriptive identifiers — no single-letter variable names.
- Extract non-UI logic (data transforms, business rules) into composables/utility modules — keep it out of the component.
- No side effects at module scope. Use `watchEffect` for data fetching (runs immediately, reruns on reactive deps). Use `onMounted` only for DOM-dependent work. Wrap async calls in `try/catch` with explicit error handling.
- No `any`. Import/use explicit types. Annotate function return types.

### Import order

1. Vue core (`vue`)
2. Third-party modules
3. Vue components (third-party → arches core → arches applications → local)
4. Utilities/composables (same hierarchy)
5. Types (same hierarchy)

Use `@/…` aliases for all local imports — never raw relative paths (`../../`).

### Declaration order inside `<script setup>`

1. Static constants
2. `defineProps`
3. `defineEmits` / `defineExpose`
4. Dependency injection (`inject`)
5. Composables/utilities setup
6. Component state (`ref`/`reactive`)
7. Computed properties
8. Watchers
9. Lifecycle hooks
10. Methods/functions

## `<template>` tag

### Attribute order

1. Directives (`v-for`, `v-if`)
2. Slots (`v-slot:header="…"`)
3. Static attributes (`id`, `class`)
4. Dynamic props (`:prop="…"`)
5. Event listeners (`@click="…"`)

- 1 attribute → same line as tag. 2+ attributes → one per line, indented.
- Always explicit assignment (`prop="value"`, `:prop="value"`) — no shorthand booleans.
- Attribute names (incl. custom props/events) are kebab-case.
- Self-close tags with no children: `<LogoIcon />`, `<img src="…" alt="…" />`.
- Simple ternaries OK in templates; move compound/nested ternaries, chained calls, or heavy expressions to a computed or method.
- No loose text nodes — wrap plain text in `<span>` or a semantic tag.

### i18n

- Wrap all user-facing strings in `$gettext()`.
- Runtime values: use `%{placeholder}` syntax + a values object as the second arg. Never concatenate translated strings.
- `interpolate()`: omit the third arg (HTML-escape) when the translation is rendered via `v-html`; pass `true` as the third arg when a substituted value may contain literal `<`/`>` (e.g. "Aircraft <by type>").

## `<style>` tag

- `<style scoped>` by default.
- `display: flex` for 1-D layout, `display: grid` for 2-D. Use `gap` for spacing, not margins. No `float`.
- Units: `rem` for spacing/typography/gaps/borders. `vh`/`vw` only for viewport-spanning elements. `%` for fluid layouts. **No `px`.**
- Logical properties only (`margin-inline-start`, `margin-block-start`), never physical (`margin-left`). **No negative margins.**
- No `calc()` where flex/grid already solves the layout; don't mix `calc()` with hardcoded values.
- Design tokens only — no raw color values. Centralize tokens in one theme file; build semantic layers on top (`--color-success`). Define light/dark variants. PrimeVue tokens are available as `--p-` prefixed CSS custom properties.
- Selector naming: prefix with the component root class, then chain descendants:

```css
.user-card { display: flex; }
.user-card .header { display: grid; }
.user-card .header .title { color: var(--p-primary-500); }
```

## Testing

- Co-locate test files next to the component; suffix `.spec.ts`.
- Vitest + Vue Test Utils. Prefer mounting real children; stub only external services / libraries that are hard to mount in jsdom.
- Cover all code paths: error states, conditional rendering, emitted events.
- Descriptive test names; group with `describe`.
- Use `await flushPromises()` / `await nextTick()` after triggering async updates.

```bash
npm run vitest                                            # all tests
npm run vitest -- src/components/CounterButton.spec.ts    # one file
npm run vitest -- --watch
npm run vitest -- --coverage
```
