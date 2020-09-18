#!/usr/bin/python


import logging
import os
import time
import string
import datetime
import random
import subprocess
import re
from os import path


def compile_c(file):
    """Compile a single .c file into a binary.
    Also generate the assembly (.s) file and an objdump file (.objdump)"""
    source_dir = file.rsplit('/', 1)[0] + '/'
    c_file = file.rsplit('/', 1)[1]
    e_file = os.path.splitext(c_file)[0]  # Executable file
    o_file = e_file + '.o'
    s_file = e_file + '.s'
    readelf_file = e_file + '.readelf'
    objdump_file = e_file + '.objdump'

    # Clear any old files to prevent overwrite
    delete_file_if_exists(source_dir + e_file)
    delete_file_if_exists(source_dir + o_file)
    delete_file_if_exists(source_dir + s_file)
    delete_file_if_exists(source_dir + readelf_file)
    delete_file_if_exists(source_dir + objdump_file)

    # Get the assembly file first
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-gcc', "-S", source_dir + c_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd
    # Move the .s file to the source_directory
    os.replace(s_file, source_dir + s_file)

    # Get the obj file
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-gcc', "-c", source_dir + s_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd
    # Move the .o file to the source_directory
    os.replace(o_file, source_dir + o_file)

    # Link the obj file to create an executable
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-gcc', "-o", source_dir + e_file, source_dir + o_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd

    # Generate the readelf file
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-readelf', "-a", source_dir + e_file, '>', source_dir + readelf_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd

    # Generate the objdump file
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-objdump', "-d", source_dir + e_file, '>', source_dir + objdump_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd


def compile_s(file):
    """Compile a assembly file (.s) into an executable file"""
    source_dir = file.rsplit('/', 1)[0] + '/'
    s_file = file.rsplit('/', 1)[1]
    e_file = os.path.splitext(s_file)[0]  # Executable file
    o_file = e_file + '.o'
    readelf_file = e_file + '.readelf'
    objdump_file = e_file + '.objdump'

    # Clear any old files to prevent overwrite
    delete_file_if_exists(source_dir + e_file)
    delete_file_if_exists(source_dir + o_file)
    delete_file_if_exists(source_dir + readelf_file)
    delete_file_if_exists(source_dir + objdump_file)

    # Get the obj file
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-gcc', "-c", source_dir + s_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd
    # Move the .o file to the source_directory
    os.replace(o_file, source_dir + o_file)

    # Link the obj file to create an executable
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-gcc', "-o", source_dir + e_file, source_dir + o_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd

    # Generate the readelf file
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-readelf', "-a", source_dir + e_file, '>', source_dir + readelf_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd

    # Generate the objdump file
    cmd = ['/opt/riscv64/bin/riscv64-unknown-elf-objdump', "-d", source_dir + e_file, '>', source_dir + objdump_file]
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd


''' The following functions will serve as the helper functions for the above mentioned
    functions, and shouldn't be called upon externally'''


def find_file(path):
    for directory in (os.getcwd(), os.path.dirname()):
        fullpath = os.path.join(directory, path)
        if os.path.exists(fullpath):
            return fullpath
    return None


def delete_file_if_exists(i_file):
    if os.path.exists(i_file):
        os.remove(i_file)
