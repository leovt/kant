10 DIM I AS INTEGER
20 DIM NAME AS STRING
30 INPUT "WHATS YOUR NAME? "; NAME
40 INPUT "WHATS YOUR AGE? "; I
50 LET I = I - 1
60 IF I = 0 THEN GOTO 90
70 PRINT "HELLO, " ; NAME ; I
80 GOTO 50
90 LET NAME = NAME + "E"
95 LET I = I = 1
96 PRINT "SHOULD BE ZERO: "; I
97 LET I = NAME = "NAME"
98 PRINT I; NAME
99 PRINT "" = ""
100 END
