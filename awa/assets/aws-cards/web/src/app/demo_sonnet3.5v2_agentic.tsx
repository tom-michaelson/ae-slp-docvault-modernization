'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import InputAdornment from '@mui/material/InputAdornment';
import { styled } from '@mui/material/styles';

// Data Models
interface CalculatorInputs {
  purchaseAmount: number;
  promotionalPeriod: number;
  postPromotionalAPR: number;
  amountPaid: number;
}

interface CalculationResults {
  remainingBalance: number;
  interestCharged: number;
  totalAmountDue: number;
  isPaidInFull: boolean;
}

// Validation Rules
const VALIDATION_RULES = {
  purchaseAmount: {
    min: 0.01,
    max: 999999999.99,
    maxDigitsBeforeDecimal: 9,
    maxDigitsAfterDecimal: 2,
  },
  promotionalPeriod: {
    min: 1,
    max: 99,
    maxDigitsBeforeDecimal: 2,
    maxDigitsAfterDecimal: 0,
  },
  postPromotionalAPR: {
    min: 0,
    max: 99.99,
    maxDigitsBeforeDecimal: 2,
    maxDigitsAfterDecimal: 2,
  },
  amountPaid: {
    min: 0,
    max: 999999999.99,
    maxDigitsBeforeDecimal: 9,
    maxDigitsAfterDecimal: 2,
  },
};

// Utility Functions
const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercentage = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
};

// Validation Service
class InputValidator {
  static validateMonetaryValue(value: number, rules: typeof VALIDATION_RULES.purchaseAmount): boolean {
    if (isNaN(value)) return false;
    if (value < rules.min || value > rules.max) return false;

    const [before, after] = value.toString().split('.');
    if (before.length > rules.maxDigitsBeforeDecimal) return false;
    if (after && after.length > rules.maxDigitsAfterDecimal) return false;

    return true;
  }

  static validatePromotionalPeriod(value: number): boolean {
    return this.validateMonetaryValue(value, VALIDATION_RULES.promotionalPeriod);
  }

  static validateAPR(value: number): boolean {
    return this.validateMonetaryValue(value, VALIDATION_RULES.postPromotionalAPR);
  }
}

// Calculator Service
class DeferredInterestCalculator {
  static calculateResults(inputs: CalculatorInputs): CalculationResults {
    const remainingBalance = this.calculateRemainingBalance(
      inputs.purchaseAmount,
      inputs.amountPaid
    );

    const interestCharged = this.calculateInterest(
      inputs.purchaseAmount,
      inputs.postPromotionalAPR,
      remainingBalance
    );

    const totalAmountDue = remainingBalance + interestCharged;
    const isPaidInFull = remainingBalance <= 0;

    return {
      remainingBalance,
      interestCharged,
      totalAmountDue,
      isPaidInFull,
    };
  }

  private static calculateRemainingBalance(purchase: number, paid: number): number {
    return Number((purchase - paid).toFixed(2));
  }

  private static calculateInterest(
    purchase: number,
    apr: number,
    remainingBalance: number
  ): number {
    if (remainingBalance > 0) {
      return Number(((purchase * apr) / 100).toFixed(2));
    }
    return 0;
  }
}

// Styled Components
const ResultCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginTop: theme.spacing(3),
}));

