       IDENTIFICATION DIVISION.
       PROGRAM-ID. DEFERRED-INTEREST-CALC.
       ENVIRONMENT DIVISION.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           77  PCH-AMT                     PIC 9(9)V99 VALUE 0.
           77  PROMO-PERIOD-MONTHS         PIC 99     VALUE 12.
           77  POST-PROMO-APR              PIC 99V99  VALUE 18.00.
           77  AMOUNT-PAID                 PIC 9(9)V99 VALUE 0.
           77  REMAINING-BALANCE           PIC 9(9)V99 VALUE 0.
           77  RET-INTEREST                PIC 9(9)V99 VALUE 0.
           77  TOTAL-DUE                   PIC 9(9)V99 VALUE 0.
           77  WS-NEW-LINE                 PIC X       VALUE SPACE.
           77  PCH-AMT-DISPLAY             PIC $9,999,999.99.
           77  AMOUNT-PAID-DISPLAY         PIC $9,999,999.99.
           77  REMAINING-BALANCE-DISPLAY   PIC $9,999,999.99.
           77  RET-INTEREST-DISPLAY        PIC $9,999,999.99.
           77  TOTAL-DUE-DISPLAY           PIC $9,999,999.99.
           77  PROMO-PERIOD-DISPLAY        PIC Z9.
       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           PERFORM GET-USER-INPUT.
           PERFORM CALCULATE-BALANCE.
           PERFORM DISPLAY-RESULTS.
           STOP RUN.
       GET-USER-INPUT.
           DISPLAY "Deferred Interest Promotion Calculator".
           DISPLAY "---------------------------------------".
           DISPLAY WS-NEW-LINE.
           DISPLAY "Enter Purchase Amount: " WITH NO ADVANCING.
           ACCEPT PCH-AMT.
           DISPLAY "Enter Promotional Period in Months: "
           -      WITH NO ADVANCING.
           ACCEPT PROMO-PERIOD-MONTHS.
           IF PROMO-PERIOD-MONTHS = ZERO
               MOVE 12 TO PROMO-PERIOD-MONTHS.
           END-IF.
           DISPLAY "Enter Post-Promotion APR (Default is 18%): "
           -      WITH NO ADVANCING.
           ACCEPT POST-PROMO-APR.
           IF POST-PROMO-APR = ZERO
               MOVE 18.00 TO POST-PROMO-APR.
           END-IF.
           MOVE PROMO-PERIOD-MONTHS TO PROMO-PERIOD-DISPLAY.
           DISPLAY "Enter Monthly payment " PROMO-PERIOD-DISPLAY ": "
           -      WITH NO ADVANCING.
           ACCEPT AMOUNT-PAID.
       CALCULATE-BALANCE.
           COMPUTE REMAINING-BALANCE = PCH-AMT - AMOUNT-PAID.
           IF REMAINING-BALANCE > ZERO
               DISPLAY "Balance not fully paid during promotion period."
               COMPUTE RET-INTEREST = PCH-AMT * (POST-PROMO-APR / 100).
               COMPUTE TOTAL-DUE = REMAINING-BALANCE + RET-INTEREST.
           ELSE
               MOVE ZERO TO RET-INTEREST.
               MOVE REMAINING-BALANCE TO TOTAL-DUE.
           END-IF.
       DISPLAY-RESULTS.
           DISPLAY WS-NEW-LINE.
           DISPLAY "Calculation Results:".
           DISPLAY "--------------------".
           MOVE PCH-AMT TO PCH-AMT-DISPLAY.
           DISPLAY "Purchase Amount:      " PCH-AMT-DISPLAY.
           MOVE AMOUNT-PAID TO AMOUNT-PAID-DISPLAY.
           DISPLAY "Amount Paid:          " AMOUNT-PAID-DISPLAY.
           MOVE REMAINING-BALANCE TO REMAINING-BALANCE-DISPLAY.
           DISPLAY "Remaining Balance:    " REMAINING-BALANCE-DISPLAY.
           IF RET-INTEREST > ZERO
               MOVE RET-INTEREST TO RET-INTEREST-DISPLAY.
               DISPLAY "Deferred Interest Charged: "
               -      RET-INTEREST-DISPLAY.
               MOVE TOTAL-DUE TO TOTAL-DUE-DISPLAY.
               DISPLAY "Total Due:           " TOTAL-DUE-DISPLAY.
           ELSE
               DISPLAY "No interest charged. Balance paid in full."
           END-IF.
       END PROGRAM DEFERRED-INTEREST-CALC.
