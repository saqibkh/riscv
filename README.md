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


From writing to running

    $ riscv‐unknown‐elf‐gcc –S sum.c                 --> Compile
    $ riscv‐unknown‐elf‐gcc –c sum.s                 --> Assemble
    $ riscv‐unknown‐elf‐gcc –o sum sum.o             --> Link
    $ qemu‐riscv64 sum                               --> Load



Interactive Debug Mode
-------------------------------

To invoke interactive debug mode, launch spike with -d:

    $ spike -d pk hello

To see the contents of an integer register (0 is for core 0):

    : reg 0 a0

To see the contents of a floating point register:

    : fregs 0 ft0

or:

    : fregd 0 ft0

depending upon whether you wish to print the register as single- or double-precision.

To see the contents of a memory location (physical address in hex):

    : mem 2020

To see the contents of memory with a virtual address (0 for core 0):

    : mem 0 2020

You can advance by one instruction by pressing the enter key. You can also
execute until a desired equality is reached:

    : until pc 0 2020                   (stop when pc=2020)
    : until mem 2020 50a9907311096993   (stop when mem[2020]=50a9907311096993)

Alternatively, you can execute as long as an equality is true:

    : while mem 2020 50a9907311096993

You can continue execution indefinitely by:

    : r

At any point during execution (even without -d), you can enter the
interactive debug mode with `<control>-<c>`.

To end the simulation from the debug prompt, press `<control>-<c>` or:

    : q


------------------------------------------------------------------------------------

Python: /snap/bin/pycharm-community

