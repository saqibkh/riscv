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


# Check whether the input number is a prime number or not
def isPrime(i_num):
    for i in range(2, i_num):
        if i_num % i == 0:
            return False
    return True


# Checks whether i_num exists within the i_list
def isInList(i_list, i_num):
    for i in range(len(i_list)):
        if i_list[i] == i_num:
            return True
    return False


def generate_YACCA_file_updated():
    print("Done")


class ECCA:
    def __init__(self, i_map):
        self.original_map = i_map

        # Compile time signature (BID)
        # BID us a unique compile time signature and has to be a prime number larger than 2
        self.BID = []

        # Compile time signatures of the successor blocks of the current basic block.
        # Note that in case of only 1 successor block the NEXT2 entry will be NONE
        self.NEXT1 = [None] * len(i_map.blocks)
        self.NEXT2 = [None] * len(i_map.blocks)

        random.seed(a=1, version=2)
        self.generate_BID()

        # Now get the compile time signatures of the successor blocks
        self.generateSuccessorSig()

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        utils.generate_instruction_mapping(self)

        # Generate the new assembly file
        self.generate_ECCA_file_updated()

        print("Finished processing ECCA")

    ''' Beginning of class function definitions '''
    def generate_ECCA_file_updated(self):
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
                            if self.original_map.file_asm[i_line_num_new_asm_file].split('\t', 1)[1] == \
                                    i_line_block_asm[i]:
                                block_found = True

                                del i_line_block_obj, i_line_block_asm, i_line_asm
                                break
                    except Exception as e:
                        # unexpected line encountered
                        i_line_num_new_asm_file += 1
                        continue

            if block_found:
                # For initial basic block we need to load BID into v1 and v2
                # s11 holds v1 which is the run-time signature
                # s10 holds v2 which is a helper variable used during two updates of v1
                if len(self.original_map.blocks[i_block].previous_block_id) == 0:
                    inst_mov_initial_v1 = '\tli\ts11,' + str(self.BID[i_block])
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_mov_initial_v1)
                    i_line_num_new_asm_file += 1
                    inst_mov_initial_v2 = '\tli\ts10,' + str(self.BID[i_block])
                    self.new_asm_file.insert(i_line_num_new_asm_file, inst_mov_initial_v2)
                    i_line_num_new_asm_file += 1

                # ECCA adds 4 operations to each basic block to detect CFEs
                # 1. v1 = (v1-BID) x (v2-BID)  - At the start of block
                self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str(self.BID[i_block] * -1))
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts10,s10,' + str(self.BID[i_block] * -1))
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tmul\ts11,s11,s10')
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tbnez\ts11,' + utils.exception_handler_address)
                i_line_num_new_asm_file += 1

                # 2. v1 = (BID+1) / ((v1+1)/(2v1+1)) - At the start of block
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tslli\ts10,s11,1')
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,1')
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts10,s10,1')
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tdivu\ts11,s11,s10')
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(int(self.BID[i_block]) + 1))
                i_line_num_new_asm_file += 1
                self.new_asm_file.insert(i_line_num_new_asm_file, '\tdivu\ts11,s10,s11')
                i_line_num_new_asm_file += 1

                # Get to the last instruction in the block and then add the extended signature
                for i in range(len(self.original_map.blocks[i_block].entries) - 1):
                    i_line_num_new_asm_file += 1

                # If there are no outputs blocks then don't add steps 3 and 4
                if len(self.original_map.blocks[i_block].next_block_id) != 0:
                    # 3. v2= (v1-BID) x NEXT2
                    # 4. v1 = (v1-BID) x NEXT1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str((self.BID[i_block] + 1) * -1))
                    i_line_num_new_asm_file += 1
                    if self.NEXT2[i_block] != None:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts10,s11,' + str(self.NEXT2[i_block]))
                        i_line_num_new_asm_file += 1
                    if self.NEXT1[i_block] != None:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\taddi\ts11,s11,' + str(self.NEXT1[i_block]))
                        i_line_num_new_asm_file += 1

                # Finish processing the block
                i_block += 1

            i_line_num_new_asm_file += 1

    def generateSuccessorSig(self):
        for i in range(len(self.original_map.blocks)):

            next_block_1_id = None
            next_block_2_id = None

            # Not all blocks have successor blocks so wrap it with try/except statements
            try:
                next_block_1_id = self.original_map.blocks[i].next_block_id[0]
            except IndexError as e:
                pass
            try:
                next_block_2_id = self.original_map.blocks[i].next_block_id[1]
            except IndexError as e:
                pass

            if next_block_1_id != None:
                self.NEXT1[i] = self.BID[next_block_1_id]
            if next_block_2_id != None:
                self.NEXT2[i] = self.BID[next_block_2_id]

    def generate_BID(self):
        # loop until we fill the compile time variable list
        while len(self.BID) != len(self.original_map.blocks):
            # Get a random number
            i_num = random.sample(range(3, (len(self.BID) * 4) + 10), 1)[0]
            # Check if it is prime number
            if isPrime(i_num):
                # Check if the number already exists in the list. If not, then add to the list
                if not isInList(self.BID, i_num):
                    self.BID.append(i_num)
