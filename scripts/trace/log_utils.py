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

def check_instructions(i_file):
    for i in range(len(i_file)):
        i_line = i_file[i]

        # Make sure this is a instruction log
        if i_line.startswith("core   0: 0x"):
            i_line = ((i_line.replace("  ", " ")).replace("  ", " ")).split(" ")

            i_address = i_line[2]
            i_opcode = i_line[3].strip()

            i_instruction = i_line[4]
            if i_instruction not in instructions.all_instructions:
                print("The following instruction is not yet added to the master list of instruction: " + i_instruction)
                #raise Exception

    #print("Hello")