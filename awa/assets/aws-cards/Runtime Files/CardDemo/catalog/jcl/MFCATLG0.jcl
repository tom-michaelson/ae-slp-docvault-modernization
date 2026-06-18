//MFCATLG1 JOB 'MFCATLG1',CLASS=A,MSGCLASS=X,TIME=1440,
//        COND=(8,LT),NOTIFY=MYUSERID,RESTART=*,LINES=(500,CANCEL)
//*
//*-------------------------------------------------------------------*
//*   CATALOG PDS  ==> MICRO FOCUS ONLY <==
//*-------------------------------------------------------------------*
//*
//STEP02  EXEC PGM=IEFBR14
//*
//SYSOUT   DD  SYSOUT=*
//*
//PDS001   DD  DSN=AWS.M2.CARDDEMO.JCL,
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=80,DSORG=PO)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\*.JCL'
//*
//PDS002   DD  DSN=AWS.M2.CARDDEMO.PROC,
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=80,DSORG=PO)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\*.PRC'
//*
//PDS003   DD  DSN=AWS.M2.CARDDEMO.CNTL,
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=80,DSORG=PO)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\*.CTL'
//*
//*
//*-------------------------------------------------------------------*
//*   CATALOG PDS MEMBERS  ==> MICRO FOCUS ONLY <==
//*-------------------------------------------------------------------*
//*
//STEP03  EXEC PGM=IEFBR14
//*
//SYSOUT   DD  SYSOUT=*
//*
//PS0001   DD  DSN=AWS.M2.CARDDEMO.PROC(REPROC),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\REPROC.PRC'
//*
//PS0002   DD  DSN=AWS.M2.CARDDEMO.PROC(TRANREPT),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANREPT.PRC'
//*
//PS0003   DD  DSN=AWS.M2.CARDDEMO.CNTL(REPROCT),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\REPROCT.CTL'
//*
//PS0005   DD  DSN=AWS.M2.CARDDEMO.JCL(ACCTFILE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\ACCTFILE.JCL'
//*
//PS0006   DD  DSN=AWS.M2.CARDDEMO.JCL(CARDFILE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\CARDFILE.JCL'
//*
//PS0007   DD  DSN=AWS.M2.CARDDEMO.JCL(CBADMCDJ),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\CBADMCDJ.JCL'
//*
//PS0008   DD  DSN=AWS.M2.CARDDEMO.JCL(CLOSEFIL),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\CLOSEFIL.JCL'
//*
//PS0009   DD  DSN=AWS.M2.CARDDEMO.JCL(COMBTRAN),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\COMBTRAN.JCL'
//*
//PS0010   DD  DSN=AWS.M2.CARDDEMO.JCL(CUSTFILE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\CUSTFILE.JCL'
//*
//PS0011   DD  DSN=AWS.M2.CARDDEMO.JCL(DALYREJS),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\DALYREJS.JCL'
//*
//PS0012   DD  DSN=AWS.M2.CARDDEMO.JCL(DEFCUST),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\DEFCUST.JCL'
//*
//PS0013   DD  DSN=AWS.M2.CARDDEMO.JCL(DEFGDGB),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\DEFGDGB.JCL'
//*
//PS0014   DD  DSN=AWS.M2.CARDDEMO.JCL(DISCGRP),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\DISCGRP.JCL'
//*
//PS0015   DD  DSN=AWS.M2.CARDDEMO.JCL(DUSRSECJ),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\DUSRSECJ.JCL'
//*
//PS0016   DD  DSN=AWS.M2.CARDDEMO.JCL(INTCALC),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\INTCALC.JCL'
//*
//PS0017   DD  DSN=AWS.M2.CARDDEMO.JCL(MFCATLG2),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\MFCATLG2.JCL'
//*
//PS0018   DD  DSN=AWS.M2.CARDDEMO.JCL(OPENFIL),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\OPENFIL.JCL'
//*
//PS0019   DD  DSN=AWS.M2.CARDDEMO.JCL(POSTTRAN),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\POSTTRAN.JCL'
//*
//PS0020   DD  DSN=AWS.M2.CARDDEMO.JCL(PRTCATBL),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\PRTCATBL.JCL'
//*
//PS0021   DD  DSN=AWS.M2.CARDDEMO.JCL(READACCT),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\READACCT.JCL'
//*
//PS0022   DD  DSN=AWS.M2.CARDDEMO.JCL(READCARD),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\READCARD.JCL'
//*
//PS0023   DD  DSN=AWS.M2.CARDDEMO.JCL(READCUST),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\READCUST.JCL'
//*
//PS0024   DD  DSN=AWS.M2.CARDDEMO.JCL(READXREF),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\READXREF.JCL'
//*
//PS0025   DD  DSN=AWS.M2.CARDDEMO.JCL(REPTFILE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\REPTFILE.JCL'
//*
//PS0026   DD  DSN=AWS.M2.CARDDEMO.JCL(TCATBALF),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TCATBALF.JCL'
//*
//PS0027   DD  DSN=AWS.M2.CARDDEMO.JCL(TRANBKP),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANBKP.JCL'
//*
//PS0028   DD  DSN=AWS.M2.CARDDEMO.JCL(TRANCATG),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANCATG.JCL'
//*
//PS0029   DD  DSN=AWS.M2.CARDDEMO.JCL(TRANFILE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANFILE.JCL'
//*
//PS0030   DD  DSN=AWS.M2.CARDDEMO.JCL(TRANIDX),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANIDX.JCL'
//*
//PS0031   DD  DSN=AWS.M2.CARDDEMO.JCL(TRANREPT),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANREPT.JCL'
//*
//PS0032   DD  DSN=AWS.M2.CARDDEMO.JCL(TRANTYPE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\TRANTYPE.JCL'
//*
//PS0033   DD  DSN=AWS.M2.CARDDEMO.JCL(XREFFILE),
//             DISP=(MOD,CATLG,DELETE),
//             DCB=(RECFM=LSEQ,LRECL=0,DSORG=PS)
//*MFE: %PCDSN='<CATALOGFOLDER>\jcl-job\XREFFILE.JCL'
//*
//*-------------------------------------------------------------------*
//* DEFINE VSAM CLUSTER
//*-------------------------------------------------------------------*
//*
//STEP04  EXEC PGM=IDCAMS
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  *
 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS)           -
                    KEYS(8,0)                                     -
                    RECORDSIZE(80,80)                             -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS.DATA))     -
        INDEX   (NAME(AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS)         -
                    KEYS(11,0)                                    -
                    RECORDSIZE(300,300)                           -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS)         -
                    KEYS(16,0)                                    -
                    RECORDSIZE(150,150)                           -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS)         -
                    KEYS(9,0)                                     -
                    RECORDSIZE(500,500)                           -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS)         -
                    KEYS(16,0)                                    -
                    RECORDSIZE(50,50)                             -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS)         -
                    KEYS(16,0)                                    -
                    RECORDSIZE(350,350)                           -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS)          -
                    KEYS(16,0)                                    -
                    RECORDSIZE(50,50)                             -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS.DATA))    -
        INDEX   (NAME(AWS.M2.CARDDEMO.DISCGRP.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS)         -
                    KEYS(17,0)                                    -
                    RECORDSIZE(50,50)                             -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.TCATBALF.VSAM.KSDS.INDEX))


 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.TRANCATG.VSAM.KSDS)         -
                    KEYS(6,0)                                     -
                    RECORDSIZE(60,60)                             -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.TRANCATG.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.TRANCATG.VSAM.KSDS.INDEX))

 DEFINE CLUSTER (NAME(AWS.M2.CARDDEMO.TRANTYPE.VSAM.KSDS)         -
                    KEYS(2,0)                                     -
                    RECORDSIZE(60,60)                             -
                    ERASE                                         -
                    INDEXED                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.TRANTYPE.VSAM.KSDS.DATA))   -
        INDEX   (NAME(AWS.M2.CARDDEMO.TRANTYPE.VSAM.KSDS.INDEX))
