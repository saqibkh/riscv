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
        self.process_CFCSS_blocks()
        self.generate_CFCSS_file_updated()