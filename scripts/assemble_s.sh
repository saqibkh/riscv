#!/bin/bash
#
# This script will be used to assemble and link a .S file
# It will provide the an object file and an executable file
# Input: s file


# Take in one input and verify that it is a s file
S_file=${1?Error: no s file provided}
if [[ "$S_file" == *".s" ]]; then
    echo "S file to compile = $S_file."
else
    echo "The input file provided $S_file is not a s file"
    exit 1
fi

E_file=${S_file::-2}
O_file="${E_file}.o"

# Create an obj file (*.o)
echo "riscv64-unknown-elf-gcc -c $S_file"
riscv64-unknown-elf-gcc -c $S_file
# Link the obj file to create an executable
echo "riscv64-unknown-elf-gcc -o $E_file $O_file"
riscv64-unknown-elf-gcc -o $E_file $O_file
