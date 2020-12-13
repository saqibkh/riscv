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


class YACCA:
    def __init__(self, i_map):
        self.original_map = i_map

        # Compile time signature (B_i)
        self.compile_time_sig = []

        # Previous represents all predecessor blocks of the current basic block.
        # It is calculated by multiplying compile-time signatures of all predecessor
        # blocks of he current basic block
        self.previous = []

        # M1 is only assigned to basic blocks with 2 predecessors
        # M1 = B_pred1 Exclusive NOR B_pred2
        self.M1 = [None] * len(i_map.blocks)

        # M2 represents both the current block and its predecessor
        # M2 = B_pred Exclusive OR B_i, or
        # M2 = B_pred1 AND M1_i Exclusive OR B_i
        self.M2 = [None] * len(i_map.blocks)

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        utils.generate_instruction_mapping(self)

        # 1) Generate compile time signatures (B_i) for each block
        random.seed(a=1, version=2)
        self.compile_time_sig = random.sample(range(1, len(self.original_map.blocks) * 2),
                                              len(self.original_map.blocks))

        # 2) Generate the 2nd compile-time variable named Previous
        self.generate_Previous()

        # 3) Generate M1 for blocks with 2 predecessors
        self.generate_M1()

        # 4) Generate M2 which is the fourth compile-time variable
        self.generate_M2()

        self.generate_YACCA_file_updated()

        print("Finished processing YACCA")
        return

    ''' Beginning of class function definitions '''
    def generate_YACCA_file_updated(self):
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

                # For initial basic block we need to load 1 into s11
                if len(self.original_map.blocks[i_block].previous_block_id) == 0:
                    inst_mov_s11_sig = '\tli\ts11,1'
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_mov_s11_sig)
                    i_line_num_new_asm_file += 1

                inst_mov_s10_prev = '\tli\ts10,' + str(self.previous[i_block])
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_mov_s10_prev)
                i_line_num_new_asm_file += 1

                inst_modulo = '\tremu\ts9,s10,s11'
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_modulo)
                i_line_num_new_asm_file += 1

                inst_branch_sig_check = '\tbnez\ts9,' + utils.exception_handler_address
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_branch_sig_check)
                i_line_num_new_asm_file += 1

                # Get to the last instruction in the block and then add the extended signature
                for i in range(len(self.original_map.blocks[i_block].entries) - 1):
                    i_line_num_new_asm_file += 1

                # If there are no outputs blocks then don't add an extended signature (M1 and M2)
                if len(self.original_map.blocks[i_block].next_block_id) != 0:
                    if self.M1[i_block] is not None:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tand\ts11,s11,' + str(self.M1[i_block]))
                        i_line_num_new_asm_file += 1

                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txori\ts11,s11,' + str(self.M2[i_block]))

                # Finish processing the block
                i_block += 1

            i_line_num_new_asm_file += 1



    def generate_Previous(self):
        for i in range(len(self.original_map.blocks)):
            # Take care of case where there is no incoming block (i.e. Main())
            if len(self.original_map.blocks[i].previous_block_id) == 0:
                self.previous.append(0)

            # Block with only 1 incoming block
            elif len(self.original_map.blocks[i].previous_block_id) == 1:
                self.previous.append(self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]])

            # Block with 2 incoming blocks
            elif len(self.original_map.blocks[i].previous_block_id) == 2:
                sig_1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                sig_2 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[1]]
                self.previous.append(sig_1 * sig_2)

            elif len(self.original_map.blocks[i].previous_block_id) == 3:
                sig_1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                sig_2 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[1]]
                sig_3 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[2]]
                self.previous.append(sig_1 * sig_2 * sig_3)

            else:
                print("Too many incoming blocks to generate the \"Previous\" Value")
                raise Exception


    def generate_M1(self):
        for i in range(len(self.original_map.blocks)):
            if len(self.original_map.blocks[i].previous_block_id) < 2:
                continue

            elif len(self.original_map.blocks[i].previous_block_id) == 2:
                sig_1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                sig_2 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[1]]
                self.M1[i] = utils.xnor(sig_1, sig_2)

            elif len(self.original_map.blocks[i].previous_block_id) == 3:
                sig_1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                sig_2 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[1]]
                sig_3 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[2]]
                self.M1[i] = utils.xnor(utils.xnor(sig_1, sig_2), sig_3)
            else:
                print("Too many incoming blocks to generate the \"M1\" Value")
                raise Exception

    def generate_M2(self):
        for i in range(len(self.original_map.blocks)):
            # For blocks that are end blocks i.e. has no outgoing blocks, we don't need to get M2
            if len(self.original_map.blocks[i].next_block_id) == 0:
                continue

            if len(self.original_map.blocks[i].previous_block_id) == 0:
                # M2 = 1 Exclusive OR B_i
                B_i = self.compile_time_sig[i]
                self.M2[i] = 1 ^ B_i

            elif len(self.original_map.blocks[i].previous_block_id) == 1:
                # M2 = B_pred1 Exclusive OR B_i
                B_pred1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                B_i = self.compile_time_sig[i]
                self.M2[i] = B_pred1 ^ B_i

            elif len(self.original_map.blocks[i].previous_block_id) >= 2:
                # M2 = (B_pred1 AND M1_i) Exclusive OR B_i
                B_pred1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                M1_i = self.M1[i]
                B_i = self.compile_time_sig[i]
                self.M2[i] = (B_pred1 & M1_i) ^ B_i

            elif len(self.original_map.blocks[i].previous_block_id) > 2:
                print('We have a problem here as we have more than 2 incoming branches')
                raise Exception

    ''' End of class definitions '''
