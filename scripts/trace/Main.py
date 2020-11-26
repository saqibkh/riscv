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
    if l_file.endswith(".s") or file.endswith(".c"):
        print("Input file is either an assembly file or a c file that needs to be compiled first")
        l_file = testlib.compile(l_file)
    else:
        print("Input file is an executable and don't need compilation")

    # Generate logs
    spike = testlib.Spike(l_file, l_outout_dir)

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
    except Error as e:
        print("Error with the given path")
        return 1



if __name__ == "__main__":
    main(sys.argv[1:])
