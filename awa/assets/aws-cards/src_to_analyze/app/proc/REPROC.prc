//REPROC PROC

//* *******************************************************************
//* REPRO UTILITY TO LOAD OR UNLOAD VSAM FILE
//* *******************************************************************
//PRC001 EXEC PGM=IDCAMS
//SYSPRINT DD SYSOUT=*
//FILEIN  DD DISP=SHR,
//        DSN=NULLFILE
//FILEOUT DD DISP=SHR,
//        DSN=NULLFILE
//SYSIN   DD DISP=SHR,
//        DSN=&CNTLLIB(REPROCT)
// PEND
//*
//* Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:27:38 CDT
//*
