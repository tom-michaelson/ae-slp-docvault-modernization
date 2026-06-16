# UI Test Framework

This directory contains the Playwright-based UI testing framework for the AWA project.

## Directory Structure

```
tests/ui/
├── fixtures/          # Custom test fixtures
├── tests/            # Test specifications
├── utils/            # Utilities and helpers
│   ├── pages/        # Page Object Model classes
│   ├── helpers/      # Helper utilities
│   └── constants/    # Test constants
├── tsconfig.json     # TypeScript configuration with path aliases
└── playwright.config.ts
```

## Path Aliases

The framework uses TypeScript path aliases for cleaner imports:

- `@ui/*` → Points to `../../ui/src/*` (main UI source)
- `@pages/*` → Points to `utils/pages/*`
- `@helpers/*` → Points to `utils/helpers/*`
- `@fixtures/*` → Points to `fixtures/*`
- `@constants` → Points to `utils/constants`
- `@tests/*` → Points to `tests/*`

### Example Usage

Instead of:
```typescript
import { testId } from '../../../../ui/src/utils/constants';
import { HomePage } from '../utils/pages/home';
```

Use:
```typescript
import { testId } from '@ui/utils/constants';
import { HomePage } from '@pages/home';
```

## Running Tests

```bash
# Run all tests
make test-ui

# Run tests in headed mode
make test-ui-headed

# Run specific test file
npx playwright test tests/example.spec.ts

# Run tests with UI mode
npx playwright test --ui
```

## Key Features

1. **Page Object Model**: All page interactions are encapsulated in page objects
2. **Automatic Cleanup**: Tests automatically clean up after execution
3. **Parallel Execution Safe**: Tests can run in parallel without conflicts
4. **Page Validation**: All pages validate they're loaded before proceeding
5. **Custom Fixtures**: Reusable test setup and data generation

## Writing Tests

1. Use the custom test fixtures:
```typescript
import { test, expect } from '@fixtures/testFixtures';

test('my test', async ({ homePage, runsPage }) => {
  // Page objects are automatically available
});
```

2. All page objects validate loading:
```typescript
await homePage.goto(); // Automatically waits for page to be ready
```

3. Test data is generated with parallel safety:
```typescript
const uniqueId = TestDataHelpers.generateId(); // Worker-safe
```

## Best Practices

1. Always use page objects instead of direct selectors
2. Let automatic cleanup handle test isolation
3. Use the provided wait helpers instead of arbitrary timeouts
4. Leverage TypeScript path aliases for clean imports
5. Keep test data generation in TestDataHelpers
