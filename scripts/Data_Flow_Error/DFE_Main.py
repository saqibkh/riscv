#!/usr/bin/python


##############################################################################
#
# This file will be used to auto-generate the modified assembly files
# for Data Flow Error Detection techniques, which includes
# 1) EDDDI
# 2) EDDI
# 3) SA
# 4) SWIFT
# 5) VAR3+
# 6) CBD
# 7) SEDSR
##############################################################################



import sys
import logging
import time
import string
import datetime
import getopt
import random
import subprocess
import os
from os import path

# ---------Set sys.path for CFE_MAIN execution---------------------------------------
full_path = os.path.abspath(os.path.dirname(sys.argv[0])).split('riscv')[0]
sys.path.append(full_path)
# Walk path and append to sys.path
for root, dirs, files in os.walk(full_path):
    for dir in dirs:
        sys.path.append(os.path.join(root, dir))

import compileUtil
import utils
import instructions
import sim_logging


def usage():
    print("Usage: Please provide the absolute path for a C program that matches <file>.c")
    print(
        "Example ./DFE_Main.py src/dir/test/bit_count.c --enable-extras (Must have the entire path to the source file")


def checkFileExists(i_filename):
    if not utils.checkFileExists(i_filename):
        print("file: " + i_filename + " doesn't exist.")
        raise Exception

def main(argv):
    l_test = "ALL"
    l_enable_extras = False
    simlog = sim_logging.SIMLOG()

    if len(sys.argv) == 1:
        usage()
        sys.exit()

    if len(sys.argv) > 2:
        "Check for any more parameters"
        for i in range(len(argv) - 1):
            if argv[i + 1] == '--enable-extras':
                l_enable_extras = True
            elif '--test_' in argv[i + 1]:
                l_test = argv[i + 1].split("--test_")[-1]

    simlog.info("Processing file: " + argv[0])

    file_c = argv[0]
    ''' Create an assembly file and an objdump file from the C program file provided to us '''
    compileUtil.compile_c(file_c)
    file_c_executable = file_c.split(".c")[0]

    l_file_dir = file_c.rsplit('/', 1)[0]
    l_test_name = (file_c.rsplit('/', 1)[1]).rsplit('.c')[0]

    # Check if all the assembly and objdump files exist
    file_s = argv[0].rsplit('.')[0] + ".s"
    checkFileExists(file_s)
    file_objdump = argv[0].rsplit('.')[0] + ".objdump"
    checkFileExists(file_objdump)

    #################################################################
    ######                                                     ######
    ######   Start generating the Data Flow Error Detection    ######
    ######                                                     ######
    #################################################################

#####################################################################################################################


#####################################################################################################################


#####################################################################################################################


#####################################################################################################################


#####################################################################################################################


#####################################################################################################################


#####################################################################################################################


#####################################################################################################################

    # Delete the unnecessary .o .objdump .readelf file
    if not l_enable_extras:
        compileUtil.delete_all_useless_files(l_file_dir, l_test_name)

if __name__ == "__main__":
    main(sys.argv[1:])