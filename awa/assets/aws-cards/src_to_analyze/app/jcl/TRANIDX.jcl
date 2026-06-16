//TRANIDX JOB 'Define AIX on Transaction Master',CLASS=A,MSGCLASS=0,
//  NOTIFY=&SYSUID

//*-------------------------------------------------------------------*
//* CREATE ALTERNATE INDEX ON PROCESSED TIMESTAMP
//*-------------------------------------------------------------------*
//STEP20  EXEC PGM=IDCAMS
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  *
   DEFINE ALTERNATEINDEX (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX)-
   RELATE(AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS)                    -
   KEYS(26 304)                                                  -
   NONUNIQUEKEY                                                  -
   UPGRADE                                                       -
   RECORDSIZE(350,350)                                           -
   VOLUMES(AWSHJ1)                                               -
   CYLINDERS(5,1))                                               -
   DATA (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX.DATA))           -
   INDEX (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX.INDEX))
/*
//*-------------------------------------------------------------------*
//* DEFINE PATH IS USED TO RELATE THE ALTERNATE INDEX TO BASE CLUSTER
//*-------------------------------------------------------------------*
//STEP25  EXEC PGM=IDCAMS
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  *
  DEFINE PATH                                           -
   (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX.PATH)        -
    PATHENTRY(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX))
/*
//*------------------------------------------------------------------
//* BUILD ALTERNATE INDEX CLUSTER
//*-------------------------------------------------------------------*
//STEP30  EXEC PGM=IDCAMS
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  *
   BLDINDEX                                                      -
   INDATASET(AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS)                 -
   OUTDATASET(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX)
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:08 CDT
//*
