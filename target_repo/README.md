# `target_repo/`

The modernization target — Spring Boot (Java 25) API + Angular UI.

## What goes here

Re-implemented application code driven by
[`../docs/entry-points/`](../docs/README.md). Each legacy UI feature / API
endpoint maps to component(s) under `source/ui` and controller/service/repository
classes under `source/api`, following the per-item `technical-plan.md` the
develop workflow will generate.

## Relationship to the other trees

```
new-modernization-sdlc/
├── legacy/        (read-only input)     ← eShopOnWeb
├── docs/          (generated artifacts) ← awa-discover output
└── target_repo/   (writable output)     ← Angular + Spring Boot implementation
```

Flow: `legacy/` → `awa-discover` → `docs/` → `awa-develop` → `target_repo/`.

## Target stack

The develop workflow defaults to `target_stack: "angular-java"`. Override only
if you want per-phase slash commands to shape output differently:

```bash
uv run python -m awa workflow start awa-develop \
  --input '{"pages": ["homepage-catalog-list", "basket-view-page"]}'
```

## Structure

```
target_repo/
├── .claude/commands/       ← target-stack slash commands (see SPEC.md)
├── source/
│   ├── api/                ← Spring Boot app
│   │   ├── build.gradle
│   │   ├── settings.gradle
│   │   └── src/
│   │       ├── main/java/com/slalom/modernization/
│   │       │   ├── Application.java
│   │       │   ├── config/CacheConfig.java
│   │       │   └── controller/HelloController.java
│   │       ├── main/resources/application.yml
│   │       └── test/java/com/slalom/modernization/controller/HelloControllerTest.java
│   └── ui/                 ← Angular 19 app
│       ├── angular.json, package.json, tsconfig*.json
│       └── src/
│           ├── index.html, main.ts, styles.scss
│           └── app/
│               ├── app.component.ts   (header + hero + router-outlet + footer)
│               ├── app.config.ts, app.routes.ts
│               ├── layout/{header,hero-banner,footer}.component.ts
│               └── pages/{home,basket}/…   (placeholders, filled by workflow)
└── README.md
```

`.claude/commands/` holds the slash command definitions the discover + develop
workflows invoke — see `SPEC.md` in that folder for the contract.

## Requirements

Install the Playwright MCP so screenshot / visual-validation phases can drive
headless Chrome:

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

Windows:

```bash
claude mcp add --transport stdio playwright --scope local -- cmd /c npx @playwright/mcp@latest --headless
```

## `source/api` — Spring Boot app

Baseline Spring Boot 3.5 app with:

- **Java 25** (Gradle toolchain auto-downloads via Foojay resolver)
- **H2** in-memory database (`jdbc:h2:mem:modernization`), console at `/h2-console`
- **Caffeine** cache (`greetings`, 5-min TTL, 1000-item cap)
- `GET /hello?name=…` — sample cached endpoint
- JUnit 5 + MockMvc integration test

### One-time bootstrap

Gradle isn't installed locally; install it once to generate the wrapper, then
the wrapper takes over:

```bash
brew install gradle
cd target_repo/source/api
gradle wrapper --gradle-version 8.10
```

Java 25 is **not** required on `PATH` — the toolchain will fetch it on first
build. To install it yourself:

```bash
brew install openjdk@25    # or: sdk install java 25-open
```

### Run

```bash
cd target_repo/source/api
./gradlew bootRun
# -> http://localhost:8080/hello?name=Evan
# -> http://localhost:8080/h2-console
```

### Test

```bash
./gradlew test
```

## `source/ui` — Angular app

Angular 19 with standalone components. The layout mirrors the hosted eShopOnWeb
shell — header, hero banner, footer — with `<router-outlet>` in the middle for
per-page content. See [`source/ui/README.md`](./source/ui/README.md).

### First-time setup + run

```bash
cd target_repo/source/ui
npm install
npm start           # dev server on http://localhost:4200
npm run build
npm test
```
