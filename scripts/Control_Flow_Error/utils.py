#!/usr/bin/python


import logging
import time
import string
import datetime
import random
import subprocess
import re
from os import path


branch_unconditional_instructions = ['b', 'j', 'jal', 'jr', 'ret']
branch_conditional_instructions = ['bne', 'beq', 'blt', 'bge', 'bnez']


##
# Description: This method will hold the entire Control Flow Graph (CFG)
#               including the blocks, all incoming and outgoing threads


class Function:
    def __init__(self, i_name):
        self.name = i_name
        self.address = []
        self.opcode = []
        self.instruction = []

    def addEntry(self, i_address, i_opcode, i_instruction):
        self.address.append(i_address)
        self.opcode.append(i_opcode)
        self.instruction.append(i_instruction)


class Functions:
    def __init__(self):
        self.f_names = []
        self.f_instructions = []
        self.f_outputs = []
        self.f_inputs = []
        self.f_calling_func = [[]]
        self.f_addr = []


class Blocks:
    def __init__(self, i_func_name, i_id):
        self.id = i_id
        self.previous_block_id = []
        self.next_block_addr = []
        self.func_name = i_func_name
        self.entries = []
        self.memory = []
        self.opcode = []

    def addEntry(self, entry):
        self.entries.append(entry)


'''
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
            line = self.f_asm[i]  # Remove after debugging this function call

            if not processing_block:
                function_name = self.f_asm[i][:-1]
                block = Blocks(function_name, len(self.blocks))
                processing_block = True

            else:  # processing_block == True
                block.addEntry(self.f_asm[i])

                try:
                    if not self.f_asm[i + 1].startswith('\t'):
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
                        break
'''


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


