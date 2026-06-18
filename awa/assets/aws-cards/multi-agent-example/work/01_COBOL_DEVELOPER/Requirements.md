# Deferred Interest Calculator - Business Requirements

## 1. Overview
The Deferred Interest Calculator is a financial application that calculates the outcome of deferred interest promotions on purchases. It determines whether interest will be charged based on payment completion during a promotional period.

## 2. Core Features

### 2.1 Input Requirements
- Accept purchase amount (numeric value with 2 decimal places)
- Accept promotional period duration (whole numbers in months)
- Accept post-promotional Annual Percentage Rate (APR)
- Accept monthly payment amount during the promotional period

### 2.2 Default Values
- Promotional period: 12 months if no value is provided
- Post-promotional APR: 18.00% if no value is provided

### 2.3 Calculation Requirements
The system must:
1. Calculate remaining balance after promotional period
   - Formula: `Remaining Balance = Purchase Amount - Amount Paid`
2. Determine interest charges based on payment completion
   - If balance remains: Calculate retroactive interest on original purchase amount
   - Formula for retroactive interest: `Interest = Purchase Amount × (APR ÷ 100)`
3. Calculate total amount due
   - If balance remains: `Total Due = Remaining Balance + Retroactive Interest`
   - If paid in full: `Total Due = Remaining Balance`

### 2.4 Display Requirements
The system must show:
1. Original purchase amount (formatted as currency)
2. Total amount paid (formatted as currency)
3. Remaining balance (formatted as currency)
4. When applicable:
   - Deferred interest charged (formatted as currency)
   - Total amount due (formatted as currency)
5. When paid in full:
   - Message indicating no interest charged

## 3. Business Rules

### 3.1 Interest Assessment
- Interest is charged only if a balance remains after the promotional period
- When charged, interest is calculated on the full original purchase amount
- No partial interest calculations are performed
- Interest is calculated for one year at the post-promotional APR

### 3.2 Payment Processing
- All payments are treated as a single lump sum
- Overpayments are allowed and will result in a negative remaining balance
- No minimum payment requirements are enforced

### 3.3 Data Validation
- Purchase amounts must be numeric and non-negative
- Promotional periods must be whole numbers
- APR must be numeric with up to 2 decimal places
- Payment amounts must be numeric and can be zero or positive

## 4. Technical Constraints
- Numbers support up to 9 digits before the decimal point
- Currency values support 2 decimal places
- APR values support 2 decimal places
- Promotional periods are limited to 2 digits (99 months maximum)

## 5. User Interface Requirements

### 5.1 Input Prompts
- "Enter Purchase Amount:"
- "Enter Promotional Period in Months:"
- "Enter Post-Promotion APR (Default is 18%):"
- "Enter Monthly payment [XX]:" (where XX is the promotional period)

### 5.2 Output Format
- Clear section headers with separating lines
- Currency values aligned and properly formatted with dollar signs and commas
- Distinct messaging for paid-in-full vs. interest-charged scenarios
