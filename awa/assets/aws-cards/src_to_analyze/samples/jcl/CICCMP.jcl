//CICCMP  JOB 'Compile CICS Program',CLASS=A,MSGCLASS=H,
//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID,TIME=1440
//*********************************************************************
//*  change CICSPGMN to your program name everywhere
//*----->   C CICSPGMN xyz all <--------
//*  set    HLQ      to your high level qualifier
//*********************************************************************
//****  Sample CICS COBOL Compile JCL                            ******
//****  Check with your Administrator for                        ******
//****  JCL suitable to your environment                         ******
//*********************************************************************
//****  Compile CICS COBOL program                               ******
//****  After compiling the related maps                         ******
//*********************************************************************
//*  Set Parms for this compile:
//*********************************************************************
//   SET HLQ=AWS.M2
//   SET MEMNAME=CICSPGMN
//*********************************************************************
//*  Add proclib reference
//*********************************************************************
//CCLIBS  JCLLIB ORDER=&HLQ..CARDDEMO.PRC.UTIL
//*********************************************************************
//*  compile the COBOL code:
//*********************************************************************
//CICSCMP      EXEC BUILDONL,MEM=&MEMNAME,HLQ=&HLQ
//*********************************************************************
//****  CICS commands in batch to perform NEWCOPY                ******
//*********************************************************************
//NEWCOPY EXEC PGM=SDSF,COND=(4,LT)
//ISFOUT DD SYSOUT=*
//CMDOUT DD SYSOUT=*
//ISFIN  DD *
 /MODIFY CICSAWSA,'CEMT SET PROG(CICSPGMN) NEWCOPY'
/*
