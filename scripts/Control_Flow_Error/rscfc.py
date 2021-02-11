#!/usr/bin/python

import sys
import logging
import time
import string
import datetime
import random
import subprocess
import utils
from os import path


class RSCFC:
    def __init__(self, i_map):
        self.simlog = i_map.simlog
        self.original_map = i_map

        # Compile time signature (s_i)
        self.compile_time_sig = [None] * len(i_map.blocks)

        # CFG Locator L_i
        self.L_i = [None] * len(i_map.blocks)

        # Cumulative signature (m_i)
        self.m_i = [None] * len(i_map.blocks)

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        utils.generate_instruction_mapping(self)

        self.generate_cumulative_sig()
        self.generate_CFG_Locator()
        self.generate_compile_Sig()

        self.generate_RSCFC_file_updated()

        self.simlog.info("Finished processing RSCFC")

    ''' Beginning of class function definitions '''
    def generate_RSCFC_file_updated(self):
        i_block = 0
        i_line_num_new_asm_file = 0

        # 1. Loop the asm file lines until the end of file
        while i_line_num_new_asm_file < len(self.new_asm_file):

            # Return once all the blocks are processed
            if i_block == len(self.original_map.blocks):
                return

            block_found = False
            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]

            # A basic block will start when the line matches the first line of that particular block
            if i_line_asm.startswith('\t'):
                i_line_asm = i_line_asm.split('\t', 1)[1]
                if not i_line_asm.startswith('.'):
                    i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                    i_line_block_asm = utils.get_matching_asm_line_using_objdump_line(self.instruction_map,
                                                                                      i_line_block_obj)
                    try:
                        i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file].split('\t', 1)[1]
                        for i in range(len(i_line_block_asm)):
                            if self.original_map.file_asm[i_line_num_new_asm_file].split('\t', 1)[1] in \
                                    i_line_block_asm[i]:
                                block_found = True

                                del i_line_block_obj, i_line_block_asm, i_line_asm
                                break
                    except Exception as e:
                        # unexpected line encountered
                        i_line_num_new_asm_file += 1
                        continue

            if block_found:
                # 0. S = s_i & (S XNOR L_i) & (-!N)

                # For initial basic block we need to load 1 into s11 which
                # is the register that will hold the run-time S.
                if len(self.original_map.blocks[i_block].previous_block_id) == 0:
                    inst_mov_s11_sig = '\tli\ts11,1'
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_mov_s11_sig)
                    i_line_num_new_asm_file += 1

                # 1. AND the runtime signature with the compile time signature and make sure the result
                #    not equal to zero
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts9,' + str(int(self.L_i[i_block],2)))
                i_line_num_new_asm_file += 1
                inst_AND_s11_compile_sig = '\tand\ts11,s11,s9'
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_AND_s11_compile_sig)
                i_line_num_new_asm_file += 1
                inst_AND_COMP_EQ_ZERO = '\tbeqz\ts11,' + utils.exception_handler_address
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_AND_COMP_EQ_ZERO)
                i_line_num_new_asm_file += 1

                # Don't need to check for cummulative signature anymore as this is the end block or
                # if there is only 1 inst within the block and if that inst is a branch instruction (i.e. m_i = ob)
                if (len(self.original_map.blocks[i_block].next_block_id) > 0) and self.m_i[i_block] != '0b':
                    # 2. Load the cummulative signature N into register s10
                    inst_cumm_sig_N = '\tli\ts10,' + str(int(self.m_i[i_block],2))
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_cumm_sig_N)
                    i_line_num_new_asm_file += 1

                    # 3. This section implements the intra-block part of RSCFC.
                    #
                    for i in range(len(self.original_map.blocks[i_block].entries)):
                        # We can't check the final branch instruction in he basic block
                        if utils.is_branch_instruction(self.original_map.file_asm[i_line_num_new_asm_file].split('\t', 1)[-1]):
                            break
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts9,' + str(int(1 << i)))
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts10,s10,s9')
                        i_line_num_new_asm_file += 1

                    # 4. Check the cummulative signature and then update the run-time signature
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts9,' + str(int(self.L_i[i_block], 2)))
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s9')
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txori\ts11,s11,-1')
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txori\ts10,s10,-1')
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tand\ts11,s11,s10')
                    i_line_num_new_asm_file += 1

                    # We will store the expected compile time sig in s10 temporarily
                    x = str(int(self.compile_time_sig[i_block],2))
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(int(self.compile_time_sig[i_block],2)))
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file,
                                             '\tbeq\ts11,s10,' + utils.exception_handler_address)
                    i_line_num_new_asm_file += 1

                # Finish processing the block
                i_block += 1

            i_line_num_new_asm_file += 1


    def generate_compile_Sig(self):
        # Get the base/original compile time signature for all basic branches.
        # If there are n basic blocks in the CFG, the signature is n+1 bits wide
        i_basic_sig = '0b1'
        for i in range(len(self.original_map.blocks)):
            i_basic_sig += '0'

        # Set the basic compile time sig for all basic blocks
        for i in range(len(self.original_map.blocks)):
            self.compile_time_sig[i] = i_basic_sig

        # Loop through the basic blocks to set the correct compile time signature
        for i in range(len(self.original_map.blocks)):

            # 1. It is possible that the basic block is an end block and thus no compile time sig.
            #    In this case, set the sig to None
            if len(self.original_map.blocks[i].next_block_id) == 0:
                self.compile_time_sig[i] = None

            i_current_block_sig = self.compile_time_sig[i]  # .split('0b')[-1]
            # 2. For all remaining blocks, the bits of the successor blocks are set to 1
            for j in range(len(self.original_map.blocks[i].next_block_id)):
                i_next_block_sig = self.L_i[self.original_map.blocks[i].next_block_id[j]]
                i_current_block_sig = bin(int(i_current_block_sig, 2) | int(i_next_block_sig, 2))

            # Write the compile_time sig back to the list
            self.compile_time_sig[i] = i_current_block_sig

    def generate_CFG_Locator(self):
        next_L_i = '0b10'
        for i in range(len(self.original_map.blocks)):
            # Look for the first basic block in CFG and set its L-i to 0x1
            if len(self.original_map.blocks[i].previous_block_id) == 0:
                self.L_i[i] = '0b1'
            else:
                self.L_i[i] = next_L_i
                next_L_i += '0'

    def generate_cumulative_sig(self):
        for i in range(len(self.original_map.blocks)):
            cum_sig = '0b0'

            # We are not going to count the final branch instruction within the basic block
            for j in range(len(self.original_map.blocks[i].entries)):
                # Get the instruction
                i_inst = utils.get_instruction(self.original_map.blocks[i].entries[j])
                if not utils.is_branch_instruction(i_inst):
                    cum_sig += '1'
                else:
                    # We found a branch instruction in the end of a basic block.
                    # Therefore, we are not going to add another bit in the cumulative signature.
                    continue

            self.m_i[i] = cum_sig
