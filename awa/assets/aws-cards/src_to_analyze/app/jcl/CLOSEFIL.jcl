//CLOSEFIL JOB 'Close files in CICS',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID

//*********************************************************************
//* Close files in CICS region
//*********************************************************************
//CLCIFIL EXEC PGM=SDSF
//ISFOUT DD SYSOUT=*
//CMDOUT DD SYSOUT=*
//ISFIN  DD *
 /F CICSAWSA,'CEMT SET FIL(TRANSACT ) CLO'
 /F CICSAWSA,'CEMT SET FIL(CCXREF ) CLO'
 /F CICSAWSA,'CEMT SET FIL(ACCTDAT ) CLO'
 /F CICSAWSA,'CEMT SET FIL(CXACAIX ) CLO'
 /F CICSAWSA,'CEMT SET FIL(USRSEC ) CLO'
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:05 CDT
//*
