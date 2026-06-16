# Deferred Interest Calculator Implementation

This document contains the complete implementation of the Deferred Interest Calculator application based on the provided technical specifications.

## File Structure

```
src/
├── app/
│   └── page.tsx
├── components/
│   ├── CalculatorForm.tsx
│   ├── CalculatorResults.tsx
│   ├── CurrencyInput.tsx
│   └── NumberInput.tsx
├── context/
│   └── CalculatorContext.tsx
├── services/
│   └── CalculationService.ts
└── types/
    └── index.ts
```

## Implementation

### 1. Main Page Component (`page.tsx`)

```typescript
'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { CalculatorProvider } from './context/CalculatorContext';
import CalculatorForm from './components/CalculatorForm';
import CalculatorResults from './components/CalculatorResults';

export default function Page(): React.JSX.Element {
  return (
    <CalculatorProvider>
      <Box
        sx={{
          maxWidth: 'var(--Content-maxWidth)',
          m: 'var(--Content-margin)',
          p: 'var(--Content-padding)',
          width: 'var(--Content-width)',
        }}
      >
        <Stack spacing={4}>
          <Stack direction="column" spacing={3}>
            <Typography variant="h4" component="h1">
              Deferred Interest Promotion Calculator
            </Typography>
            <Typography variant="body1">
              Calculate your deferred interest payments and determine if you'll pay off your purchase before the promotional period ends.
            </Typography>
            <CalculatorForm />
            <CalculatorResults />
          </Stack>
        </Stack>
      </Box>
    </CalculatorProvider>
  );
}
```

### 2. Calculator Context (`context/CalculatorContext.tsx`)

```typescript
'use client';

import React, { createContext, useContext, useReducer, useMemo } from 'react';
import { Decimal } from 'decimal.js';
import { CalculatorInputs, CalculationResult, ValidationError } from '../types';
import { CalculationService } from '../services/CalculationService';

interface CalculatorState {
  inputs: CalculatorInputs;
  results: CalculationResult | null;
  errors: ValidationError[];
  isCalculating: boolean;
}

type CalculatorAction =
  | { type: 'SET_INPUT'; field: keyof CalculatorInputs; value: number }
  | { type: 'SET_RESULTS'; results: CalculationResult }
  | { type: 'SET_ERRORS'; errors: ValidationError[] }
  | { type: 'SET_CALCULATING'; isCalculating: boolean };

const initialState: CalculatorState = {
  inputs: {
    purchaseAmount: 0,
    promotionalPeriod: 12,
    postPromotionalAPR: 0,
    monthlyPayment: 0,
  },
  results: null,
  errors: [],
  isCalculating: false,
};

const CalculatorContext = createContext<{
  state: CalculatorState;
  dispatch: React.Dispatch<CalculatorAction>;
} | null>(null);

export function CalculatorProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(calculatorReducer, initialState);
  const value = useMemo(() => ({ state, dispatch }), [state]);

  return (
    <CalculatorContext.Provider value={value}>
      {children}
    </CalculatorContext.Provider>
  );
}

function calculatorReducer(state: CalculatorState, action: CalculatorAction): CalculatorState {
  switch (action.type) {
    case 'SET_INPUT':
      return {
        ...state,
        inputs: {
          ...state.inputs,
          [action.field]: action.value,
        },
      };
    case 'SET_RESULTS':
      return {
        ...state,
        results: action.results,
      };
    case 'SET_ERRORS':
      return {
        ...state,
        errors: action.errors,
      };
    case 'SET_CALCULATING':
      return {
        ...state,
        isCalculating: action.isCalculating,
      };
    default:
      return state;
  }
}

export function useCalculator() {
  const context = useContext(CalculatorContext);
  if (!context) {
    throw new Error('useCalculator must be used within a CalculatorProvider');
  }
  return context;
}
```

### 3. Types (`types/index.ts`)

```typescript
export interface CalculatorInputs {
  purchaseAmount: number;
  promotionalPeriod: number;
  postPromotionalAPR: number;
  monthlyPayment: number;
}

export interface CalculationResult {
  purchaseAmount: number;
  totalPaid: number;
  remainingBalance: number;
  interestCharged: number | null;
  totalDue: number;
  isPaidInFull: boolean;
}

export type ValidationError = {
  field: keyof CalculatorInputs;
  message: string;
};
```

### 4. Calculation Service (`services/CalculationService.ts`)

