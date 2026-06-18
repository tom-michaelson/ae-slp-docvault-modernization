//CNJBATMP JOB 'Compile Batch COBOL Program',CLASS=A,MSGCLASS=H,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID,TIME=1440
//*********************************************************************
//*  change BATCHPGM to your program name everywhere
//*----->   C BATCHPGM xyz all <--------
//*********************************************************************
//****  Sample Batch COBOL Compile JCL                           ******
//****  Check with your Administrator for                        ******
//****  JCL suitable to your environment                         ******
//*********************************************************************
//*  change BATCHPGM to your program name everywhere
//*----->   C BATCHPGM xyz all <--------
//*********************************************************************
//****  COMPILE BATCH COBOL PROGRAM                              ******
//*********************************************************************
//*  Set Parms for this compile:
//*********************************************************************
//   SET MEMNAME=BATCHPGM
//   SET HLQ=AWS.M2
//*********************************************************************
//*  Add proclib reference
//*********************************************************************
//CCLIBS  JCLLIB ORDER=&HLQ..CARDDEMO.PRC.UTIL
//*********************************************************************
//*  compile the COBOL code:
//*********************************************************************
//BATCMP       EXEC BUILDBAT,MEM=&MEMNAME,HLQ=&HLQ
