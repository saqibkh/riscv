#!/usr/bin/env python

##############################################################################
#
#  This file will be used to process the logs that were generated.
#  We could input either the <file>_extended.log or <file>_extended_debug.log
#
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
import csv

from os import path

#---------Set sys.path for CFE_MAIN execution---------------------------------------
full_path = os.path.abspath(os.path.dirname(sys.argv[0])).split('riscv')[0]
sys.path.append(full_path)
# Walk path and append to sys.path
for root, dirs, files in os.walk(full_path):
    for dir in dirs:
        sys.path.append(os.path.join(root, dir))

import instructions
import log_utils
import ML1

def usage():
    print("Usage: Please provide a log file <file>_extended.log or <file>_extended_debug.log")
    print("Example ./Process_Logs.py -F <file>.log")
    print(" -F | --file         file_name ")


def main(argv):
    l_file = None

    if len(sys.argv) == 1:
        usage()
        sys.exit()

    try:
        opts, args = getopt.getopt(
            argv, "hF:", ["help", "file="])
    except getopt.GetoptError:
        usage()
        sys.exit()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-F", "--file"):
            l_file = arg

    # Delete variables that are no longer necessary
    del arg, args, argv, opt, opts

    # Check if the file provided is accessible or not
    if not path.exists(l_file):
        print("The log file %s doesn't exist" % l_file)
        sys.exit()

    # Check if the file provided is a valid log file
    l_file_name = l_file.rsplit('/', 1)[-1]
    if ("_extended.log" not in l_file_name) and ("_extended_debug.log" not in l_file_name):
        print("Please provide a <file>_extended.log or <file>_extended_debug.log")
        sys.exit()

    # Check if the instructions within the log file are accounted for in the instruction.py file.
    # Otherwise update the instruction.py file
    i_instruction_map = log_utils.Instruction_Map(l_file)

    i_ML1 = ML1.ML1(i_instruction_map)
    print("Finished processing logs")



if __name__ == "__main__":
    main(sys.argv[1:])