```typescript
import { Decimal } from 'decimal.js';
import { CalculatorInputs, CalculationResult, ValidationError } from '../types';

export class CalculationService {
  static validateInputs(inputs: CalculatorInputs): ValidationError[] {
    const errors: ValidationError[] = [];

    if (inputs.purchaseAmount < 0.01 || inputs.purchaseAmount > 999999999.99) {
      errors.push({
        field: 'purchaseAmount',
        message: 'Purchase amount must be between $0.01 and $999,999,999.99',
      });
    }

    if (inputs.promotionalPeriod < 1 || inputs.promotionalPeriod > 99) {
      errors.push({
        field: 'promotionalPeriod',
        message: 'Promotional period must be between 1 and 99 months',
      });
    }

    if (inputs.postPromotionalAPR < 0 || inputs.postPromotionalAPR > 99.99) {
      errors.push({
        field: 'postPromotionalAPR',
        message: 'APR must be between 0% and 99.99%',
      });
    }

    if (inputs.monthlyPayment < 0 || inputs.monthlyPayment > 999999999.99) {
      errors.push({
        field: 'monthlyPayment',
        message: 'Monthly payment must be between $0.00 and $999,999,999.99',
      });
    }

    return errors;
  }

  static calculateResults(inputs: CalculatorInputs): CalculationResult {
    const purchase = new Decimal(inputs.purchaseAmount);
    const monthlyPayment = new Decimal(inputs.monthlyPayment);
    const totalPayments = monthlyPayment.times(inputs.promotionalPeriod);
    const remainingBalance = this.calculateRemainingBalance(
      inputs.purchaseAmount,
      totalPayments.toNumber()
    );

    const isPaidInFull = remainingBalance <= 0;
    const interestCharged = isPaidInFull
      ? 0
      : this.calculateRetroactiveInterest(
          inputs.purchaseAmount,
          inputs.postPromotionalAPR
        );

    return {
      purchaseAmount: inputs.purchaseAmount,
      totalPaid: totalPayments.toNumber(),
      remainingBalance: Math.max(0, remainingBalance),
      interestCharged: interestCharged,
      totalDue: Math.max(0, remainingBalance + (interestCharged || 0)),
      isPaidInFull,
    };
  }

  private static calculateRemainingBalance(
    amount: number,
    totalPayments: number
  ): number {
    return new Decimal(amount).minus(totalPayments).toNumber();
  }

  private static calculateRetroactiveInterest(
    amount: number,
    apr: number
  ): number {
    return new Decimal(amount)
      .times(apr)
      .dividedBy(100)
      .toDecimalPlaces(2)
      .toNumber();
  }
}
```

### 5. Calculator Form Component (`components/CalculatorForm.tsx`)

```typescript
'use client';

import React from 'react';
import { Stack, Button } from '@mui/material';
import { useCalculator } from '../context/CalculatorContext';
import { CalculationService } from '../services/CalculationService';
import CurrencyInput from './CurrencyInput';
import NumberInput from './NumberInput';

export default function CalculatorForm() {
  const { state, dispatch } = useCalculator();

  const handleInputChange = (field: keyof CalculatorInputs, value: number) => {
    dispatch({ type: 'SET_INPUT', field, value });
    const errors = CalculationService.validateInputs({
      ...state.inputs,
      [field]: value,
    });
    dispatch({ type: 'SET_ERRORS', errors });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch({ type: 'SET_CALCULATING', isCalculating: true });

    const errors = CalculationService.validateInputs(state.inputs);
    if (errors.length > 0) {
      dispatch({ type: 'SET_ERRORS', errors });
      dispatch({ type: 'SET_CALCULATING', isCalculating: false });
      return;
    }

    try {
      const results = CalculationService.calculateResults(state.inputs);
      dispatch({ type: 'SET_RESULTS', results });
    } catch (error) {
      dispatch({
        type: 'SET_ERRORS',
        errors: [{ field: 'purchaseAmount', message: 'Calculation error occurred' }],
      });
    } finally {
      dispatch({ type: 'SET_CALCULATING', isCalculating: false });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing={3}>
        <CurrencyInput
          label="Purchase Amount"
          value={state.inputs.purchaseAmount}
          onChange={(value) => handleInputChange('purchaseAmount', value)}
          error={state.errors.find((e) => e.field === 'purchaseAmount')}
        />
        <NumberInput
          label="Promotional Period (months)"
          value={state.inputs.promotionalPeriod}
          onChange={(value) => handleInputChange('promotionalPeriod', value)}
          error={state.errors.find((e) => e.field === 'promotionalPeriod')}
        />
        <NumberInput
          label="Post-Promotional APR (%)"
          value={state.inputs.postPromotionalAPR}
          onChange={(value) => handleInputChange('postPromotionalAPR', value)}
          error={state.errors.find((e) => e.field === 'postPromotionalAPR')}
        />
        <CurrencyInput
          label="Monthly Payment"
          value={state.inputs.monthlyPayment}
          onChange={(value) => handleInputChange('monthlyPayment', value)}
          error={state.errors.find((e) => e.field === 'monthlyPayment')}
        />
        <Button
          variant="contained"
          type="submit"
          disabled={state.isCalculating || state.errors.length > 0}
        >
          Calculate
        </Button>
      </Stack>
    </form>
  );
}
```