/*
//*
//*-------------------------------------------------------------------*
//* DEFINE VSAM ALTERNATEINDEX
//*-------------------------------------------------------------------*
//*
//STEP05  EXEC PGM=IDCAMS
//*
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  *

 DEFINE ALTERNATEINDEX (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX)   -
        RELATE(AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS)                -
                    KEYS(11,16)                                   -
                    NONUNIQUEKEY                                  -
                    RECORDSIZE(150,150)                           -
                    UPGRADE                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.DATA))    -
        INDEX   (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.INDEX))

 DEFINE PATH   (NAME(AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH)      -
      PATHENTRY(AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX))

 DEFINE ALTERNATEINDEX (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX)   -
        RELATE(AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS)                -
                    KEYS(11,25)                                   -
                    NONUNIQUEKEY                                  -
                    RECORDSIZE(50,50)                             -
                    UPGRADE                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.DATA))    -
        INDEX   (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.INDEX))

 DEFINE PATH   (NAME(AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH)      -
      PATHENTRY(AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX))

 DEFINE ALTERNATEINDEX (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX)   -
        RELATE(AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS)                -
                    KEYS(26,304)                                  -
                    NONUNIQUEKEY                                  -
                    RECORDSIZE(350,350)                           -
                    UPGRADE                                       -
                    CYLINDERS(1,5))                               -
        DATA    (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX.DATA))    -
        INDEX   (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX.INDEX))

 DEFINE PATH   (NAME(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX.PATH)      -
      PATHENTRY(AWS.M2.CARDDEMO.TRANSACT.VSAM.AIX))

/*
//*
//* *******************************************************************
//*  DEFINE GDG BASES NEEDED BY CARDDEMO PROJECT
//* *******************************************************************
//STEP06 EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.TRANSACT.BKUP) -
    LIMIT(5) -
    SCRATCH -
   )
   IF LASTCC LE 12 THEN SET MAXCC=0
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.TRANSACT.DALY) -
    LIMIT(5) -
    SCRATCH -
   )
   IF LASTCC LE 12 THEN SET MAXCC=0
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.TRANREPT) -
    LIMIT(5) -
    SCRATCH -
   )
   IF LASTCC LE 12 THEN SET MAXCC=0
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.TCATBALF.BKUP) -
    LIMIT(5) -
    SCRATCH -
   )
   IF LASTCC LE 12 THEN SET MAXCC=0
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.SYSTRAN) -
    LIMIT(5) -
    SCRATCH -
   )
   IF LASTCC LE 12 THEN SET MAXCC=0
   DEFINE GENERATIONDATAGROUP -
   (NAME(AWS.M2.CARDDEMO.TRANSACT.COMBINED) -
    LIMIT(5) -
    SCRATCH -
   )
   IF LASTCC LE 12 THEN SET MAXCC=0
/*
//*
//
