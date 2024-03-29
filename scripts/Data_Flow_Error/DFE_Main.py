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

import eddddi
import eddi
import swift

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
    # Generate EDDDDI
    if l_test == "ALL" or l_test == "EDDDDI":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing EDDDDI")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_eddddi = eddddi.EDDDDI(map)
        eddddi_file = argv[0].rsplit('.')[0] + '_EDDDDI.s'
        eddddi_file_objdump = argv[0].rsplit('.')[0] + '_EDDDDI.objdump'
        with open(eddddi_file, 'w') as filehandle:
            for listitem in i_eddddi.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(eddddi_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(eddddi_file), utils.readfile(eddddi_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del eddddi_file, map, i_eddddi, new_map, eddddi_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")


#####################################################################################################################
    # Generate EDDI
    if l_test == "ALL" or l_test == "EDDI":
        simlog.info(
            "------------------------------------------------------------------------------------------------")
        simlog.info("Start processing EDDI")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_eddi = eddi.EDDI(map)
        eddi_file = argv[0].rsplit('.')[0] + '_EDDI.s'
        eddi_file_objdump = argv[0].rsplit('.')[0] + '_EDDI.objdump'
        with open(eddi_file, 'w') as filehandle:
            for listitem in i_eddi.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(eddi_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(eddi_file), utils.readfile(eddi_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del eddi_file, map, i_eddi, new_map, eddi_file_objdump
        simlog.info(
            "---------------------------------------------------------------------------------------------\n\n")

#####################################################################################################################
    # Generate SWIFT
    if l_test == "ALL" or l_test == "SWIFT":
        simlog.info(
            "------------------------------------------------------------------------------------------------")
        simlog.info("Start processing SWIFT")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_swift = swift.SWIFT(map)
        swift_file = argv[0].rsplit('.')[0] + '_SWIFT.s'
        swift_file_objdump = argv[0].rsplit('.')[0] + '_SWIFT.objdump'
        with open(swift_file, 'w') as filehandle:
            for listitem in i_swift.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(swift_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(swift_file), utils.readfile(swift_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del swift_file, map, i_swift, new_map, swift_file_objdump
        simlog.info(
            "---------------------------------------------------------------------------------------------\n\n")

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