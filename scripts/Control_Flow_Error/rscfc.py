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

    ''' Beginning of class function definitions '''
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
            #2. For all remaining blocks, the bits of the successor blocks are set to 1
            for j in range(len(self.original_map.blocks[i].next_block_id)):
                i_next_block_sig = self.L_i[self.original_map.blocks[i].next_block_id[j]]
                i_current_block_sig = bin(int(i_current_block_sig,2) | int(i_next_block_sig,2))

            # Write the compile_time sig back to the list
            self.compile_time_sig[i] = i_current_block_sig
        print('Here')


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
            cum_sig = '0b'

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

            # Make sure there are more than 1 instructions in the basic block.
            # If there is only one instruction, then there is no need to check for intra-block CFE.
            if len(cum_sig) >= 4:
                self.m_i[i] = cum_sig
            else:
                self.m_i[i] = None



