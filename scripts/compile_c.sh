#!/bin/bash
#
# This script will be used to compile, assemble and link a C program
# It will provide the assembly file, an object file and an executable file
# Input: c file


# Take in one input and verify that it is a c file
C_file=${1?Error: no c file provided}
if [[ "$C_file" == *".c" ]]; then
    echo "C file to compile = $C_file."
else
    echo "The input file provided $C_file is not a c file"
    exit 1
fi

E_file=${C_file::-2}
S_file="${E_file}.s"
O_file="${E_file}.o"
readelf_file="${E_file}.readelf"
objdump_file="${E_file}.objdump"

# Create an assembly file (.s)
echo "riscv64-unknown-elf-gcc -S $C_file"
riscv64-unknown-elf-gcc -S $C_file
# Create an obj file (*.o)
echo "riscv64-unknown-elf-gcc -c $S_file"
riscv64-unknown-elf-gcc -c $S_file
# Link the obj file to create an executable
echo "riscv64-unknown-elf-gcc -o $E_file $O_file"
riscv64-unknown-elf-gcc -o $E_file $O_file

echo "riscv64-unknown-elf-readelf -a ${E_file} > $readelf_file"
riscv64-unknown-elf-readelf -a ${E_file} > $readelf_file
echo "riscv64-unknown-elf-objdump -d ${E_file} > $objdump_file"
riscv64-unknown-elf-objdump -d ${E_file} > $objdump_file
