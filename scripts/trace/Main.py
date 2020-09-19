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
import pexpect

from os import path

def usage():
    print("Usage: Please provide a assembly file")
    print("Example ./Main.py bit_count.S")

def main(argv):

    if len(sys.argv) == 1:
        usage()
        sys.exit()

    # Check if the file exist
    file = argv[0]
    if(checkFileExists(file) == False):
        print("The assembly file %s doesn't exist" %file)
        return 1

    # Check if it is an executable file or an assembly file that needs to be compiled first
    if(file.endswith(".s")):
        print("Input file is an assembly file and needs to be compiled first")
        file = testlib.compile(file)
    else:
        print("Input file is an executable and don't need compilation")

    # Generate logs
    spike = testlib.Spike(file)
    #spike.generate_logs()
    #spike.generate_extended_logs()
    spike.generate_extended_debug_logs()

##
# Description: Check if the given file exists in the directory
#
# Input: filename (String)
# Output: boolean
def checkFileExists(filename):
    return path.exists(filename)

if __name__ == "__main__":
    main(sys.argv[1:])
