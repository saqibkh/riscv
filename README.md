# RISC-V
==============================================

RISC-V simulator can be downloaded from https://github.com/riscv/riscv-isa-sim.git

Build Steps
-------------------------------

We assume that the RISCV environment variable is set to the RISC-V tools
install path.

    $ apt-get install device-tree-compiler
    $ mkdir build
    $ cd build
    $ ../configure --prefix=$RISCV
    $ make
    $ [sudo] make install

Compiling and Running a Simple C Program
-------------------------------

Write a short C program and name it hello.c. Then, compile it into a RISC-V ELF binary named hello:

    $ riscv64-unknown-elf-gcc -o hello hello.c

Now you can simulate the program using:

    $ spike $(which pk) hello
    
Create an assembly program:

    $ riscv64-unknown-elf-gcc -O2 -S hello.c
    The "-O2" option is the code minimization/optimization technique

Assemble and link with gcc/binutils:

    $ riscv64-unknown-elf-gcc –o hello hello.S
    
Inspect the output binary:

    $ riscv64-unknown-elf-readelf -a hello | less
    $ riscv64-unknown-elf-objdump -d hello | less

Compile a test program using dynamically linked libraries

    $ riscv64-unknown-linux-gnu-gcc -O2 -o hello hello.c

    

