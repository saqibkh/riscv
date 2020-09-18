##############################################################################
#
# This file will be used to auto-generate the modified assembly files
# for Control Flow Error Detection techniques, which includes
# 1) Control Flow Checking by Software Signature (CFCSS)
#
##############################################################################

# !/usr/bin/python

import sys
import logging
import time
import string
import datetime
import random
import subprocess

import compileUtil
import utils
import cfcss
import os

from os import path


def usage():
    print("Usage: Please provide a C program that matches <file>.c")
    print("Example ./CFE_Main.py src/dir/test/bit_count.c    (Must have the entire path to the source file")


def main(argv):
    if len(sys.argv) == 1:
        usage()
        sys.exit()

    file_c = argv[0]
    ''' Create an assembly file and an objdump file from the C program file provided to us '''
    compileUtil.compile_c(file_c)

    # Check if all the assembly and objdump files exist
    file = argv[0].rsplit('.')[0] + ".s"
    if not utils.checkFileExists(file):
        print("file: " + file + " doesn't exist.")
        return 1
    f_asm = utils.readfile(file)
    file = argv[0].rsplit('.')[0] + ".objdump"
    if not utils.checkFileExists(file):
        print("file: " + file + " doesn't exist.")
        return 1
    f_obj = utils.readfile(file)
    del file

    # Create a Control Flow Graph
    map = utils.ControlFlowMapRevised(f_asm, f_obj)

    # Generate CFCSS (Control Flow Checking by Software Signature)
    i_cfcss = cfcss.CFCSS(map)

    cfcss_file = argv[0].rsplit('.')[0] + '_cfcss.s'
    with open(cfcss_file, 'w') as filehandle:
        for listitem in i_cfcss.new_asm_file:
            filehandle.write('%s\n' % listitem)

    ''' Compile the newly created assembly file to generate a static binary '''
    compileUtil.compile_s(cfcss_file)

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
