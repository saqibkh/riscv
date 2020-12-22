#!/usr/bin/env python

import sys
import logging
import time
import string
import datetime
import getopt
import random
import subprocess
import os

import instructions


def readfile(filename):
    ##
    # Description: Return all the contents within a file.
    #              --> strips out newline char and spaces
    #              --> removes unnecessary contents within the file
    #
    # Input: filename (String)
    # Output: list of strings (each element is a line in the file)
    with open(filename) as f:
        lines = [line.rstrip() for line in f]
    return lines


class Instruction_Map:
    def __init__(self, i_file):

        self.file = i_file
        self.log = readfile(i_file)
        self.map = []
        self.generate_map(self.log)

    def generate_map(self, i_file):
        for i in range(len(i_file)):
            i_line = i_file[i]

            # Make sure this is a instruction log
            if i_line.startswith("core   0: 0x"):
                i_line_components = ((i_line.replace("  ", " ")).replace("  ", " ")).replace("  ", " ").split(" ")

                i_address = i_line_components[2]
                i_opcode = ((i_line_components[3].strip()).replace('(', '')).replace(')', '')

                i_complete_instruction = ((i_line.replace("  ", " ")).replace("  ", " ")).replace("  ", " ").split(" ", 4)[-1]
                i_instruction = i_complete_instruction.split(' ', 1)[0]
                i_instruction_components = (i_complete_instruction.split(' ', 1)[-1]).split(',')


                if i_instruction not in instructions.all_instructions:
                    print("The following instruction is not yet added to the master list of instruction: " + i_instruction)
                    raise Exception

                i_object = [i_address, i_opcode, i_instruction]
                for j in range(len(i_instruction_components)):
                    i_object.append(i_instruction_components[j])
                self.map.append(i_object)

