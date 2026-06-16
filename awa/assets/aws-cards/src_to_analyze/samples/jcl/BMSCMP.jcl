//CBLDBMS  JOB 'Compile BMS Map',CLASS=A,MSGCLASS=H,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID,TIME=1440
//*********************************************************************
//*  Change CICSMAP to your map name everywhere
//*----->   C CICSMAP xyz all <--------
//*  set    HLQ      to your high level qualifier
//*********************************************************************
//****  Sample Assembler BMS Compile JCL                         ******
//****  Check with your Administrator for                        ******
//****  JCL suitable to your environment                         ******
//*********************************************************************
//****  Compile CICS BMS to generate Copybook                    ******
//*********************************************************************
//*  ---------------------------
//*  Set Parms for this compile:
//*  ---------------------------
//   SET HLQ=AWS.M2
//*
//*********************************************************************
//*  Add Proclib Reference
//*********************************************************************
//CCLIBS  JCLLIB ORDER=&HLQ..CARDDEMO.PRC.UTIL
//STEP1 EXEC BUILDBMS,MAPNAME=CICSMAP,HLQ=&HLQ
//*********************************************************************
//****  CICS commands in batch to Execute NEWCOPY                ******
//*********************************************************************
//SDSF1 EXEC PGM=SDSF
//ISFOUT DD SYSOUT=*
//CMDOUT DD SYSOUT=*
//ISFIN  DD *
 /MODIFY CICSAWSA,'CEMT SET PROG(CICSMAP) NEWCOPY'
/*
