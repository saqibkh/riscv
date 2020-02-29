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
    $spike $(which pk) hello
