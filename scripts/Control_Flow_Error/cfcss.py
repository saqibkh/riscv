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


# TODO:
#       1. Test the code with an example where a block calls itself (this might not be supported).
#       2. compile-time signature shouldn't start from 0. Better to make them a random bit sequence
#

class CFCSS:
    def __init__(self, i_map):
        self.original_map = i_map
        # Compile time signature
        self.compile_time_sig = []
        # Defines a valid branch to a block signature
        self.valid_branch_d = []
        # Extended signature
        self.D_sig = [None] * len(i_map.blocks)
        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]

        self.new_asm_file = self.original_map.file_asm

        self.generate_instruction_mapping()
        self.process_CFCSS_blocks()
        self.generate_CFCSS_file_updated()

    def generate_CFCSS_file_updated(self):

        i_block = 0
        i_line_num_new_asm_file = 0

        # 1. Loop the asm file lines until the end of file
        while(i_line_num_new_asm_file < len(self.new_asm_file)):

            # Return once all the blocks are processed
            if i_block == len(self.original_map.blocks):
                return

            block_found = False
            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]

            # There are two cases where a basic block can start from
            # 1. When a function beings within the asm file (make sure the first instruction within the function and the block matches one another)
            if not i_line_asm.startswith('\t'):
                # Make sure the first instruction in asm function matches the first instruction in the block
                # Get the first instruction in this particular block for comparison
                i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                # i_line_block_asm could get multiple hits
                i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                for i in range(len(i_line_block_asm)):
                    if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] == i_line_block_asm[i]:
                        block_found = True
                        del i_line_block_obj, i_line_block_asm
                        break

            # 2. When a branch instruction is present within the function itself
            #    and the next instruction is the starting instruction of the next block
            else: # Line starts with '\t'
                i_line_asm = i_line_asm.split('\t', 1)[1]
                if not i_line_asm.startswith('.'):
                    if utils.is_branch_instruction(i_line_asm):
                        # Get the first instruction in the next block for comparison
                        try:
                            i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                        except:
                            print('done')
                        i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                        try:
                            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1]
                            for i in range(len(i_line_block_asm)):
                                if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] == i_line_block_asm[i]:
                                    block_found = True
                                    break
                        except:
                            #unexpected line encountered
                            i_line_num_new_asm_file += 1
                            continue

            if block_found:
                i_line_num_new_asm_file += 1
                inst_xori = '\txori\ts11,s11,' + str(self.valid_branch_d[i_block])
                inst_li = '\tli\tt6,' + str(self.compile_time_sig[i_block])
                inst_branch_exception_handler = '\tbne\ts11,t6,' + utils.exception_handler_address
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_branch_exception_handler)
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_li)

                # If more than 1 incoming blocks then we need to account for the extended
                # signature checking
                if len(self.original_map.blocks[i_block].previous_block_id) > 1:
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                    i_line_num_new_asm_file += 1

                self.new_asm_file.insert(i_line_num_new_asm_file, inst_xori)
                i_line_num_new_asm_file += 3

                # Get to the last instruction in the block and then add the extended signature
                for i in range(len(self.original_map.blocks[i_block].entries) - 1):
                    i_line_num_new_asm_file += 1

                # If there are no outputs blocks then don't add an extended signature
                if len(self.original_map.blocks[i_block].next_block_id) != 0:
                    # loop through all the next blocks
                    for i in range(len(self.original_map.blocks[i_block].next_block_id)):
                        if self.D_sig[i_block] != None:
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(self.D_sig[i_block]))
                        else:
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,0')

                i_block += 1

            i_line_num_new_asm_file += 1

        if i_block != len(self.original_map.blocks):
            print('Failed to process all blocks. Currently at block id # ' + str(i_block))
            raise Exception

    def generate_CFCSS_file(self):
        line_new_asm_file = 0
        line_obj = 0
        line_instruction_map = 0


        # 1. Get the first instruction of each block
        for i in range(len(self.original_map.blocks)):
            i_asm_instruction = None
            first_inst_in_block = self.original_map.blocks[i].entries[0]
            last_inst_in_block = self.get_matching_asm_line_using_objdump_line(self.original_map.blocks[i].entries[-1])[0]
            if len(i_line_block_asm) != 1:
                print('We found multiple matches of this particular instruction in the asm/obj mapping file')
                raise Exception

            # 2. Find the corresponding objdump instruction in the objdump file
            while line_instruction_map < len(self.instruction_map[0]):
                i_line = self.instruction_map[1][line_instruction_map]
                if first_inst_in_block == self.instruction_map[1][line_instruction_map]:
                    # 3. Get the corresponding asm instruction from the .s file
                    i_asm_instruction = self.instruction_map[0][line_instruction_map]
                    break
                else:
                    line_instruction_map += 1

            if not i_asm_instruction:
                print('Failed to find the corresponding asm instruction')
                raise Exception
            # 4. Find the corresponding instruction in the new_asm_file
            while line_new_asm_file < len(self.new_asm_file):
                i_line = self.new_asm_file[line_new_asm_file]
                # Ignore lines that are not instructions
                if not self.is_instruction_asm(i_line):
                    line_new_asm_file += 1
                    continue

                # 5. Insert valid_branch and signature checking at the start of that block
                #    Also add the extended signature checking before the final instruction
                i_line = i_line.split('\t', 1)[1]
                if i_line == i_asm_instruction:
                    inst_xori = '\txori\ts11,s11,' + str(self.valid_branch_d[i])
                    inst_li = '\tli\tt6,' + str(self.compile_time_sig[i])
                    inst_branch_exception_handler = '\tbne\ts11,t6,' + utils.exception_handler_address
                    self.new_asm_file.insert(line_new_asm_file, inst_branch_exception_handler)
                    self.new_asm_file.insert(line_new_asm_file, inst_li)

                    # If more than 1 incoming blocks then we need to account for the extended
                    # signature checking
                    if len(self.original_map.blocks[i].previous_block_id) > 1:
                        self.new_asm_file.insert(line_new_asm_file, '\txor\ts11,s11,s10')

                    self.new_asm_file.insert(line_new_asm_file, inst_xori)
                    line_new_asm_file += 4
                    block_complete=True
                    break

                line_new_asm_file += 1

    def get_matching_asm_line_using_objdump_line(self, i_line):
        # Definition: Checks for a matching line in the objdump file and returns the
        #             corresponding asm line
        line_instruction_map = 0
        list_matching_objects = []

        while line_instruction_map < len(self.instruction_map[0]):
            if i_line == self.instruction_map[1][line_instruction_map]:
                i_asm_instruction = self.instruction_map[0][line_instruction_map]
                list_matching_objects.append(i_asm_instruction)
            line_instruction_map += 1
        return list_matching_objects

    def process_CFCSS_blocks(self):

        # 1. Generate compile time signature for each block
        #    s_i is a unique bit sequence for each block
        # We need a seed to be able reproduce an errors
        random.seed(a=1, version=2)
        self.compile_time_sig = random.sample(range(1, len(self.original_map.blocks)*2), len(self.original_map.blocks))

        # 2. Generate the valid branch for each block
        #    Valid branch (d_i) is calculated as: d_i = s_i XOR s_pred1 (predecessor 1)
        for i in range(len(self.original_map.blocks)):
            s_i = self.compile_time_sig[i]

            # First make sure that a predecessor block exist which might not always be true
            # Main will not have an incoming block.
            if not self.original_map.blocks[i].previous_block_id:
                s_pred1 = s_i
                d_i = s_i
            else:
                # 0th elements points to first predecessor
                s_pred1 = self.get_signature_based_on_id(self.original_map.blocks[i].previous_block_id[0])
                d_i = s_i ^ s_pred1
            self.valid_branch_d.append(d_i)
            del d_i, s_i, s_pred1

        # 3. Generate D (run-time adjusting signature). When a basic block has multiple incoming edges,
        # the signature uses an extra variable D. This variable is updated by the predecessor basic blocks
        # and ensures that the run-time signature can be updated to the correct value,
        # regardless of which predecessor has executed.
        for i in range(len(self.original_map.blocks)):
            if len(self.original_map.blocks[i].previous_block_id) > 1:
                # Get the signature of the first incoming block
                predesessor_block_id_1 = self.original_map.blocks[i].previous_block_id[0]
                D_sign = self.compile_time_sig[predesessor_block_id_1]

                for j in range(len(self.original_map.blocks[i].previous_block_id) - 1):
                    predesessor_block_id_next = self.original_map.blocks[i].previous_block_id[j+1]
                    # Get the ID of the incoming blocks
                    incoming_block_id = self.original_map.blocks[i].previous_block_id[j+1]
                    self.D_sig[incoming_block_id] = D_sign ^ self.compile_time_sig[predesessor_block_id_next]
        print('Finished processing CFCSS.')

    def get_signature_based_on_id(self, i_id):
        for i in range(len(self.original_map.blocks)):
            if self.original_map.blocks[i].id == i_id:
                return self.compile_time_sig[i]

    def generate_instruction_mapping(self):
        # Definition: This creates a 1-1 mapping between instructions in .s file and .objdump file
        instruction_map_asm = []
        instruction_map_obj = []

        # Process the instructions in .s file first
        for i in range(len(self.original_map.functions.f_names)):
            f_name = self.original_map.functions.f_names[i]
            for j in range(len(self.original_map.file_asm)):
                i_line = self.original_map.file_asm[j]
                if not i_line.startswith(f_name):
                    continue
                # Found the start of the function definition in .s file
                j+=1
                while True:

                    try:
                        i_line = self.original_map.file_asm[j]
                    except Exception as e:
                        #print('Reached end of file')
                        break
                    if self.is_instruction_asm(i_line):
                        instruction_map_asm.append(i_line.split('\t', 1)[1])
                    j+=1
                    # Check when a new function begins so we can exit this loop
                    if not (i_line.startswith('.') or i_line.startswith('\t')):
                        finish_function = True
                        break
                if finish_function:
                    finish_function = False
                    break

        # Now Process the instructions in .objdump file
        for i in range(len(self.original_map.functions.f_names)):
            for j in range(len(self.original_map.functions.f_instructions[i].instruction)):
                instruction_map_obj.append(self.original_map.functions.f_instructions[i].instruction[j])

        # Form a 2-dimensional array with instructions from both .s and .obj file
        if(len(instruction_map_asm) != len(instruction_map_obj)):
            print('Number of instructions is not the same in both .s and .obj file')
            raise Exception
        self.instruction_map = [instruction_map_asm, instruction_map_obj]

    def get_length_all_instruction(self):
        # Definition: gets the total number of instruction present in all the basic blocks
        inst_len = 0
        for i in range(len(self.original_map.blocks)):
            inst_len += len(self.original_map.blocks[i].entries)
        return inst_len

    def is_instruction_asm(self, i_line):
        # Definition: checks if the provided line is a valid instruction in the asm file
        if not i_line.startswith('\t'):
            return False
        i_line = i_line.strip('\t')
        if i_line.startswith('.'):
            return False
        return True

