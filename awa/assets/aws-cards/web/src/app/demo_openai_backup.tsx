'use client';
import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';

const DeferredInterestCalculator: React.FC = () => {
  const [purchaseAmount, setPurchaseAmount] = useState<number>(0);
  const [promotionalPeriod, setPromotionalPeriod] = useState<number>(0);
  const [apr, setApr] = useState<number>(0);
  const [amountPaid, setAmountPaid] = useState<number>(0);
  const [result, setResult] = useState<string>('');

  const calculate = () => {
    const remainingBalance = purchaseAmount - amountPaid;
    const retroactiveInterest = remainingBalance * (apr / 100) * (promotionalPeriod / 12);
    const totalDue = remainingBalance + retroactiveInterest;
    setResult(`Remaining Balance: $${remainingBalance.toFixed(2)}, Retroactive Interest: $${retroactiveInterest.toFixed(2)}, Total Due: $${totalDue.toFixed(2)}`);
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
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ alignItems: 'flex-start' }}>
          <Typography variant="h4">Deferred Interest Promotion Calculator</Typography>
        </Stack>
        <Stack spacing={2}>
          <TextField label="Purchase Amount" type="number" value={purchaseAmount} onChange={(e) => setPurchaseAmount(Number(e.target.value))} />
          <TextField label="Promotional Period (months)" type="number" value={promotionalPeriod} onChange={(e) => setPromotionalPeriod(Number(e.target.value))} />
          <TextField label="APR (%)" type="number" value={apr} onChange={(e) => setApr(Number(e.target.value))} />
          <TextField label="Amount Paid" type="number" value={amountPaid} onChange={(e) => setAmountPaid(Number(e.target.value))} />
          <Button variant="contained" onClick={calculate}>Calculate</Button>
          <Typography variant="body1">{result}</Typography>
        </Stack>
      </Stack>
    </Box>
  );
};

export default DeferredInterestCalculator;
