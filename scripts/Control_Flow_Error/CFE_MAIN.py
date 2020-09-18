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
import utils
import cfcss
import os

from os import path


def usage():
    print("Usage: Please provide a test that has corresponding file names that matches <file>.s <file>.objdump")
    print("Example ./TMMain.py src/dir/test/bit_count    (Must have bit_count.s and bit_count.objdump files in the "
          "folder)")


def main(argv):
    if len(sys.argv) == 1:
        usage()
        sys.exit()

    # Check if all the assembly and objdump files exist
    file = argv[0] + ".s"
    if not utils.checkFileExists(file):
        print("file: " + file + " doesn't exist.")
        return 1
    f_asm = utils.readfile(file)
    file = argv[0] + ".objdump"
    if not utils.checkFileExists(file):
        print("file: " + file + " doesn't exist.")
        return 1
    f_obj = utils.readfile(file)
    del file

    # Create a Control Flow Graph
    map = utils.ControlFlowMapRevised(f_asm, f_obj)

    # Generate CFCSS (Control Flow Checking by Software Signature)
    i_cfcss = cfcss.CFCSS(map)

    cfcss_file = argv[0] + '_cfcss.s'
    with open(cfcss_file, 'w') as filehandle:
        for listitem in i_cfcss.new_asm_file:
            filehandle.write('%s\n' % listitem)
    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
