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
