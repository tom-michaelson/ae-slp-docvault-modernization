000700*****************************************************************
000800* CABENDD.CPY                                                   *
000900*---------------------------------------------------------------*
001000* Work areas for abend routine                                  *

001200 01  ABEND-DATA.
001300   05  ABEND-CODE                            PIC X(4)
001400       VALUE SPACES.
001500   05  ABEND-CULPRIT                         PIC X(8)
001600       VALUE SPACES.
001700   05  ABEND-REASON                          PIC X(50)
001800       VALUE SPACES.
001900   05  ABEND-MSG                             PIC X(72)
002000       VALUE SPACES.



      *
      * Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:15:58 CDT
      *
