'use client';
import React, { useState } from 'react';
import { Box, Stack, Typography, TextField, Button, Alert, Paper } from '@mui/material';

interface CalculationResult {
  remainingBalance: number;
  retroactiveInterest: number;
  totalAmountDue: number;
}

export default function DeferredInterestCalculator(): React.JSX.Element {
  const [purchaseAmount, setPurchaseAmount] = useState<string>('');
  const [promotionalPeriod, setPromotionalPeriod] = useState<string>('');
  const [apr, setApr] = useState<string>('');
  const [amountPaid, setAmountPaid] = useState<string>('');
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const calculateDeferredInterest = () => {
    setError(null);
    setResult(null);

    const purchase = parseFloat(purchaseAmount);
    const period = parseInt(promotionalPeriod);
    const rate = parseFloat(apr) / 100;
    const paid = parseFloat(amountPaid);

    if (isNaN(purchase) || isNaN(period) || isNaN(rate) || isNaN(paid)) {
      setError('Please enter valid numbers for all fields.');
      return;
    }

    if (purchase <= 0 || period <= 0 || rate <= 0 || paid < 0) {
      setError('Please enter positive values (amount paid can be zero).');
      return;
    }

    const remainingBalance = Math.max(0, purchase - paid);
    const retroactiveInterest = purchase * rate * (period / 12);
    const totalAmountDue = remainingBalance > 0 ? remainingBalance + retroactiveInterest : 0;

    setResult({
      remainingBalance: Number(remainingBalance.toFixed(2)),
      retroactiveInterest: Number(retroactiveInterest.toFixed(2)),
      totalAmountDue: Number(totalAmountDue.toFixed(2))
    });
  };

  return (
    <Box sx={{ maxWidth: 600, margin: 'auto', padding: 3 }}>
      <Paper elevation={3} sx={{ padding: 3 }}>
        <Stack spacing={3}>
          <Typography variant="h4" align="center">Deferred Interest Promotion Calculator</Typography>
          <TextField
            label="Purchase Amount ($)"
            type="number"
            value={purchaseAmount}
            onChange={(e) => setPurchaseAmount(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="Promotional Period (months)"
            type="number"
            value={promotionalPeriod}
            onChange={(e) => setPromotionalPeriod(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="APR (%)"
            type="number"
            value={apr}
            onChange={(e) => setApr(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="Amount Paid ($)"
            type="number"
            value={amountPaid}
            onChange={(e) => setAmountPaid(e.target.value)}
            fullWidth
            required
          />
          <Button
            variant="contained"
            onClick={calculateDeferredInterest}
            size="large"
          >
            Calculate
          </Button>
        </Stack>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
        )}
        {result && (
          <Paper elevation={1} sx={{ mt: 3, p: 2 }}>
            <Typography variant="h6" gutterBottom>Results:</Typography>
            <Typography>Remaining Balance: ${result.remainingBalance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</Typography>
            <Typography>Retroactive Interest: ${result.retroactiveInterest.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</Typography>
            <Typography>Total Amount Due: ${result.totalAmountDue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</Typography>
          </Paper>
        )}
      </Paper>
    </Box>
  );
}
