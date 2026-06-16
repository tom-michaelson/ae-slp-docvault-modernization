//MFCATLG2 JOB 'MFCATLG2',CLASS=A,MSGCLASS=X,TIME=1440,
//        COND=(8,LT),NOTIFY=MYUSERID,RESTART=*,LINES=(500,CANCEL)
//*
//*-------------------------------------------------------------------*
//*   CATALOG VSAM AND LOAD  ==> MICRO FOCUS ONLY <==
//*-------------------------------------------------------------------*
//*
//STEP01  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(CLOSEFIL)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP02  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(ACCTFILE)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP03  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(CARDFILE)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP04  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(XREFFILE)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP05  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(CUSTFILE)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP06  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(TRANFILE)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP07  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(DISCGRP)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP08  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(TCATBALF)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP09  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(TRANCATG)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP10  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(TRANTYPE)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP11  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(DUSRSECJ)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP12  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(OPENFIL)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
//*-------------------------------------------------------------------*
//*
//STEP13  EXEC PGM=IEBGENER
//*
//SYSUT1   DD  DISP=SHR,DSN=AWS.M2.CARDDEMO.JCL(DEFGDGB)
//SYSUT2   DD  SYSOUT=(*,INTRDR)
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//*
