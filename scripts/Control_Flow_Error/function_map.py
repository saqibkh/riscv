#!/usr/bin/python

import logging
import time
import string
import datetime
import random
import subprocess
import re
import instructions
import registers
from os import path

''' Start of class definitions'''


class Function:
    def __init__(self, i_name):
        # Name of the function such as main or countSetBits
        self.name = i_name

        # List of functions that are called from within this particular function.
        # For example main calling printf and countSetBits
        self.list_sub_functions = []

        # List of block names that falls within these functions. The block names starts with "." in the asm file, such
        # as .L2, .L3 etc.
        self.list_blocks_names = []


class FunctionMap:
    ##
    # Description: initializes the ControlFlowMap class and
    #              processes the CFG blocks
    #
    # Inputs: f_asm and f_obj objects
    def __init__(self, i_asm):
        self.functions = []

        self.get_functions(i_asm)

    def get_functions(self, i_asm):
        i_found_function = False
        for i in range(len(i_asm)):
            i_line = i_asm[i]
            if i_found_function:
                # This is an original instruction in assembly form. Look for "call" instruction to get sub_functions
                if i_line.startswith('\t'):
                    i_line_components = i_line.split("\t")
                    if "call" in i_line_components:
                        i_func.list_sub_functions.append(i_line_components[-1])
                # This is the block name for a particular function
                elif i_line.startswith('.'):
                    i_func.list_blocks_names.append(i_line.split(":")[0])
                # This is the end of a function
                else:
                    # This is the start of a new function
                    self.functions.append(i_func)
                    i_func = Function(i_line.split(':')[0])
                    i_found_function = True

            else:
                if i_line.startswith('\t') or i_line.startswith('.'):
                    continue
                else:
                    i_func = Function(i_line.split(':')[0])
                    i_found_function = True

        # The append the last function to the self.functions list
        self.functions.append(i_func)


''' End of class definitions'''
