#!/usr/bin/python


##############################################################################
#
# This file will be used to auto-generate the modified assembly files
# for Control Flow Error Detection techniques, which includes
# 1) Control Flow Checking by Software Signature (CFCSS)
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
from os import path

#---------Set sys.path for CFE_MAIN execution---------------------------------------
full_path = os.path.abspath(os.path.dirname(sys.argv[0])).split('riscv')[0]
sys.path.append(full_path)
# Walk path and append to sys.path
for root, dirs, files in os.walk(full_path):
    for dir in dirs:
        sys.path.append(os.path.join(root, dir))

import compileUtil
import utils
import cfcss
import yacca
import ecca
import rscfc
import trial1
import trial2
import trial3
import instructions


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

    print("Processing file: " + argv[0])
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

#####################################################################################################################
    # Generate CFCSS (Control Flow Checking by Software Signature)
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_cfcss = cfcss.CFCSS(map)
    cfcss_file = argv[0].rsplit('.')[0] + '_cfcss.s'
    with open(cfcss_file, 'w') as filehandle:
        for listitem in i_cfcss.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(cfcss_file)  # Compile the newly created assembly file to generate a static binary
    del cfcss_file, map, i_cfcss
#####################################################################################################################

#####################################################################################################################
    # Generate YACCA
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_yacca = yacca.YACCA(map)
    yacca_file = argv[0].rsplit('.')[0] + '_yacca.s'
    with open(yacca_file, 'w') as filehandle:
        for listitem in i_yacca.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(yacca_file)  # Compile the newly created assembly file to generate a static binary
    del map, i_yacca, yacca_file
#####################################################################################################################

#####################################################################################################################
    # Generate ECCA
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_ecca = ecca.ECCA(map)
    ecca_file = argv[0].rsplit('.')[0] + '_ecca.s'
    with open(ecca_file, 'w') as filehandle:
        for listitem in i_ecca.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(ecca_file)  # Compile the newly created assembly file to generate a static binary
    del map, i_ecca, ecca_file
#####################################################################################################################

#####################################################################################################################
    # Generate RSCFC
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_rscfc = rscfc.RSCFC(map)
    rscfc_file = argv[0].rsplit('.')[0] + '_rscfc.s'
    with open(rscfc_file, 'w') as filehandle:
        for listitem in i_rscfc.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(rscfc_file)  # Compile the newly created assembly file to generate a static binary
    del map, i_rscfc, rscfc_file
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL1
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_trial1 = trial1.TRIAL1(map)
    trial1_file = argv[0].rsplit('.')[0] + '_trial1.s'
    with open(trial1_file, 'w') as filehandle:
        for listitem in i_trial1.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(trial1_file)  # Compile the newly created assembly file to generate a static binary
    del map, i_trial1, trial1_file
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL2
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_trial2 = trial2.TRIAL2(map)
    trial2_file = argv[0].rsplit('.')[0] + '_trial2.s'
    with open(trial2_file, 'w') as filehandle:
        for listitem in i_trial2.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(trial2_file)  # Compile the newly created assembly file to generate a static binary

    ## Re-read the <test>_intermediate_trial2 objdump and .s file and form the Control Flow Graph again
    update_file_required = True
    # loop until we get the same signature values
    while update_file_required:
        trial2_s_intermediate_file = utils.readfile(trial2_file)
        trial2_obj_intermediate_file = utils.readfile(trial2_file.split(".s")[0] + ".objdump")
        trial2_s_intermediate_file, trial2_obj_intermediate_file = i_trial2.remove_signature_checking(
            trial2_s_intermediate_file, trial2_obj_intermediate_file)
        map_new = utils.ControlFlowMapRevised(trial2_s_intermediate_file, trial2_obj_intermediate_file)
        map_new = i_trial2.update_opcodes(map, map_new)
        i_trial2_new = trial2.TRIAL2(map_new, i_generate_signature_only=True)
        # We have old and new signatures in i_trial2 and i_trial2_new respectively.
        update_file_required = trial2.update_signature(i_trial2, i_trial2_new, trial2_file)
        compileUtil.compile_s(trial2_file)  # Compile the newly created assembly file to generate a static binary

        i_trial2 = i_trial2_new
        map = map_new

    print("Finished processing TRIAL2")
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL3
    map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump))
    i_trial3 = trial3.TRIAL3(map)
    trial3_file = argv[0].rsplit('.')[0] + '_trial3.s'
    with open(trial3_file, 'w') as filehandle:
        for listitem in i_trial3.new_asm_file:
            filehandle.write('%s\n' % listitem)
    compileUtil.compile_s(trial3_file)  # Compile the newly created assembly file to generate a static binary
    del map, i_trial3, trial3_file
#####################################################################################################################

#####################################################################################################################

    # Delete the unnecessary .o .objdump .readelf file
    if not l_enable_extras:
        compileUtil.delete_all_useless_files(l_file_dir, l_test_name)


if __name__ == "__main__":
    main(sys.argv[1:])
