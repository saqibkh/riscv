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

def checkFileExists(i_filename):
    if not utils.checkFileExists(i_filename):
        print("file: " + i_filename + " doesn't exist.")
        raise Exception

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

def split(word):
    return [char for char in word]

class Instruction_Map:
    def __init__(self, i_file):

        self.file = i_file
        self.log = readfile(i_file)
        self.map = []
        self.opcode = []
        self.address = []
        self.instruction = []
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

                # All addresses are 64-bits, so zero fill the address to occupy 64-bits
                i_address_binary = split((bin(int(i_address, 16)).split('0b')[-1]).zfill(64))
                i_address_binary = [int(j) for j in i_address_binary]
                self.address.append(i_address_binary)

                # All opcodes occupy 32-bits, so zero fill the address to occupy 8bytes or 32-bits
                i_opcode_binary = split((bin(int(i_opcode, 16)).split('0b')[-1]).zfill(32))
                i_opcode_binary = [int(j) for j in i_opcode_binary]
                self.opcode.append(i_opcode_binary)

                # Append the instruction
                self.instruction.append(i_instruction)

                i_object = [i_address, i_opcode, i_instruction]
                for j in range(len(i_instruction_components)):
                    i_object.append(i_instruction_components[j])
                self.map.append(i_object)

