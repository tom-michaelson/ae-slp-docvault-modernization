//DISCGRP JOB 'DEFINE DISCLOSURE GROUP FILE',CLASS=A,MSGCLASS=0,
//  NOTIFY=&SYSUID

//* *******************************************************************
//* DELETE DISCLOSURE GROUP VSAM FILE IF ONE ALREADY EXISTS
//* *******************************************************************
//STEP05 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DELETE AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS -
          CLUSTER
   SET    MAXCC = 0
/*
//*
//* *******************************************************************
//* DEFINE DISCLOSURE GROUP VSAM FILE
//* *******************************************************************
//STEP10 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS) -
          CYLINDERS(1 5) -
          VOLUMES(AWSHJ1 -
          ) -
          KEYS(16 0) -
          RECORDSIZE(50 50) -
          SHAREOPTIONS(2 3) -
          ERASE -
          INDEXED -
          ) -
          DATA (NAME(AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS.DATA) -
          ) -
          INDEX (NAME(AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS.INDEX) -
          )
/*
//* *******************************************************************
//* COPY DATA FROM FLAT FILE TO VSAM FILE
//* *******************************************************************
//STEP15 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//DISCGRP DD DISP=SHR,
//         DSN=AWS.M2.CARDDEMO.DISCGRP.PS
//DISCVSAM DD DISP=OLD,
//         DSN=AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS
//SYSIN    DD   *
   REPRO INFILE(DISCGRP) OUTFILE(DISCVSAM)
/*
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:23:06 CDT
//*
