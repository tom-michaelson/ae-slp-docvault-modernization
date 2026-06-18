//POSTTRAN JOB 'POSTTRAN',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID

//* *******************************************************************
//* Process and load daily transaction file and create transaction
//* category balance and update transaction master vsam
//* *******************************************************************
//STEP15 EXEC PGM=CBTRN02C
//STEPLIB  DD DISP=SHR,
//            DSN=AWS.M2.CARDDEMO.LOADLIB
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//TRANFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
//DALYTRAN DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.DALYTRAN.PS
//XREFFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
//DALYREJS DD DISP=(NEW,CATLG,DELETE),
//         UNIT=SYSDA,
//         DCB=(RECFM=F,LRECL=430,BLKSIZE=0),
//         SPACE=(CYL,(1,1),RLSE),
//         DSN=AWS.M2.CARDDEMO.DALYREJS(+1)
//ACCTFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
//TCATBALF DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:06 CDT
//*
