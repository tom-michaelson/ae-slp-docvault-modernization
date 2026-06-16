//READXREF JOB 'Read Cross Ref file',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID

//* *******************************************************************
//* RUN THE PROGRAM THAT READS THE XREF MASTER VSAM FILE
//* *******************************************************************
//STEP05 EXEC PGM=CBACT03C
//STEPLIB  DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.LOADLIB
//XREFFILE DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
//SYSOUT   DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:07 CDT
//*
