      ******************************************************************
      * CardDemo - Admin Menu Options
      ******************************************************************
       01 CARDDEMO-ADMIN-MENU-OPTIONS.
         05 CDEMO-ADMIN-OPT-COUNT           PIC 9(02) VALUE 4.

         05 CDEMO-ADMIN-OPTIONS-DATA.

           10 FILLER                        PIC 9(02) VALUE 1.
           10 FILLER                        PIC X(35) VALUE
               'User List (Security)               '.
           10 FILLER                        PIC X(08) VALUE 'COUSR00C'.

           10 FILLER                        PIC 9(02) VALUE 2.
           10 FILLER                        PIC X(35) VALUE
               'User Add (Security)                '.
           10 FILLER                        PIC X(08) VALUE 'COUSR01C'.

           10 FILLER                        PIC 9(02) VALUE 3.
           10 FILLER                        PIC X(35) VALUE
               'User Update (Security)             '.
           10 FILLER                        PIC X(08) VALUE 'COUSR02C'.

           10 FILLER                        PIC 9(02) VALUE 4.
           10 FILLER                        PIC X(35) VALUE
               'User Delete (Security)             '.
           10 FILLER                        PIC X(08) VALUE 'COUSR03C'.

         05 CDEMO-ADMIN-OPTIONS REDEFINES CDEMO-ADMIN-OPTIONS-DATA.
           10 CDEMO-ADMIN-OPT OCCURS 9 TIMES.
             15 CDEMO-ADMIN-OPT-NUM           PIC 9(02).
             15 CDEMO-ADMIN-OPT-NAME          PIC X(35).
             15 CDEMO-ADMIN-OPT-PGMNAME       PIC X(08).
      *
      * Ver: CardDemo_v1.0-26-g42273c1-79 Date: 2022-07-20 16:59:12 CDT
      *
