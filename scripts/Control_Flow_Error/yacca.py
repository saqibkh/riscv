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

        return

    ''' Beginning of class function definitions '''
    def generate_Previous(self):
        for i in range(len(self.original_map.blocks)):
            # Take care of case where there is no incoming block (i.e. Main())
            if len(self.original_map.blocks[i].previous_block_id) == 0:
                self.previous.append(0)

            # Block with only 1 incoming block
            elif len(self.original_map.blocks[i].previous_block_id) == 1:
                self.previous.append(self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]])

            # Block with 2 incoming blocks
            else:
                sig_1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                sig_2 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[1]]
                self.previous.append(sig_1 * sig_2)

    def generate_M1(self):
        for i in range(len(self.original_map.blocks)):
            if len(self.original_map.blocks[i].previous_block_id) == 2:
                sig_1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                sig_2 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[1]]
                M1 = ~(sig_1 ^ sig_2)
                # Flip the sign if M1 is negative
                if(M1 < 0):
                    M1 *= -1
                self.M1[i] = M1

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

            elif len(self.original_map.blocks[i].previous_block_id) == 2:
                # M2 = (B_pred1 AND M1_i) Exclusive OR B_i
                B_pred1 = self.compile_time_sig[self.original_map.blocks[i].previous_block_id[0]]
                M1_i = self.M1[i]
                B_i = self.compile_time_sig[i]
                self.M2[i] = (B_pred1 & M1_i) ^ B_i

    def generate_YACCA_file_updated(self):
        return

    ''' End of class definitions '''
