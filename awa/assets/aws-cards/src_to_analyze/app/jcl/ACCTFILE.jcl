//ACCTFILE JOB 'Delete define Account Data',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID
//* *******************************************************************
//* DELETE ACCOUNT VSAM FILE IF ONE ALREADY EXISTS
//* *******************************************************************
//STEP05 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DELETE AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS -
          CLUSTER
   IF MAXCC LE 08 THEN SET MAXCC = 0
/*
//*
//* *******************************************************************
//* DEFINE ACCOUNT VSAM FILE
//* *******************************************************************
//STEP10 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS) -
          CYLINDERS(1 5) -
          VOLUMES(AWSHJ1 -
          ) -
          KEYS(11 0) -
          RECORDSIZE(300 300) -
          SHAREOPTIONS(2 3) -
          ERASE -
          INDEXED -
          ) -
          DATA (NAME(AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS.DATA) -
          ) -
          INDEX (NAME(AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS.INDEX) -
          )
/*
//* *******************************************************************
//* COPY DATA FROM FLAT FILE TO VSAM FILE
//* *******************************************************************
//STEP15 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//ACCTDATA DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.ACCTDATA.PS
//ACCTVSAM DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
//SYSIN    DD   *
   REPRO INFILE(ACCTDATA) OUTFILE(ACCTVSAM)
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:04 CDT
//*
