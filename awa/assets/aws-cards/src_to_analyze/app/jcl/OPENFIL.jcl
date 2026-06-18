//OEPNFIL JOB 'Open files in CICS',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID

//*********************************************************************
//* Open files in CICS region
//*********************************************************************
//OPCIFIL EXEC PGM=SDSF
//ISFOUT DD SYSOUT=*
//CMDOUT DD SYSOUT=*
//ISFIN  DD *
 /F CICSAWSA,'CEMT SET FIL(TRANSACT ) OPE'
 /F CICSAWSA,'CEMT SET FIL(CCXREF ) OPE'
 /F CICSAWSA,'CEMT SET FIL(ACCTDAT ) OPE'
 /F CICSAWSA,'CEMT SET FIL(CXACAIX ) OPE'
 /F CICSAWSA,'CEMT SET FIL(USRSEC ) OPE'
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:06 CDT
//*
