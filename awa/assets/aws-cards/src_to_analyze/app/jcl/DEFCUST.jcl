//DEFCUST JOB 'Define Customer Data File',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID

//* *******************************************************************
//* DELETE CUSTOMER VSAM FILE IF ONE ALREADY EXISTS
//* *******************************************************************
//STEP05 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DELETE AWS.CCDA.CUSTDATA.CLUSTER -
          CLUSTER
/*
//*
//* *******************************************************************
//* DELETE CUSTOMER VSAM FILE IF ONE ALREADY EXISTS
//* *******************************************************************
//STEP05 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DEFINE CLUSTER (NAME(AWS.CUSTDATA.CLUSTER) -
          CYLINDERS(1 5) -
          KEYS(10 0) -
          RECORDSIZE(500 500) -
          SHAREOPTIONS(1 4) -
          ERASE -
          INDEXED -
          ) -
          DATA (NAME(AWS.CUSTDATA.CLUSTER.DATA) -
          ) -
          INDEX (NAME(AWS.CUSTDATA.CLUSTER.INDEX) -
          )
/*