// Main Component
export default function Page(): React.JSX.Element {
  // State Management
  const [inputs, setInputs] = React.useState<CalculatorInputs>({
    purchaseAmount: 0,
    promotionalPeriod: 12,
    postPromotionalAPR: 0,
    amountPaid: 0,
  });

  const [errors, setErrors] = React.useState<Partial<Record<keyof CalculatorInputs, string>>>({});
  const [results, setResults] = React.useState<CalculationResults | null>(null);

  // Input Handlers
  const handleInputChange = (field: keyof CalculatorInputs) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = parseFloat(event.target.value);
    setInputs((prev) => ({ ...prev, [field]: value }));
    validateField(field, value);
  };

  // Validation
  const validateField = (field: keyof CalculatorInputs, value: number) => {
    let isValid = true;
    let errorMessage = '';

    switch (field) {
      case 'purchaseAmount':
      case 'amountPaid':
        isValid = InputValidator.validateMonetaryValue(value, VALIDATION_RULES[field]);
        errorMessage = isValid ? '' : 'Invalid amount';
        break;
      case 'promotionalPeriod':
        isValid = InputValidator.validatePromotionalPeriod(value);
        errorMessage = isValid ? '' : 'Invalid period (1-99 months)';
        break;
      case 'postPromotionalAPR':
        isValid = InputValidator.validateAPR(value);
        errorMessage = isValid ? '' : 'Invalid APR (0-99.99%)';
        break;
    }

    setErrors((prev) => ({
      ...prev,
      [field]: errorMessage,
    }));

    return isValid;
  };

  // Calculate Results
  const handleCalculate = () => {
    // Validate all fields
    const isValid = Object.keys(inputs).every((key) =>
      validateField(key as keyof CalculatorInputs, inputs[key as keyof CalculatorInputs])
    );

    if (!isValid) return;

    try {
      const calculationResults = DeferredInterestCalculator.calculateResults(inputs);
      setResults(calculationResults);
    } catch (error) {
      console.error('Calculation error:', error);
    }
  };

  return (
    <Box
      sx={{
        maxWidth: 'var(--Content-maxWidth)',
        m: 'var(--Content-margin)',
        p: 'var(--Content-padding)',
        width: 'var(--Content-width)',
      }}
    >
      <Stack spacing={4}>
        <Typography variant="h4" component="h1">
          Deferred Interest Promotion Calculator
        </Typography>

        {/* Calculator Form */}
        <Stack spacing={3}>
          <TextField
            label="Purchase Amount"
            type="number"
            value={inputs.purchaseAmount}
            onChange={handleInputChange('purchaseAmount')}
            error={!!errors.purchaseAmount}
            helperText={errors.purchaseAmount}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
            }}
            inputProps={{
              'aria-label': 'Purchase Amount',
              step: '0.01',
              min: VALIDATION_RULES.purchaseAmount.min,
              max: VALIDATION_RULES.purchaseAmount.max,
            }}
          />

          <TextField
            label="Promotional Period (Months)"
            type="number"
            value={inputs.promotionalPeriod}
            onChange={handleInputChange('promotionalPeriod')}
            error={!!errors.promotionalPeriod}
            helperText={errors.promotionalPeriod}
            inputProps={{
              'aria-label': 'Promotional Period',
              step: '1',
              min: VALIDATION_RULES.promotionalPeriod.min,
              max: VALIDATION_RULES.promotionalPeriod.max,
            }}
          />

          <TextField
            label="Post-Promotional APR"
            type="number"
            value={inputs.postPromotionalAPR}
            onChange={handleInputChange('postPromotionalAPR')}
            error={!!errors.postPromotionalAPR}
            helperText={errors.postPromotionalAPR}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>,
            }}
            inputProps={{
              'aria-label': 'Post-Promotional APR',
              step: '0.01',
              min: VALIDATION_RULES.postPromotionalAPR.min,
              max: VALIDATION_RULES.postPromotionalAPR.max,
            }}
          />

          <TextField
            label="Amount Paid"
            type="number"
            value={inputs.amountPaid}
            onChange={handleInputChange('amountPaid')}
            error={!!errors.amountPaid}
            helperText={errors.amountPaid}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
            }}
            inputProps={{
              'aria-label': 'Amount Paid',
              step: '0.01',
              min: VALIDATION_RULES.amountPaid.min,
              max: VALIDATION_RULES.amountPaid.max,
            }}
          />

          <Button
            variant="contained"
            onClick={handleCalculate}
            disabled={Object.keys(errors).some((key) => !!errors[key as keyof CalculatorInputs])}
          >
            Calculate
          </Button>
        </Stack>

        {/* Results Display */}
        {results && (
          <ResultCard elevation={3}>
            <Stack spacing={2}>
              <Typography variant="h5">Results</Typography>

              {results.isPaidInFull ? (
                <Alert severity="success">
                  Congratulations! The purchase has been paid in full with no deferred interest charges.
                </Alert>
              ) : (
                <Alert severity="warning">
                  Remaining balance detected. Deferred interest will be charged.
                </Alert>
              )}

              <Typography>
                Remaining Balance: {formatCurrency(results.remainingBalance)}
              </Typography>

              <Typography>
                Interest Charged: {formatCurrency(results.interestCharged)}
              </Typography>

              <Typography variant="h6">
                Total Amount Due: {formatCurrency(results.totalAmountDue)}
              </Typography>
            </Stack>
          </ResultCard>
        )}
      </Stack>
    </Box>
  );
}
