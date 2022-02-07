#!/usr/bin/env python

##############################################################################
# This file will be used to auto-generate the instruction trace logs
# using the assembly files provided.
# It will create a log file that will include all SPRs and GPRs before
# and after instruction execution.
##############################################################################


import os
import testlib
import unittest
import tempfile
import time
import sys
import getopt
import pathlib


from os import path

# ---------Set sys.path for CFE_MAIN execution---------------------------------------
full_path = os.path.abspath(os.path.dirname(sys.argv[0])).split('riscv')[0]
sys.path.append(full_path)
# Walk path and append to sys.path
for root, dirs, files in os.walk(full_path):
    for dir in dirs:
        sys.path.append(os.path.join(root, dir))

import utils


def usage():
    print("Usage: Please provide a assembly file or an executable file")
    print("Example ./Main.py -F bit_count.S -O <output_directory>")
    print(" -F | --file         file_name ")
    print(" -O | --output_dir   output_directory ")


def main(argv):
    l_file = None
    l_outout_dir = None

    if len(sys.argv) == 1:
        usage()
        sys.exit()

    try:
        opts, args = getopt.getopt(
            argv, "hF:O:", ["help", "file=", "output_dir="])
    except getopt.GetoptError:
        usage()
        sys.exit()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-F", "--file"):
            l_file = arg
        elif opt in ("-O", "--output_dir"):
            l_outout_dir = arg

    # Check if the file provided is accessible or not
    if not checkFileExists(l_file):
        print("The assembly file %s doesn't exist" % l_file)
        sys.exit()

    # Check whether the output directory where the logs will be stored is present
    # and is accessible
    checkPathExists(l_outout_dir)

    # Check if it is an executable file or an assembly file that needs to be compiled first
    if l_file.endswith(".s") or l_file.endswith(".c"):
        print("Input file is either an assembly file or a c file that needs to be compiled first")
        l_file = testlib.compile(l_file)
    else:
        print("Input file is an executable and don't need compilation")

    # Check if the objdump file exists. If it does, then get the starting
    # address of the main subroutine, so that we can skip initial instructions
    l_file_objdump = l_file + ".objdump"
    checkFileExists(l_file_objdump)
    l_starting_address = get_main_starting_address(l_file_objdump)

    # Generate logs
    spike = testlib.Spike(l_file, l_outout_dir, l_starting_address)

    print("\nGenerating log file.")
    sys.stdout.flush()
    spike.generate_logs()
    print("Log file generated!\n")

    print("\nGenerating Extending log file. Please wait!");
    sys.stdout.flush()
    spike.generate_extended_logs()
    print("Extended log file generated!\n")

    print("\nGenerating Extending Debug log file. Please wait longer!")
    sys.stdout.flush()
    spike.generate_extended_debug_logs()
    print("Extended debug log file generated!\n")


##
# Description: Get the starting address of the main function
#
# Input: filename (String)
# Output: address (String)
def get_main_starting_address(l_file_objdump):
    l_file_objdump = utils.readfile(l_file_objdump)
    for i in range(len(l_file_objdump)):
        if "<main>:" in l_file_objdump[i]:
            l_starting_address = l_file_objdump[i].split(' ')[0]
            while l_starting_address[0] == '0':
                l_starting_address = l_starting_address[1:]
            return l_starting_address


##
# Description: Check if the given file exists in the directory
#
# Input: filename (String)
# Output: boolean
def checkFileExists(filename):
    return path.exists(filename)


##
# Description: Check if the given path exists, if not then try to mkdir
#
# Input: filename (String)
# Output: boolean
def checkPathExists(i_path):
    try:
        pathlib.Path(i_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return


if __name__ == "__main__":
    main(sys.argv[1:])
