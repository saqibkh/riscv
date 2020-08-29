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

    # Check if the assembly file exist
    file = argv[0]
    if(checkFileExists(file) == False):
        print("The assembly file %s doesn't exist" %file)
        return 1


    binary_file = testlib.compile(file)

    # Generate logs
    spike = testlib.Spike(binary_file)
    spike.generate_logs()
    spike.generate_extended_logs()
    #spike.generate_extended_debug_logs()



##
# Description: Check if the given file exists in the directory
#
# Input: filename (String)
# Output: boolean
def checkFileExists(filename):
    return path.exists(filename)



if __name__ == "__main__":
    main(sys.argv[1:])