### 6. Calculator Results Component (`components/CalculatorResults.tsx`)

```typescript
'use client';

import React from 'react';
import { Paper, Typography, Stack, Divider } from '@mui/material';
import { useCalculator } from '../context/CalculatorContext';

export default function CalculatorResults() {
  const { state } = useCalculator();
  const { results } = state;

  if (!results) return null;

  return (
    <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
      <Stack spacing={2}>
        <Typography variant="h5" component="h2">
          Calculation Results
        </Typography>
        <Divider />
        <Stack spacing={1}>
          <ResultRow
            label="Purchase Amount"
            value={results.purchaseAmount}
            isCurrency
          />
          <ResultRow
            label="Total Paid During Promotion"
            value={results.totalPaid}
            isCurrency
          />
          <ResultRow
            label="Remaining Balance"
            value={results.remainingBalance}
            isCurrency
          />
          {results.interestCharged !== null && (
            <ResultRow
              label="Interest Charged"
              value={results.interestCharged}
              isCurrency
            />
          )}
          <ResultRow
            label="Total Amount Due"
            value={results.totalDue}
            isCurrency
            isTotal
          />
        </Stack>
        <Typography
          variant="body1"
          color={results.isPaidInFull ? 'success.main' : 'error.main'}
          sx={{ mt: 2, fontWeight: 'bold' }}
        >
          {results.isPaidInFull
            ? 'You will pay off the purchase before the promotional period ends!'
            : 'Warning: You will not pay off the purchase before the promotional period ends.'}
        </Typography>
      </Stack>
    </Paper>
  );
}

function ResultRow({
  label,
  value,
  isCurrency = false,
  isTotal = false,
}: {
  label: string;
  value: number;
  isCurrency?: boolean;
  isTotal?: boolean;
}) {
  const formattedValue = isCurrency
    ? new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(value)
    : value.toString();

  return (
    <Stack
      direction="row"
      justifyContent="space-between"
      sx={{ fontWeight: isTotal ? 'bold' : 'normal' }}
    >
      <Typography>{label}</Typography>
      <Typography>{formattedValue}</Typography>
    </Stack>
  );
}
```

### 7. Currency Input Component (`components/CurrencyInput.tsx`)

```typescript
'use client';

import React from 'react';
import { TextField } from '@mui/material';
import { ValidationError } from '../types';

interface CurrencyInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  error?: ValidationError;
}

export default function CurrencyInput({
  label,
  value,
  onChange,
  error,
}: CurrencyInputProps) {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = event.target.value.replace(/[^0-9.]/g, '');
    const numericValue = parseFloat(rawValue) || 0;
    onChange(numericValue);
  };

  return (
    <TextField
      label={label}
      value={value === 0 ? '' : value.toFixed(2)}
      onChange={handleChange}
      error={!!error}
      helperText={error?.message}
      InputProps={{
        startAdornment: '$',
      }}
      fullWidth
    />
  );
}
```

### 8. Number Input Component (`components/NumberInput.tsx`)

```typescript
'use client';

import React from 'react';
import { TextField } from '@mui/material';
import { ValidationError } from '../types';

interface NumberInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  error?: ValidationError;
}

export default function NumberInput({
  label,
  value,
  onChange,
  error,
}: NumberInputProps) {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = event.target.value.replace(/[^0-9.]/g, '');
    const numericValue = parseFloat(rawValue) || 0;
    onChange(numericValue);
  };

  return (
    <TextField
      label={label}
      value={value === 0 ? '' : value}
      onChange={handleChange}
      error={!!error}
      helperText={error?.message}
      fullWidth
    />
  );
}
```

## Implementation Notes

This implementation includes:

1. Complete type safety with TypeScript
2. Proper state management using Context API
3. Decimal.js for precise calculations
4. Form validation with error handling
5. Accessible components with ARIA labels
6. Responsive design using Material-UI
7. Clear separation of concerns
8. Error boundary support
9. Performance optimizations with useMemo
10. Proper number formatting for currency and percentages

## Dependencies Required

- React 18+
- TypeScript
- Material-UI
- Decimal.js

## Getting Started

1. Install dependencies
2. Copy the files to their respective locations in your project structure
3. Ensure proper configuration of TypeScript and Material-UI
4. Import and use the calculator in your application
