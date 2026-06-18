//TCATBALF JOB 'DEFINE TRANCAT BAL',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID

//* *******************************************************************
//* DELETE TRANSACTION CATEGORY BALANCE VSAM FILE IF ONE ALREADY EXISTS
//* *******************************************************************
//STEP05 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DELETE AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS -
          CLUSTER
   SET    MAXCC = 0
/*
//*
//* *******************************************************************
//* DEFINE TRANSACTION CATEGORY BALANCE VSAM FILE
//* *******************************************************************
//STEP10 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS) -
          CYLINDERS(1 5) -
          VOLUMES(AWSHJ1 -
          ) -
          KEYS(17 0) -
          RECORDSIZE(50 50) -
          SHAREOPTIONS(2 3) -
          ERASE -
          INDEXED -
          ) -
          DATA (NAME(AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS.DATA) -
          ) -
          INDEX (NAME(AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS.INDEX) -
          )
/*
//* *******************************************************************
//* COPY DATA FROM FLAT FILE TO VSAM FILE
//* *******************************************************************
//STEP15 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//TCATBAL DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.TCATBALF.PS
//TCATBALV DD DISP=OLD,
//         DSN=AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS
//SYSIN    DD   *
   REPRO INFILE(TCATBAL) OUTFILE(TCATBALV)
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:07 CDT
//*
