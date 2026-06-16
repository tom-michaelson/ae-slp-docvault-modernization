//DALYREJS JOB 'DEF GDG FOR REJS',CLASS=A,MSGCLASS=0,NOTIFY=&SYSUID

//* *******************************************************************
//* DELETE TRANSACATION MASTER VSAM FILE IF ONE ALREADY EXISTS
//* *******************************************************************
//STEP05 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.DALYREJS) -
    LIMIT(5) -
    SCRATCH -
   )
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:05 CDT
//*