class ControlFlowMapRevised:

    ##
    # Description: initializes the ControlFlowMap class and
    #              processes the CFG blocks
    #
    # Inputs: f_asm and f_obj objects
    def __init__(self, i_asm, i_obj):
        self.f_asm = i_asm
        self.f_obj = i_obj
        self.blocks = []
        self.functions = Functions()

        ##
        # 1. Get all the function names from asm file so that we
        #    can search for them in the objdump file
        self.get_function_names()

        ##
        # 2. Get all the instructions that corresponds to a particular function
        #    from within the objdump file
        for i in range(len(self.functions.f_names)):
            self.get_function_data(i)

        ##
        # 3. Process the blocks within each function
        for i in range(len(self.functions.f_names)):
            self.generate_blocks(i)

        ##
        # 4. Process the blocks within each block
        for i in range(len(self.functions.f_names)):
            self.generate_extended_blocks()

        ##
        # 5. Get outputs to each block
        self.get_calling_functions()
        self.get_output_paths()

        ##
        # 6. Get inputs for each block
        self.get_input_paths()

        print("Done")


    def get_input_paths(self):

        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].next_block_addr)):
                i_block_id = self.find_block_with_addr(self.blocks[i].next_block_addr[j])
                if(i_block_id != None):
                    self.blocks[i].previous_block_id.append(i_block_id)



    def find_block_with_addr(self, i_addr):
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].memory)):
                line = self.blocks[i].memory[j]
                if(i_addr == self.blocks[i].memory[j]):
                    return self.blocks[i].id
        return None

    def get_calling_functions(self):
        # We need to create a list with equal number of elements as the function_names
        while(len(self.functions.f_names) != len(self.functions.f_calling_func)):
            self.functions.f_calling_func.append([])

        # Fills the self.functions.f_calling_func list with the function
        #  names that the host function calls upon (Example <main> calls <subroutine>)
        for i in range(len(self.functions.f_names)):
            for j in range(len(self.functions.f_instructions[i].instruction)):
                line = self.functions.f_instructions[i].instruction[j]
                #line = 'j	10180 <countSetBits+0x30>'
                if re.search('<.+>', line):
                    calling_func = (((line.split('<')[1]).split('>')[0]).split('+')[0])
                    self.functions.f_calling_func[i].append(calling_func)

        # Clear all function names from the calling function that calls itself
        # Also clear all function that are not user defined (i.e. skip external functions)
        for i in range(len(self.functions.f_names)):
            f_name = self.functions.f_names[i]

            j = 0
            while(j != len(self.functions.f_calling_func[i])):
                if(f_name == self.functions.f_calling_func[i][j]):
                    del self.functions.f_calling_func[i][j]
                elif not self.is_valid_calling_function(self.functions.f_calling_func[i][j]):
                    del self.functions.f_calling_func[i][j]
                else:
                    j+=1


    def is_valid_calling_function(self, i_func):
        # Check if the function given by i_func is a valid function that exists
        # under self.functions.f_names
        for i in range(len(self.functions.f_names)):
            if(i_func == self.functions.f_names[i]):
                return True
        return False

    def get_output_paths(self):
        for i in range(len(self.blocks)):
            i_line = self.blocks[i].entries[-1]  # Example: "j 0x12456"
            i_inst = self.get_instruction(i_line)  # Example'j'

            # Instruction could be of following types
            # 1) unconditional --> only 1 return address in the last instruction
            # 2) conditional --> 1 return address in last instruction  & 1 return address is last_instruction + opcode
            # 3) not a branch instruction --> 1 return address is last_instruction + last_opcode
            if i_inst in branch_unconditional_instructions:
                # Need to return to the calling function
                if (i_inst == 'ret'):
                    i_call_funcs_addr = self.get_calling_function_addr_for_ret(self.blocks[i].func_name)
                    # Add return address to output path
                    for j in range(len(i_call_funcs_addr)):
                        self.blocks[i].next_block_addr.append(i_call_funcs_addr[j])
                    continue

                return_addr = self.get_jump_address(i_line)
                self.blocks[i].next_block_addr.append(return_addr)

            elif i_inst in branch_conditional_instructions:
                return_addr = self.get_jump_address(i_line)
                self.blocks[i].next_block_addr.append(return_addr)
                return_addr = hex(int(self.blocks[i].memory[-1], 16) + int(len(self.blocks[i].opcode[-1]) / 2))
                self.blocks[i].next_block_addr.append(return_addr.split('0x')[1])

            else:
                return_addr = hex(int(self.blocks[i].memory[-1], 16) + int(len(self.blocks[i].opcode[-1]) / 2))
                return_addr = return_addr.split('0x')[1]
                self.blocks[i].next_block_addr.append(return_addr)


    def get_calling_function_addr_for_ret(self, i_func):
        # Check to see who can call this particular function and then return a list of functions that could
        # potentially call it.
        i_func_addr_list = []

        for i in range(len(self.functions.f_names)):
            for j in range(len(self.functions.f_calling_func[i])):
                if self.functions.f_calling_func[i][j] == i_func:
                    i_func_addr_list.append(self.functions.f_addr[i])
        return i_func_addr_list

    def get_instruction(self, i_line):
        line = i_line.split('\t')[0]
        return line

    def generate_extended_blocks(self):

        for i in range(len(self.blocks)):
            # Get the last instruction from each block to make sure it doesn't
            # branch to the middle of a block
            jmp_addr = self.get_jump_address(self.blocks[i].entries[-1])

            if (jmp_addr == None):
                continue

            create_new_block = True
            # Find the jmp_addr within each block
            for j in range(len(self.blocks)):
                for k in range(len(self.blocks[j].memory)):

                    line = self.blocks[j].memory[k]
                    # Found the memory address within the block
                    if (self.blocks[j].memory[k] == jmp_addr):

                        # First entry is the jump address (ALL GOOD!)
                        if (k == 0):
                            break
                        # Break the block
                        else:
                            block = Blocks(self.blocks[j].func_name, len(self.blocks))

                            while (len(self.blocks[j].memory) != k):
                                block.opcode.append(self.blocks[j].opcode[k])
                                block.memory.append(self.blocks[j].memory[k])
                                block.entries.append(self.blocks[j].entries[k])
                                del self.blocks[j].opcode[k]
                                del self.blocks[j].memory[k]
                                del self.blocks[j].entries[k]

                            # Add the block back into the Control Flow Graph
                            self.blocks.append(block)
                            break

    def get_jump_address(self, i_line):

        if ((not self.is_branch_instruction(i_line)) or (i_line == 'ret')):
            return

        i_inst, i_data = i_line.split('\t')
        if (i_inst == 'j'):
            return i_data.split(' ')[0]
        elif (i_inst == 'bnez') or (i_inst == 'jal'):
            return (i_data.split(',')[1]).split(' ')[0]
        else:
            print('branch instruction not recognized ' + i_inst)

    def generate_blocks(self, item):
        #################################################################################################
        ##
        # Description: Process the instructions defined within each function call
        #              and breaks them down in to different blocks using branch instructions
        #              to form the Control Flow Graph
        i_ins_list = self.functions.f_instructions[item]

        block = Blocks(self.functions.f_names[item], len(self.blocks))
        for i in range(len(i_ins_list.instruction)):
            line = i_ins_list.instruction[i]

            # Append entries to the block
            block.entries.append(i_ins_list.instruction[i])
            block.opcode.append(i_ins_list.opcode[i])
            block.memory.append(i_ins_list.address[i])

            # If a branch instruction is found then finish this
            # block and start a new block
            if self.is_branch_instruction(line):
                self.blocks.append(block)
                block = Blocks(self.functions.f_names[item], len(self.blocks))

    def is_branch_instruction(self, i_line):
        inst = i_line.split('\t')[0]
        if ((inst in branch_conditional_instructions) or (inst in branch_unconditional_instructions)):
            return True
        else:
            return False

    def get_function_data(self, item):
        ##
        # Description: Gets all the instructions that are defined within a function call
        #              and fills the self.function_instructions
        function = Function(self.functions.f_names[item])
        for j in range(len(self.f_obj)):
            if not self.f_obj[j].startswith('   '):
                if (function.name in self.f_obj[j]):
                    self.functions.f_addr.append(self.f_obj[j+1].strip().split(':')[0])
                    # Keep adding lines to the function until a new function starts
                    j += 1
                    while (1):
                        #line = self.f_obj[j]
                        if not self.f_obj[j].startswith('   '):
                            self.functions.f_instructions.append(function)
                            return

                        address, opcode, instruction = self.f_obj[j].split('\t', 2)
                        address = address.strip()[:-1]
                        opcode = opcode.strip()
                        function.addEntry(address, opcode, instruction)
                        j += 1

    def get_function_names(self):
        ##
        # Description: Gets the function names from within the assembly file
        #

        # Create a copy of self.f_asm
        i_asm = self.f_asm

        for i in range(len(i_asm)):
            if (i_asm[i].startswith('\t')):
                continue
            elif (i_asm[i].startswith('.')):
                continue
            else:
                self.functions.f_names.append(i_asm[i].strip()[:-1])
        del i_asm
