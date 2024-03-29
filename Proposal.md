# Things we could do as part of PhD.

============================================================

1) Implement various Control Flow Error (CFE) and Data Flow Error (DFE) detection techniques, 
   and look for ways to improve on those in terms of performance (Code Size / Execution Time)
   and in terms of the type of defects being caught by detection techniques
   (May need to classify all types of defects).
   
2) Measure the effect of adding a co-processor to detect CFEs and DFEs instead of modifying the
   compiled code. This would increase performance overhead of a processor/embedded system
   (Area, Power, Timing Delay) and weigh its pros and cons.
   How much performance degradation takes place by verifying 1,2,4,8,16 bytes (Partial verification)
   
3) Investigate how machine learning can assist in predicting results of an instruction.
   (Perhaps there is a pattern)
   For example multiplication with an even number will always result in an even number etc. 
