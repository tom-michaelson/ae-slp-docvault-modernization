//COMBTRAN JOB 'COMBINE TRANSACTIONS',CLASS=A,MSGCLASS=0,
//  NOTIFY=&SYSUID

//* *******************************************************************
//* Sort current transaction file and system generated transactions
//* *******************************************************************
//STEP05R  EXEC PGM=SORT
//SORTIN   DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TRANSACT.BKUP(0)
//         DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.SYSTRAN(0)
//SYMNAMES DD *
TRAN-ID,1,16,CH
//SYSIN    DD *
 SORT FIELDS=(TRAN-ID,A)
/*
//SYSOUT   DD SYSOUT=*
//SORTOUT  DD DISP=(NEW,CATLG,DELETE),
//         UNIT=SYSDA,
//         DCB=(*.SORTIN),
//         SPACE=(CYL,(1,1),RLSE),
//         DSN=AWS.M2.CARDDEMO.TRANSACT.COMBINED(+1)
//* *******************************************************************
//* Load combined file to transaction master
//* *******************************************************************
//STEP10 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//TRANSACT DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TRANSACT.COMBINED(+1)
//TRANVSAM DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
//SYSIN    DD   *
   REPRO INFILE(TRANSACT) OUTFILE(TRANVSAM)
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:05 CDT
//*
