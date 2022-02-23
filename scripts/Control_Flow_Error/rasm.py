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


class RASM:
    def __init__(self, i_map):
        self.simlog = i_map.simlog
        self.original_map = i_map

        # Each block must posses a unique random number
        self.random_sig = []
        # assign a random subtract value
        self.subRanPrevVal = []

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm
        self.generate_instruction_mapping()
        self.process_RASM_blocks()
        self.generate_RASM_file_updated()

        # Delete all lines that includes #Deleteme
        self.remove_unused_lines()

    def remove_unused_lines(self):
        i_line_num = 0
        while i_line_num != len(self.new_asm_file):
            i_line = self.new_asm_file[i_line_num]
            if "#Deleteme" in i_line:
                del self.new_asm_file[i_line_num]
            else:
                i_line_num += 1

    def generate_RASM_file_updated(self):
        i_block = 0
        i_line_num_new_asm_file = 0

        # 1. Loop the asm file lines until the end of file
        while i_line_num_new_asm_file < len(self.new_asm_file):

            # Return once all the blocks are processed
            if i_block == len(self.original_map.blocks):
                return

            block_found = False
            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]

            # There are two cases where a basic block can start from
            # 1. When a function beings within the asm file (make sure the first instruction within the function
            # and the block matches one another)
            if not i_line_asm.startswith('\t'):
                # Make sure the first instruction in asm function matches the first instruction in the block
                # Get the first instruction in this particular block for comparison
                i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                # i_line_block_asm could get multiple hits
                i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                for i in range(len(i_line_block_asm)):
                    if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] in i_line_block_asm[i]:
                        block_found = True
                        del i_line_block_obj, i_line_block_asm
                        break

            # 2. When a branch instruction is present within the function itself
            #    and the next instruction is the starting instruction of the next block
            else:  # Line starts with '\t'
                i_line_asm = i_line_asm.split('\t', 1)[1]
                if not i_line_asm.startswith('.'):
                    if utils.is_branch_instruction(i_line_asm):
                        # Get the first instruction in the next block for comparison
                        try:
                            i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                        except:
                            self.simlog.debug('done')
                        i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                        try:
                            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1]
                            for i in range(len(i_line_block_asm)):
                                if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] in \
                                        i_line_block_asm[i]:
                                    block_found = True
                                    break
                        except:
                            # unexpected line encountered
                            i_line_num_new_asm_file += 1
                            continue

            if block_found:

                # If this is the main block, then load the initial value for the run-time register,
                # which will be random_Sig - subRanPrevVal
                if i_line_asm == 'main:':
                    self.new_asm_file.insert(i_line_num_new_asm_file+1, '\tli\ts11,' + str(self.random_sig[i_block] + self.subRanPrevVal[i_block]))
                    i_line_num_new_asm_file += 1

                # This is the first update and signature check of the block
                i_line_num_new_asm_file += 1
                inst_sub = '\taddi\ts11,s11,-' + str(self.subRanPrevVal[i_block])
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_sub)
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(self.random_sig[i_block]))
                i_line_num_new_asm_file += 1
                inst_branch_exception_handler = '\tbne\ts11,s10,' + utils.exception_handler_address
                self.new_asm_file.insert(i_line_num_new_asm_file, inst_branch_exception_handler)
                del inst_sub, inst_branch_exception_handler

                # Next we need to update the signature at the end of the block, therefore
                # get to the last instruction in the block
                for i in range(len(self.original_map.blocks[i_block].entries)):
                    i_line_num_new_asm_file += 1

                # Here we can have several different cases, each of which requires a different implementation
                # Case 0: Check if it is the final block in the CFG, in which case we have to use the returnVal
                if len(self.original_map.blocks[i_block].next_block_id) == 0:
                    returnVal = random.sample(range(1, len(self.original_map.blocks) * 20), 1)[0]
                    returnVal = random.sample(range(1, len(self.original_map.blocks) * 20), 1)[0]
                    i_adjustedValue = self.random_sig[i_block] - returnVal
                    if i_adjustedValue > 0:
                        i_adjustedValue = i_adjustedValue * -1
                    else:
                        i_adjustedValue = abs(i_adjustedValue)
                    inst_2nd_sig_update = '\taddi\ts11,s11,' + str(i_adjustedValue)
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_2nd_sig_update)
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(returnVal))
                    i_line_num_new_asm_file += 1
                    inst_branch_exception_handler = '\tbne\ts11,s10,' + utils.exception_handler_address
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_branch_exception_handler)
                    del i_adjustedValue, inst_2nd_sig_update, returnVal

                # Case 1: Check if the instruction is conditional branch instruction
                elif utils.is_conditional_branch_instruction(self.new_asm_file[i_line_num_new_asm_file].split('\t', 1)[-1]):
                    line = self.new_asm_file[i_line_num_new_asm_file]
                    i_instruction = line.split('\t')[1]
                    i_target_address = line.split(',')[-1]
                    i_operand_2 = line.split(',')[-2]
                    i_operand_1 = (line.split(',')[-3]).split('\t')[-1]
                    if i_instruction == 'bne':
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tbeq\t' + i_operand_1 + "," + i_operand_2 + ",.RASM" + str(i_block))
                    elif i_instruction == 'beq':
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tbne\t' + i_operand_1 + "," + i_operand_2 + ",.RASM" + str(i_block))
                    elif i_instruction == 'ble':
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tbgt\t' + i_operand_1 + "," + i_operand_2 + ",.RASM" + str(i_block))
                    elif i_instruction == 'blt':
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tbge\t' + i_operand_1 + "," + i_operand_2 + ",.RASM" + str(i_block))
                    elif i_instruction == 'bge':
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tblt\t' + i_operand_1 + "," + i_operand_2 + ",.RASM" + str(i_block))
                    elif i_instruction == 'bgt':
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tble\t' + i_operand_1 + "," + i_operand_2 + ",.RASM" + str(i_block))
                    else:
                        self.simlog.error("Unable to recognize the branch instruction: " + i_instruction)
                        raise Exception

                    # Find the block of the jump target. To get that we need to find the matching objdump line of
                    # the asm line, and extract the address that to jump to. Once we have the address, we can locate
                    # the block ID.
                    #l_jump_address = utils.get_matching_objdump_line_using_asm_line(self.instruction_map, self.new_asm_file[i_line_num_new_asm_file+1].split('\t', 1)[-1])[0]
                    #l_jump_address = (l_jump_address.split(',')[-1]).split(' ')[0]

                    i_line_num_new_asm_file += 1
                    next_blocks = self.original_map.blocks[i_block].next_block_id
                    next_block_id = self.original_map.blocks[i_block].next_block_id[0]
                    #l_adjusted_value = self.random_sig[i_block] - (self.random_sig[next_block_id] + self.subRanPrevVal[next_block_id])
                    l_adjusted_value = self.calculate_adjusted_value(self.random_sig[i_block],
                                                                self.random_sig[next_block_id],
                                                                self.subRanPrevVal[next_block_id])
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str(l_adjusted_value))
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tj\t' + i_target_address)
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '.RASM' + str(i_block) + ':')
                    i_line_num_new_asm_file += 1
                    next_block_id = self.original_map.blocks[i_block].next_block_id[1]
                    l_adjusted_value = self.calculate_adjusted_value(self.random_sig[i_block],
                                                                self.random_sig[next_block_id],
                                                                self.subRanPrevVal[next_block_id])
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str(l_adjusted_value))
                    i_line_num_new_asm_file += 1

                    # Remove the old branch instruction as it is now replaced with new implementation
                    line = self.new_asm_file[i_line_num_new_asm_file]
                    self.new_asm_file[i_line_num_new_asm_file] += "   #Deleteme"
                    line = self.new_asm_file[i_line_num_new_asm_file]
                    i_line_num_new_asm_file -= 1


                # Case 2: Check if the instruction is unconditional branch instruction or load/store or arithmetic
                else:
                    # If it is a load/store or arithmetic instruction then place the "SUB" sigupdate after the last
                    # instruction, otherwise if it is an unconditional branch instruction then place it before the
                    # branch instruction
                    if not utils.is_unconditional_branch_instruction(self.new_asm_file[i_line_num_new_asm_file].split('\t', 1)[-1]):
                        i_line_num_new_asm_file += 1

                    next_block_id = self.original_map.blocks[i_block].next_block_id
                    # There must be only one next block for any load/store. or arithmetic, or unconditional branch
                    # instruction, except "jr ra" which can return to several calling functions.
                    if len(next_block_id) > 1:
                        i_inst = self.new_asm_file[i_line_num_new_asm_file].split('\t')[1]
                        i_operand = self.new_asm_file[i_line_num_new_asm_file].split('\t')[-1]
                        if i_inst != 'jr':
                            self.simlog.error("We have more than 1 successor block for block_id=" + i_block)
                            raise Exception
                        elif i_operand != 'ra':
                            self.simlog.error("We are returning to address stored in register that is not ra")
                            raise Exception
                        elif len(next_block_id) == 2:
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + self.original_map.blocks[next_block_id[0]].memory[0])
                            i_line_num_new_asm_file += 1
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tbeq\ts10,ra,RASM_multiple_return_ra' + str(i_block))
                            i_line_num_new_asm_file += 1
                            i_adjustedValue = calculate_adjusted_value(self.random_sig[i_block],
                                                                       self.random_sig[next_block_id[1]],
                                                                       self.subRanPrevVal[next_block_id[1]])
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str(i_adjustedValue))
                            i_line_num_new_asm_file += 1
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tjr\tra')
                            i_line_num_new_asm_file += 1

                            self.new_asm_file.insert(i_line_num_new_asm_file, 'RASM_multiple_return_ra' + str(i_block) + ":")
                            i_line_num_new_asm_file += 1
                            i_adjustedValue = calculate_adjusted_value(self.random_sig[i_block],
                                                                       self.random_sig[next_block_id[0]],
                                                                       self.subRanPrevVal[next_block_id[0]])
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str(i_adjustedValue))
                            i_line_num_new_asm_file += 1
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tjr\tra')

                        else:
                            self.simlog.error("We have more than 2 successor block for block_id=" + str(i_block))
                            raise Exception

                    # We only have 1 next block to consider
                    else:
                        next_block_id = next_block_id[0]
                        i_adjustedValue = self.random_sig[i_block] - (self.random_sig[next_block_id] + self.subRanPrevVal[next_block_id])
                        if i_adjustedValue > 0:
                            i_adjustedValue = i_adjustedValue * -1
                        else:
                            i_adjustedValue = abs(i_adjustedValue)
                        inst_2nd_sig_update = '\taddi\ts11,s11,' + str(i_adjustedValue)
                        self.new_asm_file.insert(i_line_num_new_asm_file, inst_2nd_sig_update)
                        del i_adjustedValue, next_block_id, inst_2nd_sig_update

                        # Now skip the uncondtional branch instruction to move to the next block
                        if utils.is_unconditional_branch_instruction(self.new_asm_file[i_line_num_new_asm_file].split('\t', 1)[-1]):
                            i_line_num_new_asm_file += 1

                i_block += 1
            i_line_num_new_asm_file += 1

        if i_block != len(self.original_map.blocks):
            self.simlog.error('Failed to process all blocks. Currently at block id # ' + str(i_block))
            raise Exception

    def calculate_adjusted_value(self, randomNumberBB, randomNumberSuccess, subRanPreValSuccess):
        i_adjustedValue = randomNumberBB - (randomNumberSuccess + subRanPreValSuccess)
        if i_adjustedValue > 0:
            i_adjustedValue = i_adjustedValue * -1
        else:
            i_adjustedValue = abs(i_adjustedValue)
        return i_adjustedValue

    def process_RASM_blocks(self):
        # Generate a random unique number for each basic block
        random.seed(a=1, version=2)
        while len(self.random_sig) != len(self.original_map.blocks):
            i_val = random.sample(range(1, len(self.original_map.blocks) * 10), 1)[0]
            if i_val not in self.random_sig:
                self.random_sig.append(i_val)

        # Now generate a random subtract value for each block
        while len(self.subRanPrevVal) != len(self.original_map.blocks):
            i_val = random.sample(range(1, len(self.original_map.blocks) * 20), 1)[0]
            if i_val not in self.subRanPrevVal:
                self.subRanPrevVal.append(i_val)

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

    def generate_instruction_mapping(self):
        finish_function = False
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
                j += 1
                while True:

                    try:
                        i_line = self.original_map.file_asm[j]
                    except Exception as e:
                        # print('Reached end of file')
                        break
                    if self.is_instruction_asm(i_line):
                        instruction_map_asm.append(i_line.split('\t', 1)[1])
                    j += 1
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

        # The .s file might have more instruction than the obj file.
        if len(instruction_map_asm) != len(instruction_map_obj):
            i_inst = 0
            while i_inst != len(instruction_map_obj):
                # Once we get the same lengths for both list then return
                if len(instruction_map_obj) == len(instruction_map_asm):
                    break
                i_inst_asm = instruction_map_asm[i_inst].split('\t')[0]
                i_inst_obj = instruction_map_obj[i_inst].split('\t')[0]
                if i_inst_asm == i_inst_obj:
                    i_inst += 1
                elif (i_inst_obj in i_inst_asm) or (i_inst_asm in i_inst_obj):
                    # It is possible that:
                    # ble be used as blez or
                    # beq be used as beqz
                    i_inst += 1
                else:
                    # It is possible that lw be expanded to two instructions lui and lw
                    # It is possible that sw be expanded to two instructions lui and sw
                    i_next_asm = instruction_map_asm[i_inst + 1].split('\t')[0]
                    if i_next_asm == i_inst_obj:
                        instruction_map_asm[i_inst] = instruction_map_asm[i_inst] + ";" + instruction_map_asm[
                            i_inst + 1]
                        del instruction_map_asm[i_inst + 1]
                        i_inst += 1
                    else:
                        # It is possible that "jal" be called as "call" instruction
                        i_inst += 1

        # Form a 2-dimensional array with instructions from both .s and .obj file
        if len(instruction_map_asm) != len(instruction_map_obj):
            self.simlog.error('Number of instructions is not the same in both .s and .obj file')
            raise Exception
        self.instruction_map = [instruction_map_asm, instruction_map_obj]
