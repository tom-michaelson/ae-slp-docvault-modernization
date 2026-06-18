
      *    Set (TESTVAR1) to red if in error and * if blankACSHLIM
           IF (FLG-(TESTVAR1)-NOT-OK
           OR  FLG-(TESTVAR1)-BLANK)
           AND CDEMO-PGM-REENTER
               MOVE DFHRED             TO
                    (SCRNVAR2)C OF (MAPNAME3)O
               IF  FLG-(TESTVAR1)-BLANK
                   MOVE '*'            TO
                    (SCRNVAR2)O OF (MAPNAME3)O
               END-IF
           END-IF
      *
      * Ver: CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:15:58 CDT
      *
