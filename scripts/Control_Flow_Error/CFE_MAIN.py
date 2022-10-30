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

# ---------Set sys.path for CFE_MAIN execution---------------------------------------
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
import rasm
import trial1
import trial2
import trial2_1
import trial3
import trial3_1
import trial3_2
import SEDIS_2_0 as sedis_2_0
import instructions
import sim_logging



def usage():
    print("Usage: Please provide the absolute path for a C program that matches <file>.c")
    print(
        "Example ./CFE_Main.py src/dir/test/bit_count.c --enable-extras (Must have the entire path to the source file")


def checkFileExists(i_filename):
    if not utils.checkFileExists(i_filename):
        print("file: " + i_filename + " doesn't exist.")
        raise Exception


def main(argv):
    l_test = "SEDIS_2_0"
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
    ######   Start generating the Control Flow Error Detection ######
    ######                                                     ######
    #################################################################

#####################################################################################################################
    # Generate RASM (Random Additive Signature Monitoring for Control Flow Error Detection
    if l_test == "ALL" or l_test == "RASM":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing RASM")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_rasm = rasm.RASM(map)
        rasm_file = argv[0].rsplit('.')[0] + '_RASM.s'
        rasm_file_objdump = argv[0].rsplit('.')[0] + '_RASM.objdump'
        with open(rasm_file, 'w') as filehandle:
            for listitem in i_rasm.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(rasm_file)  # Compile the newly created assembly file to generate a static binary

        # Re-read the objdump file to update the address of the jump target
        i_new_asm_file = i_rasm.update_jump_address(utils.readfile(file_objdump), utils.readfile(rasm_file), utils.readfile(rasm_file_objdump))
        with open(rasm_file, 'w') as filehandle:
            for listitem in i_new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(rasm_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(rasm_file), utils.readfile(rasm_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        # Get the instruction count from start to the end of this particular program.
        # Assuming that each instruction  takes 1 cycle count, we can estimate the delay in the
        # program added by this particular implementation
        utils.get_instruction_count(file_s.split('.s')[0], map, rasm_file.split('.s')[0], new_map, simlog=simlog)

        del rasm_file, map, i_rasm, new_map, rasm_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate CFCSS (Control Flow Checking by Software Signature)
    if l_test == "ALL" or l_test == "CFCSS":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing CFCSS")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_cfcss = cfcss.CFCSS(map)
        cfcss_file = argv[0].rsplit('.')[0] + '_CFCSS.s'
        cfcss_file_objdump = argv[0].rsplit('.')[0] + '_CFCSS.objdump'
        with open(cfcss_file, 'w') as filehandle:
            for listitem in i_cfcss.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(cfcss_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(cfcss_file), utils.readfile(cfcss_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del cfcss_file, map, i_cfcss, new_map, cfcss_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate YACCA
    if l_test == "ALL" or l_test == "YACCA":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing YACCA")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_yacca = yacca.YACCA(map)
        yacca_file = argv[0].rsplit('.')[0] + '_YACCA.s'
        yacca_file_objdump = argv[0].rsplit('.')[0] + '_YACCA.objdump'
        with open(yacca_file, 'w') as filehandle:
            for listitem in i_yacca.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(yacca_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(yacca_file), utils.readfile(yacca_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del map, i_yacca, yacca_file, new_map, yacca_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate ECCA
    if l_test == "ALL" or l_test == "ECCA":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing ECCA")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_ecca = ecca.ECCA(map)
        ecca_file = argv[0].rsplit('.')[0] + '_ECCA.s'
        ecca_file_objdump = argv[0].rsplit('.')[0] + '_ECCA.objdump'
        with open(ecca_file, 'w') as filehandle:
            for listitem in i_ecca.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(ecca_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(ecca_file), utils.readfile(ecca_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del map, i_ecca, ecca_file, new_map, ecca_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate RSCFC
    if l_test == "ALL" or l_test == "RSCFC":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing RSCFC")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_rscfc = rscfc.RSCFC(map)
        rscfc_file = argv[0].rsplit('.')[0] + '_RSCFC.s'
        rscfc_file_objdump = argv[0].rsplit('.')[0] + '_RSCFC.objdump'
        with open(rscfc_file, 'w') as filehandle:
            for listitem in i_rscfc.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(rscfc_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(rscfc_file), utils.readfile(rscfc_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del map, i_rscfc, rscfc_file, new_map, rscfc_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL1
    if l_test == "ALL" or l_test == "TRIAL1":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing TRIAL1")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_trial1 = trial1.TRIAL1(map)
        trial1_file = argv[0].rsplit('.')[0] + '_TRIAL1.s'
        trial1_file_objdump = argv[0].rsplit('.')[0] + '_TRIAL1.objdump'
        with open(trial1_file, 'w') as filehandle:
            for listitem in i_trial1.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(trial1_file)  # Compile the newly created assembly file to generate a static binary

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(trial1_file), utils.readfile(trial1_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del map, i_trial1, trial1_file, new_map, trial1_file_objdump
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL2
    if l_test == "ALL" or l_test == "TRIAL2":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing TRIAL2")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_trial2 = trial2.TRIAL2(map)
        trial2_file = argv[0].rsplit('.')[0] + '_TRIAL2.s'
        trial2_file_objdump = argv[0].rsplit('.')[0] + '_TRIAL2.objdump'
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

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(trial2_file), utils.readfile(trial2_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del i_trial2, i_trial2_new, new_map, map, map_new, trial2_s_intermediate_file, trial2_obj_intermediate_file
        del trial2_file, trial2_file_objdump, update_file_required
        simlog.info("Finished processing TRIAL2")
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL2_1
    if l_test == "ALL" or l_test == "TRIAL2_1":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing TRIAL2_1")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_trial2_1 = trial2_1.TRIAL2_1(map)
        trial2_1_file = argv[0].rsplit('.')[0] + '_TRIAL2_1.s'
        trial2_1_file_objdump = argv[0].rsplit('.')[0] + '_TRIAL2_1.objdump'
        with open(trial2_1_file, 'w') as filehandle:
            for listitem in i_trial2_1.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(trial2_1_file)  # Compile the newly created assembly file to generate a static binary

        # My storing signature in memory (compared to loading via instructions) is we save a lot of instructions
        trial2_1.store_signature_in_memory(trial2_1_file, simlog)

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(trial2_1_file), utils.readfile(trial2_1_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        del i_trial2_1, new_map, map
        del trial2_1_file, trial2_1_file_objdump
        simlog.info("Finished processing TRIAL2_1")
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL3
    if l_test == "TRIAL3" or l_test == "TRIAL3":
        simlog.info("------------------------------------------------------------------------------------------------")
        simlog.info("Start processing TRIAL3")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump),
                                          enable_functionMap=True, C_executable_File=file_c_executable, simlog=simlog)
        original_map = map
        i_trial3 = trial3.TRIAL3(map)
        trial3_file = argv[0].rsplit('.')[0] + '_TRIAL3.s'
        trial3_file_objdump = argv[0].rsplit('.')[0] + '_TRIAL3.objdump'

        with open(trial3_file, 'w') as filehandle:
            for listitem in i_trial3.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(trial3_file)  # Compile the newly created assembly file to generate a static binary

        ## Execute the executable binary again and then re-read the register values that needs to be checked
        #  at the start and at the end of a function.
        update_file_required = True
        # loop until we get the same signature values
        while update_file_required:
            trial3_s_intermediate_file = utils.readfile(trial3_file)
            trial3_obj_intermediate_file = utils.readfile(trial3_file.split(".s")[0] + ".objdump")
            map_new = utils.ControlFlowMapRevised(trial3_s_intermediate_file, trial3_obj_intermediate_file,
                                                  enable_functionMap=True,
                                                  C_executable_File=(file_c_executable + "_TRIAL3"), simlog=simlog)

            i_trial3_new = trial3.TRIAL3(map_new, i_recalculate_reg_values=True)
            update_file_required = trial3.update_values(i_trial3, i_trial3_new, trial3_file)
            compileUtil.compile_s(trial3_file)  # Compile the newly created assembly file to generate a static binary
            i_trial3 = i_trial3_new
            map = map_new

        # Update the asm file after all reg values have been modified
        trial3.update_registers(trial3_file)
        #compileUtil.compile_s(trial3_file)  # Compile the newly created assembly file to generate a static binary

        simlog.info("Finished processing TRIAL3")

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(trial3_file), utils.readfile(trial3_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(original_map, new_map, simlog=simlog)

        del map, i_trial3, trial3_file, trial3_file_objdump, i_trial3_new, new_map, trial3_s_intermediate_file
        del trial3_obj_intermediate_file, update_file_required, map_new, original_map
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL3_1
    if l_test == "TRIAL3_1" or l_test == "TRIAL3_1":
        simlog.info(
            "------------------------------------------------------------------------------------------------")
        simlog.info("Start processing TRIAL3_1")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump),
                                          enable_functionMap=True, C_executable_File=file_c_executable,
                                          simlog=simlog)
        original_map = map
        i_trial3_1 = trial3_1.TRIAL3_1(map)
        trial3_1_file = argv[0].rsplit('.')[0] + '_TRIAL3_1.s'
        trial3_1_file_objdump = argv[0].rsplit('.')[0] + '_TRIAL3_1.objdump'

        with open(trial3_1_file, 'w') as filehandle:
            for listitem in i_trial3_1.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(trial3_1_file)  # Compile the newly created assembly file to generate a static binary

        ## Execute the executable binary again and then re-read the register values that needs to be checked
        #  at the start and at the end of a function.
        update_file_required = True
        # loop until we get the same signature values
        while update_file_required:
            trial3_1_s_intermediate_file = utils.readfile(trial3_1_file)
            trial3_1_obj_intermediate_file = utils.readfile(trial3_1_file.split(".s")[0] + ".objdump")
            map_new = utils.ControlFlowMapRevised(trial3_1_s_intermediate_file, trial3_1_obj_intermediate_file,
                                                  enable_functionMap=True,
                                                  C_executable_File=(file_c_executable + "_TRIAL3_1"), simlog=simlog)

            i_trial3_1_new = trial3_1.TRIAL3_1(map_new, i_recalculate_reg_values=True)
            update_file_required = trial3_1.update_values(i_trial3_1, i_trial3_1_new, trial3_1_file)
            compileUtil.compile_s(
                trial3_1_file)  # Compile the newly created assembly file to generate a static binary
            i_trial3_1 = i_trial3_1_new
            map = map_new

        # Update the asm file after all reg values have been modified
        trial3_1.update_registers_update(trial3_1_file)
        #compileUtil.compile_s(trial3_1_file)  # Compile the newly modified assembly file to generate a static binary
        simlog.info("Finished processing TRIAL3_1")

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(trial3_1_file), utils.readfile(trial3_1_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(original_map, new_map, simlog=simlog)

        del map, i_trial3_1, trial3_1_file, trial3_1_file_objdump, i_trial3_1_new, new_map
        del trial3_1_s_intermediate_file
        del trial3_1_obj_intermediate_file, update_file_required, map_new, original_map,
        simlog.info(
            "---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################

#####################################################################################################################
    # Generate TRIAL3
    if l_test == "ALL" or l_test == "TRIAL3_2":
        simlog.info(
            "------------------------------------------------------------------------------------------------")
        simlog.info("Start processing TRIAL3_2")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump),
                                          enable_functionMap=True, C_executable_File=file_c_executable,
                                          simlog=simlog)
        original_map = map
        i_trial3_2 = trial3_2.TRIAL3_2(map)
        trial3_2_file = argv[0].rsplit('.')[0] + '_TRIAL3_2.s'
        trial3_2_file_objdump = argv[0].rsplit('.')[0] + '_TRIAL3_2.objdump'

        with open(trial3_2_file, 'w') as filehandle:
            for listitem in i_trial3_2.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(trial3_2_file)  # Compile the newly created assembly file to generate a static binary

        ## Execute the executable binary again and then re-read the register values that needs to be checked
        #  at the start and at the end of a function.
        update_file_required = True
        # loop until we get the same signature values
        while update_file_required:
            trial3_2_s_intermediate_file = utils.readfile(trial3_2_file)
            trial3_2_obj_intermediate_file = utils.readfile(trial3_2_file.split(".s")[0] + ".objdump")
            map_new = utils.ControlFlowMapRevised(trial3_2_s_intermediate_file, trial3_2_obj_intermediate_file,
                                                  enable_functionMap=True,
                                                  C_executable_File=(file_c_executable + "_TRIAL3_2"), simlog=simlog)

            i_trial3_2_new = trial3_2.TRIAL3_2(map_new, i_recalculate_reg_values=True)
            update_file_required = trial3_2.update_values(i_trial3_2, i_trial3_2_new, trial3_2_file)
            compileUtil.compile_s(
                trial3_2_file)  # Compile the newly created assembly file to generate a static binary
            i_trial3_2 = i_trial3_2_new
            map = map_new

        # Update the asm file after all reg values have been modified
        trial3_2.update_registers(trial3_2_file)
        compileUtil.compile_s(trial3_2_file)  # Compile the newly created assembly file to generate a static binary
        simlog.info("Finished processing TRIAL3_2")

        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(trial3_2_file), utils.readfile(trial3_2_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(original_map, new_map, simlog=simlog)

        del map, i_trial3_2, trial3_2_file, trial3_2_file_objdump, i_trial3_2_new, new_map, trial3_2_s_intermediate_file
        del trial3_2_obj_intermediate_file, update_file_required, map_new, original_map
        simlog.info("---------------------------------------------------------------------------------------------\n\n")
#####################################################################################################################

#####################################################################################################################
    # Generate SEDIS_2_0
    if l_test == "ALL" or l_test == "SEDIS_2_0":
        simlog.info(
            "------------------------------------------------------------------------------------------------")
        simlog.info("Start processing SEDIS_2_0")
        map = utils.ControlFlowMapRevised(utils.readfile(file_s), utils.readfile(file_objdump), simlog=simlog)
        i_sedis_2_0 = sedis_2_0.SEDIS_2_0(map)
        sedis_2_0_file = argv[0].rsplit('.')[0] + '_SEDIS_2_0.s'
        sedis_2_0_file_objdump = argv[0].rsplit('.')[0] + '_SEDIS_2_0.objdump'
        with open(sedis_2_0_file, 'w') as filehandle:
            for listitem in i_sedis_2_0.new_asm_file:
                filehandle.write('%s\n' % listitem)
        compileUtil.compile_s(sedis_2_0_file)  # Compile the newly created assembly file to generate a static binary

        ## Re-read the <test>_intermediate_trial2 objdump and .s file and form the Control Flow Graph again
        update_file_required = True
        # loop until we get the same signature values
        while update_file_required:
            sedis_2_0_s_intermediate_file = utils.readfile(sedis_2_0_file)
            sedis_2_0_obj_intermediate_file = utils.readfile(sedis_2_0_file.split(".s")[0] + ".objdump")
            sedis_2_0_s_intermediate_file, sedis_2_0_obj_intermediate_file = i_sedis_2_0.remove_signature_checking(
                sedis_2_0_s_intermediate_file, sedis_2_0_obj_intermediate_file)

            #################################################################################
            # This is only for debug purposes and can be removed after all fixes are in place.
            # Write the .s and .objdump file to debug the difference
            #i_intermediate_s_file = sedis_2_0_file.rsplit(".s")[0] + "_intermediate.s"
            #with open(i_intermediate_s_file, 'w') as filehandle:
            #    for listitem in sedis_2_0_s_intermediate_file:
            #        filehandle.write('%s\n' % listitem)
            #i_intermediate_objdump_file = sedis_2_0_file.rsplit(".s")[0] + "_intermediate.objdump"
            #with open(i_intermediate_objdump_file, 'w') as filehandle:
            #    for listitem in sedis_2_0_obj_intermediate_file:
            #        filehandle.write('%s\n' % listitem)
            #################################################################################
            #################################################################################

            map_new = utils.ControlFlowMapRevised(sedis_2_0_s_intermediate_file, sedis_2_0_obj_intermediate_file)
            map_new = sedis_2_0.update_blocks(map, map_new)
            #map_new = i_sedis_2_0.update_opcodes(map, map_new)
            i_sedis_2_0_new = sedis_2_0.SEDIS_2_0(map_new, i_generate_signature_only=True)
            # We have old and new signatures in sedis_2_0 and sedis_2_0_new respectively.
            update_file_required = sedis_2_0.update_signature(i_sedis_2_0, i_sedis_2_0_new, sedis_2_0_file)
            compileUtil.compile_s(sedis_2_0_file)  # Compile the newly created assembly file to generate a static binary

            i_sedis_2_0 = i_sedis_2_0_new
            map = map_new



        # Get the memory_size of the original and modified file and find it's diff
        new_map = utils.ControlFlowMapRevised(utils.readfile(sedis_2_0_file), utils.readfile(sedis_2_0_file_objdump),
                                              simlog=simlog)
        utils.get_memory_size_info(map, new_map, simlog=simlog)

        #del i_sedis_2_0, i_sedis_2_0_new, new_map, map, map_new, trial2_s_intermediate_file, sedis_2_0_obj_intermediate_file
        #del sedis_2_0_file, sedis_2_0_file_objdump, update_file_required
        simlog.info("Finished processing SEDIS_2_0")
        simlog.info(
            "---------------------------------------------------------------------------------------------\n\n")
    #####################################################################################################################


    # Delete the unnecessary .o .objdump .readelf file
    if not l_enable_extras:
        compileUtil.delete_all_useless_files(l_file_dir, l_test_name)


if __name__ == "__main__":
    main(sys.argv[1:])
