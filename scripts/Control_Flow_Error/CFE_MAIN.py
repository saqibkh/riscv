##############################################################################
#
# This file will be used to auto-generate the modified assembly files
# for Control Flow Error Detection techniques, which includes
# 1) Control Flow Checking by Software Signature (CFCSS)
#
##############################################################################

#!/usr/bin/python

import sys
import logging
import time
import string
import datetime
import random
import subprocess

from os import path

##
# Description: This method will hold the entire Control Flow Graph (CFG)
#               including the blocks, all incoming and outgoing threads

class Blocks:
    def __init__(self, i_name):
        self.func_name = i_name
        self.entries = []
        self.memory = []
        self.opcode = []

    def addEntry(self, entry):
        self.entries.append(entry)


class ControlFlowMap:

    ##
    # Description: initializes the ControlFlowMap class and
    #              processes the CFG blocks
    #
    # Inputs: f_asm and f_obj objects
    def __init__(self, i_asm, i_obj):
        self.f_asm = i_asm
        self.f_obj = i_obj
        self.blocks = []
        self.inputs = []
        self.outputs = []
        self.process_ASM()
        self.process_OBJ()

    def process_ASM(self):
        processing_block = False
        block = None

        # Remove all the lines in asm file that starts with "\t."
        ent = 0
        while ent < len(self.f_asm):
            if self.f_asm[ent].startswith('\t.'):
                del self.f_asm[ent]
            else:
                break


        for i in range(len(self.f_asm)):
            line = self.f_asm[i] # Remove after debugging this function call

            if(processing_block == False):
                function_name = self.f_asm[i][:-1]
                block = Blocks(function_name)
                processing_block = True

            else: # processing_block == True
                block.addEntry(self.f_asm[i])

                try:
                    if not self.f_asm[i+1].startswith('\t'):
                        self.blocks.append(block)
                        processing_block = False
                        block = None
                except:
                    self.blocks.append(block)
                    return


    def process_OBJ(self):

        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].entries)):
                line_asm = self.blocks[i].entries[j]

                self.blocks[i].memory.append(None)
                self.blocks[i].opcode.append(None)

                for k in range(len(self.f_obj)):
                    line_obj = self.f_obj[k]
                    if line_asm in line_obj:
                        address, opcode, instruction = line_obj.split('\t', 2)
                        address = address.strip()[:-1]
                        opcode = opcode.strip()
                        self.blocks[i].memory[j] = address
                        self.blocks[i].opcode[j] = opcode
                        break;


def usage():
    print("Usage: Please provide a test that has corresponding file names that matches <file>.s <file>.objdump")
    print("Example ./TMMain.py bit_count    (Must have bit_count.s and bit_count.objdump files in the folder)")

def main(argv):
    if len(sys.argv) == 1:
        usage()
        sys.exit()

    # Check if all the assembly and objdump files exist
    file = argv[0] + ".s"
    if(checkFileExists(file) == False):
        return 1
    f_asm = readfile(file)
    file = argv[0] + ".objdump"
    if (checkFileExists(file) == False):
        return 1
    f_obj = readfile(file)
    del file


    map = ControlFlowMap(f_asm, f_obj)


    #generate_CFCSS_file(map)


    return 0


def printlog(type, msg):
    if(type == "PROCESS_FILE"):
        print(msg)

##
# Description: Check if the given file exists in the directory
#
# Input: filename (String)
# Output: boolean
def checkFileExists(filename):
    return path.exists(filename)

##
# Description: Return all the contents within a file.
#              --> strips out newline char and spaces
#              --> removes unnecessary contents within the file
#
# Input: filename (String)
# Output: list of strings (each element is a line in the file)
def readfile(filename):
    with open(filename) as f:
        lines = [line.rstrip() for line in f]
    return lines

if __name__ == "__main__":
    main(sys.argv[1:])