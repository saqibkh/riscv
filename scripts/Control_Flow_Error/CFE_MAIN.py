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
import getopt
import random
import subprocess
import os
from os import path

import compileUtil
import utils
import cfcss
import yacca
import ecca
import rscfc
import trial1


def usage():
    print("Usage: Please provide the absolute path for a C program that matches <file>.c")
    print(
        "Example ./CFE_Main.py src/dir/test/bit_count.c --enable-extras (Must have the entire path to the source file")


def checkFileExists(i_filename):
    if not utils.checkFileExists(i_filename):
        print("file: " + i_filename + " doesn't exist.")
        raise Exception


def main(argv):
    l_enable_extras = False

    if len(sys.argv) == 1:
        usage()
        sys.exit()

    if len(sys.argv) > 2:
        "Check for any more parameters"
        for i in range(len(argv) - 1):
            if argv[i + 1] == '--enable-extras':
                l_enable_extras = True

    file_c = argv[0]
    ''' Create an assembly file and an objdump file from the C program file provided to us '''
    compileUtil.compile_c(file_c)

    l_file_dir = file_c.rsplit('/', 1)[0]
    l_test_name = (file_c.rsplit('/', 1)[1]).rsplit('.c')[0]

    # Check if all the assembly and objdump files exist
    file_s = argv[0].rsplit('.')[0] + ".s"
    checkFileExists(file_s)
    file_objdump = argv[0].rsplit('.')[0] + ".objdump"
    checkFileExists(file_objdump)

    #################################################################
    ######                                                     ######
    ######   Start generating the Control Flow Error Detection ######
    ######                                                     ######
    #################################################################

    # Generate CFCSS (Control Flow Checking by Software Signature)
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_cfcss = cfcss.CFCSS(map)
    cfcss_file = argv[0].rsplit('.')[0] + '_cfcss.s'
    with open(cfcss_file, 'w') as filehandle:
        for listitem in i_cfcss.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(cfcss_file)  # Compile the newly created assembly file to generate a static binary

    # Generate YACCA
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_yacca = yacca.YACCA(map)
    yacca_file = argv[0].rsplit('.')[0] + '_yacca.s'
    with open(yacca_file, 'w') as filehandle:
        for listitem in i_yacca.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(yacca_file)  # Compile the newly created assembly file to generate a static binary

    # Generate ECCA
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_ecca = ecca.ECCA(map)
    ecca_file = argv[0].rsplit('.')[0] + '_ecca.s'
    with open(ecca_file, 'w') as filehandle:
        for listitem in i_ecca.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(ecca_file)  # Compile the newly created assembly file to generate a static binary

    # Generate RSCFC
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_rscfc = rscfc.RSCFC(map)
    rscfc_file = argv[0].rsplit('.')[0] + '_rscfc.s'
    with open(rscfc_file, 'w') as filehandle:
        for listitem in i_rscfc.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(rscfc_file)  # Compile the newly created assembly file to generate a static binary

    # Generate TRIAL1
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_trial1 = trial1.TRIAL1(map)
    trial1_file = argv[0].rsplit('.')[0] + '_trial1.s'
    with open(trial1_file, 'w') as filehandle:
        for listitem in i_trial1.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(trial1_file)  # Compile the newly created assembly file to generate a static binary

    # Delete the unnecessary .o .objdump .readelf file
    if not l_enable_extras:
        compileUtil.delete_all_useless_files(l_file_dir, l_test_name)


if __name__ == "__main__":
    main(sys.argv[1:])
