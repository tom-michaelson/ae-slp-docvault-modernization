# Technical Specifications - Deferred Interest Calculator

## 1. Architecture Overview

### 1.1 System Architecture
The Deferred Interest Calculator will follow a layered architecture pattern with clear separation of concerns:

```plaintext
┌─────────────────────────────────────┐
│            Presentation            │
│  (React Components + Material UI)  │
├─────────────────────────────────────┤
│         Application Logic          │
│    (TypeScript Business Layer)     │
├─────────────────────────────────────┤
│          Domain Services           │
│     (Calculation Engine Core)      │
└─────────────────────────────────────┘
```

### 1.2 Technology Stack
- Frontend Framework: React 18+ with TypeScript
- UI Components: Material-UI (MUI) v5
- State Management: React Context API
- Testing: Jest + React Testing Library
- Build Tool: Vite
- Code Quality: ESLint + Prettier
- Documentation: TypeDoc

## 2. Component Specifications

### 2.1 Core Types and Interfaces

```typescript
interface CalculatorInputs {
  purchaseAmount: number;
  promotionalPeriod: number;
  postPromotionalAPR: number;
  monthlyPayment: number;
}

interface CalculationResult {
  purchaseAmount: number;
  totalPaid: number;
  remainingBalance: number;
  interestCharged: number | null;
  totalDue: number;
  isPaidInFull: boolean;
}

type ValidationError = {
  field: keyof CalculatorInputs;
  message: string;
}
```

### 2.2 Component Hierarchy

```plaintext
App
├── CalculatorProvider
│   └── CalculatorContext
├── CalculatorForm
│   ├── CurrencyInput
│   ├── NumberInput
│   └── SubmitButton
└── CalculatorResults
    ├── SummaryDisplay
    └── DetailedResults
```

## 3. Service Layer Specifications

### 3.1 Calculation Service

```typescript
class CalculationService {
  validateInputs(inputs: CalculatorInputs): ValidationError[];
  calculateResults(inputs: CalculatorInputs): CalculationResult;
  private calculateRemainingBalance(amount: number, totalPayments: number): number;
  private calculateRetroactiveInterest(amount: number, apr: number): number;
}
```

### 3.2 Validation Rules
- Purchase Amount: 0.01 to 999,999,999.99
- Promotional Period: 1 to 99 months
- APR: 0.00 to 99.99%
- Monthly Payment: 0.00 to 999,999,999.99

## 4. Data Flow

### 4.1 Input Processing Sequence
1. User inputs are collected via controlled components
2. Real-time validation occurs on input change
3. Form submission triggers comprehensive validation
4. Valid inputs are passed to calculation service
5. Results are stored in context and displayed

### 4.2 Calculation Sequence
1. Calculate total payments over promotional period
2. Determine remaining balance
3. Evaluate if interest should be charged
4. Calculate retroactive interest if applicable
5. Compute final total due amount

## 5. Implementation Details

### 5.1 Number Handling
- All calculations use decimal.js library to prevent floating-point errors
- Currency values maintain 2 decimal places throughout calculations
- Rounding follows half-up convention

### 5.2 Error Handling
- Input validation errors are displayed inline
- Calculation errors are caught and displayed as alerts
- Edge cases (overflow, underflow) are properly handled

## 6. Testing Strategy

### 6.1 Unit Tests
- Individual component rendering
- Calculation service methods
- Validation functions
- Context provider behavior

### 6.2 Integration Tests
- Form submission flow
- Context updates
- Error handling scenarios

### 6.3 Test Cases Matrix
- Edge cases for all inputs
- Boundary conditions
- Error scenarios
- Full payment scenarios
- Partial payment scenarios

## 7. Performance Considerations

### 7.1 Optimization Techniques
- Memoization of calculation results
- Debounced input validation
- Lazy loading of heavy components

### 7.2 Bundle Size
- Tree-shaking enabled
- Component code splitting
- Minimal external dependencies

## 8. Accessibility Requirements

### 8.1 WCAG Compliance
- ARIA labels for all inputs
- Keyboard navigation support
- Screen reader compatibility
- Color contrast requirements
- Error announcements

## 9. Security Considerations

### 9.1 Input Sanitization
- All numeric inputs are parsed and validated
- No external API calls required
- XSS prevention in display values

## 10. Deployment Specifications

### 10.1 Build Process
- Development, staging, and production builds
- Environment-specific configurations
- Build-time optimizations

### 10.2 Deployment Requirements
- Static file hosting
- CDN configuration
- Cache control headers
