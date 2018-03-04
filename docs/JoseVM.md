# JoséVM (JVM)

JoséVM is a try to implement a Virtual Machine, which runs José Byte Code (JBC), similar to the Java Virtual Machine (which runs Java Byte Code). It is currently heavy work in progress and does not have a compiler.

### Formatting of an instruction
An Instruction is always 1 byte long, which is interpreted as an unsigned byte (number). This number is comparable to an OP code, as different actions are taken depending on this number. Both instructions and data are in Little Endian encoding.

## Currently implemented Instructions
|Code|Name|Actions taken|Caveats|
|---|---|---|---|
|1|PUSH_INT|Pushes an Integer into the stack|Integer is a signed, 4 Bit Integer (Little Endian Encoding)|
|2|VIEW|Prints the current contents of the stack.|This prints the whole stack and not just the most recently pushed item.|