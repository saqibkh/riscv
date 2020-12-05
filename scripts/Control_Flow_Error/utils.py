#!/usr/bin/python


import logging
import time
import string
import datetime
import random
import subprocess
import re
from os import path

#
branch_unconditional_instructions = ['b', 'j', 'jr', 'jal', 'ret', 'call']
branch_conditional_instructions = ['bne', 'beq', 'blt', 'bge', 'bnez', 'ble', 'bltz', 'bgtz']

# This address is where the program execution will jmp to in case the software signatures don't match
exception_handler_address = '100'  # --> 0x64

# This address is where the program execution will jmp to in case the software signatures don't match
exception_handler_address = '100'

''' Commonly used functions will be defined here'''


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


def checkFileExists(filename):
    ##
    # Description: Check if the given file exists in the directory
    #
    # Input: filename (String)
    # Output: boolean
    return path.exists(filename)


def is_branch_instruction(i_line):
    # Definition: This function checks if the instruction defined in i_line is a branch instruction of not
    # Example: 'jal\tra,10150 <countSetBits>'
    inst = i_line.split('\t')[0]
    if (inst in branch_conditional_instructions) or (inst in branch_unconditional_instructions):
        return True
    else:
        return False


def get_instruction(i_line):
    # Definition: This function extracts the instruction from a string line
    #             Example:
    line = i_line.split('\t')[0]
    return line


def get_jump_address(i_line):
    # Definition: Gets the target address where the jump/branch instruction might end up
    #             i_line must hold a jump/branch instruction otherwise we return None
    #             Example: 'jal\tra,10150 <countSetBits>'

    # If instruction is 'ret' then return None as we need to check RA (Return Address) Register
    # If instruction is not a branch/jump instruction then it is either load/store of arithmetic operation, both of
    # which doesn't return anything
    if (not is_branch_instruction(i_line)) or (i_line == 'ret'):
        return

    i_inst, i_data = i_line.split('\t')
    if i_inst in branch_unconditional_instructions:
        if (i_inst == 'jal'):  # jal     ra,1031c <printf>
            return (i_data.split(',')[1]).split(' ')[0]
        else:
            return i_data.split(' ')[0]
    elif i_inst in branch_conditional_instructions:
        # Example 'blt a5,a4,1019e <bubbleSort+0x18>'
        return (i_data.split(' ')[0]).split(',')[-1]
    else:
        print('branch instruction not recognized ' + i_inst)
        raise Exception


def generate_instruction_mapping(self):
    # Definition: This creates a 1-1 mapping between instructions in .s file and .objdump file
    instruction_map_asm = []
    instruction_map_obj = []

    # Process the instructions in .s file first
    for i in range(len(self.original_map.functions.f_names)):
        f_name = self.original_map.functions.f_names[i]
        for j in range(len(self.original_map.file_asm)):
            i_line = self.original_map.file_asm[j]
            if not i_line.startswith(f_name):
                continue
            # Found the start of the function definition in .s file
            j += 1
            while True:

                try:
                    i_line = self.original_map.file_asm[j]
                except Exception as e:
                    # print('Reached end of file')
                    break
                if is_instruction_asm(i_line):
                    instruction_map_asm.append(i_line.split('\t', 1)[1])
                j += 1
                # Check when a new function begins so we can exit this loop
                if not (i_line.startswith('.') or i_line.startswith('\t')):
                    finish_function = True
                    break
            if finish_function:
                finish_function = False
                break

    # Now Process the instructions in .objdump file
    for i in range(len(self.original_map.functions.f_names)):
        for j in range(len(self.original_map.functions.f_instructions[i].instruction)):
            instruction_map_obj.append(self.original_map.functions.f_instructions[i].instruction[j])

    # Form a 2-dimensional array with instructions from both .s and .obj file
    if len(instruction_map_asm) != len(instruction_map_obj):
        print('Number of instructions is not the same in both .s and .obj file')
        raise Exception
    self.instruction_map = [instruction_map_asm, instruction_map_obj]


def get_matching_asm_line_using_objdump_line(i_instruction_map, i_line):
    # Definition: Checks for a matching line in the objdump file and returns the
    #             corresponding asm line
    line_instruction_map = 0
    list_matching_objects = []

    while line_instruction_map < len(i_instruction_map[0]):
        if i_line == i_instruction_map[1][line_instruction_map]:
            i_asm_instruction = i_instruction_map[0][line_instruction_map]
            list_matching_objects.append(i_asm_instruction)
        line_instruction_map += 1
    return list_matching_objects


def is_instruction_asm(i_line):
    # Definition: checks if the provided line is a valid instruction in the asm file
    if not i_line.startswith('\t'):
        return False
    i_line = i_line.strip('\t')
    if i_line.startswith('.'):
        return False
    return True

''' End of commonly defined functions'''

''' Start of class definitions'''


class Block:
    # Definition: This class defines a Control Flow Block
    def __init__(self, i_func_name, i_id):
        # func_name --> The name of the function this block belongs to in the objdump file
        self.func_name = i_func_name
        # This is the block ID and each block must have a different ID
        self.id = i_id

        # Each block has at least one in-coming and at least one out-going block
        # In-coming block is the one that calls this block
        # Out-going block is the one that this block calls up
        self.previous_block_id = []
        self.previous_block_address = []
        self.next_block_id = []
        self.next_block_address = []

        # entries define all the instructions within this particular block
        self.entries = []

        # memory defines the memory location where each instruction in the memory will be stored
        # The address is defined in hex, but in format "10840" instead of "0x10840"
        self.memory = []

        # opcode defines the instruction. It could be 8-bits, 16-bits or 32-bits
        self.opcode = []


class Instructions:
    # Definition: This is an slower level of function class that holds the list of all instructions/memory/opcode
    #             within each function
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
    # Description: This function extracts the functions defined in the assembly (.s)
    #              and objdump files.
    #              This is a higher level of function class that holds inputs/outputs to a function, calling function,
    #              instructions within each function etc
    def __init__(self):
        # List of all the function names
        self.f_names = []

        # All instructions within each function
        self.f_instructions = []

        #
        self.f_outputs = []
        self.f_inputs = []

        # Name of the function which calls this function
        self.f_calling_func = [[]]

        # The starting address of this function
        self.f_address = []

        # The return addresses of the calling function
        self.f_ret_address = []


class ControlFlowMapRevised:
    ##
    # Description: initializes the ControlFlowMap class and
    #              processes the CFG blocks
    #
    # Inputs: f_asm and f_obj objects
    def __init__(self, i_asm, i_obj):
        self.file_asm = i_asm
        self.file_obj = i_obj
        self.blocks = []
        self.functions = Functions()

        ''' Here we begin processing the asm and obj file to extract the functions and subsequently the
            control flow graphs'''

        # 1 Get all the function names from asm file so that we
        #
        self.extract_function_names()

        ##
        # 2. Get all the instructions that corresponds to a particular function
        #    from within the objdump file
        for i in range(len(self.functions.f_names)):
            self.get_function_data_objdump(i)

        ##
        # 3. Process the blocks within each function
        for i in range(len(self.functions.f_names)):
            self.generate_blocks(i)

        ##
        # 4. Process the blocks within each block
        for i in range(len(self.functions.f_names)):
            self.generate_extended_blocks()
        # Fix the IDs of each block as we might have inserted new blocks
        for i in range(len(self.blocks)):
            self.blocks[i].id = i

        ##
        # 5. Get outputs to each block also called the next block
        self.get_calling_functions()
        self.get_output_paths()
        # Also process the next_block_id
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].next_block_address)):
                self.blocks[i].next_block_id.append(
                    self.find_block_id_with_address(self.blocks[i].next_block_address[j]))

        ##
        # 6. Get inputs for each block also called the previous block
        self.get_input_paths()

        #print("Successfully created the Control Flow Graph")
        #'''                                                                     '''
        #'''               END OF CONTROL FLOW GRAPH PROCESSING                  '''
        #'''                                                                     '''

    def is_defined_address(self, i_address):
        # Definition: Checks all the function instructions to see if the address provided is defined within
        for i in range(len(self.functions.f_instructions)):
            for j in range(len(self.functions.f_instructions[i].address)):
                if i_address == self.functions.f_instructions[i].address[j]:
                    return True
        return False

    def find_address_with_block_id(self, i_block_id):
        # Definition: This function finds the starting address of this particular block ID (Example: 5)
        return self.blocks[i_block_id].memory[0]

    def find_block_id_with_address(self, i_address):
        # Definition: This function finds the block ID that holds this particular address (Example: 10180)
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].memory)):
                line = self.blocks[i].memory[j]
                if i_address == self.blocks[i].memory[j]:
                    deleteme = self.blocks[i].id
                    return self.blocks[i].id
        return None

    def get_input_paths(self):
        # Definition:
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].next_block_address)):
                i_block_id = self.find_block_id_with_address(self.blocks[i].next_block_address[j])
                if i_block_id != None:
                    self.blocks[i_block_id].previous_block_id.append(i)
                    self.blocks[i_block_id].previous_block_address.append(self.find_address_with_block_id(i))

    def get_calling_function_address_for_ret(self, i_func):
        # Definition: Check the objdump file and extract lines that calls upon this particular function
        i_func_address_list = []

        for i in range(len(self.functions.f_instructions)):
            # Skip the function if same as i_func
            if self.functions.f_instructions[i].name != i_func:
                for j in range(len(self.functions.f_instructions[i].instruction)):
                    i_line = self.functions.f_instructions[i].instruction[j]
                    if i_func in i_line:
                        i_return_address = hex(int(self.functions.f_instructions[i].address[j], 16) + int(
                            len(self.functions.f_instructions[i].opcode[j]) / 2))
                        i_func_address_list.append(i_return_address.split('0x')[1])
        return i_func_address_list

    def get_output_paths(self):
        for i in range(len(self.blocks)):
            i_line = self.blocks[i].entries[-1]  # Example: "j 0x12456"
            i_inst = get_instruction(i_line)  # Example'j'

            # Instruction could be of following types
            # 1) unconditional --> only 1 return address in the last instruction
            # 2) conditional --> 1 return address in last instruction  & 1 return address is last_instruction + opcode
            # 3) not a branch instruction --> 1 return address is last_instruction + last_opcode
            if i_inst in branch_unconditional_instructions:

                # Need to return to the calling function.
                # Check the objdump file and extract all instances/lines that calls this particular function
                if i_inst == 'ret':
                    i_call_funcs_addr = self.get_calling_function_address_for_ret(self.blocks[i].func_name)
                    # Add return address to output path
                    for j in range(len(i_call_funcs_addr)):
                        self.blocks[i].next_block_address.append(i_call_funcs_addr[j])
                    continue

                return_addr = get_jump_address(i_line)

                # Check if the function being called is defined or not.
                if self.is_defined_address(return_addr):
                    self.blocks[i].next_block_address.append(return_addr)
                else:
                    return_addr = \
                        (hex(int(self.blocks[i].memory[-1], 16) + int(len(self.blocks[i].opcode[-1]) / 2))).split('0x')[
                            1]
                    self.blocks[i].next_block_address.append(return_addr)

            elif i_inst in branch_conditional_instructions:
                return_addr = get_jump_address(i_line)
                if self.is_defined_address(return_addr):
                    self.blocks[i].next_block_address.append(return_addr)

                return_addr = \
                    (hex(int(self.blocks[i].memory[-1], 16) + int(len(self.blocks[i].opcode[-1]) / 2))).split('0x')[1]
                if self.is_defined_address(return_addr):
                    self.blocks[i].next_block_address.append(return_addr)

            else:
                return_addr = hex(int(self.blocks[i].memory[-1], 16) + int(len(self.blocks[i].opcode[-1]) / 2))
                return_addr = return_addr.split('0x')[1]
                if self.is_defined_address(return_addr):
                    self.blocks[i].next_block_address.append(return_addr)

    def is_valid_calling_function(self, i_func):
        # Check if the function given by i_func is a valid function that exists
        # under self.functions.f_names
        # Input: i_func --> Example 'countSetBits'
        for i in range(len(self.functions.f_names)):
            if i_func == self.functions.f_names[i]:
                return True
        return False

    def get_calling_functions(self):
        # We need to create a list with equal number of elements as the function_names
        while len(self.functions.f_names) != len(self.functions.f_calling_func):
            self.functions.f_calling_func.append([])

        # Fills the self.functions.f_calling_func list with the function
        #  names that the host function calls upon (Example <main> calls <subroutine>)
        for i in range(len(self.functions.f_names)):
            for j in range(len(self.functions.f_instructions[i].instruction)):
                line = self.functions.f_instructions[i].instruction[j]
                # line = 'j	10180 <countSetBits+0x30>'
                if re.search('<.+>', line):
                    calling_func = (((line.split('<')[1]).split('>')[0]).split('+')[0])
                    self.functions.f_calling_func[i].append(calling_func)

        # Clear all function names from the calling function that calls itself
        # Also clear all function that are not user defined (i.e. skip external functions)
        for i in range(len(self.functions.f_names)):
            f_name = self.functions.f_names[i]

            j = 0
            while j != len(self.functions.f_calling_func[i]):
                if f_name == self.functions.f_calling_func[i][j]:
                    del self.functions.f_calling_func[i][j]
                elif not self.is_valid_calling_function(self.functions.f_calling_func[i][j]):
                    del self.functions.f_calling_func[i][j]
                else:
                    j += 1

    def generate_extended_blocks(self):
        # Definition: This function further generates block by breaking down
        #             existing blocks because there might be a jump instruction that lands in the middle
        #             of the block (i.e. final instruction in the block will not be a branch/jump instruction)
        for i in range(len(self.blocks)):
            # Get the last instruction from each block to make sure it doesn't
            # branch to the middle of a block
            jmp_addr = get_jump_address(self.blocks[i].entries[-1])

            if jmp_addr is None:
                continue

            create_new_block = True
            # Find the jmp_addr within each block
            for j in range(len(self.blocks)):
                for k in range(len(self.blocks[j].memory)):

                    line = self.blocks[j].memory[k]
                    # Found the memory address within the block
                    if self.blocks[j].memory[k] == jmp_addr:

                        # First entry is the jump address (ALL GOOD!)
                        if k == 0:
                            break
                        # Break the block
                        else:
                            block = Block(self.blocks[j].func_name, j + 1)

                            while len(self.blocks[j].memory) != k:
                                block.opcode.append(self.blocks[j].opcode[k])
                                block.memory.append(self.blocks[j].memory[k])
                                block.entries.append(self.blocks[j].entries[k])
                                del self.blocks[j].opcode[k]
                                del self.blocks[j].memory[k]
                                del self.blocks[j].entries[k]

                            # Add the block back into the Control Flow Graph
                            self.blocks.insert(j + 1, block)
                            break

    def generate_blocks(self, item):
        # Description: Process the instructions defined within each function call
        #              and breaks them down in to different blocks using branch instructions
        #              as delimiters to form the Control Flow Graph
        i_ins_list = self.functions.f_instructions[item]

        block = Block(self.functions.f_names[item], len(self.blocks))
        for i in range(len(i_ins_list.instruction)):
            line = i_ins_list.instruction[i]

            # Append entries to the block
            block.entries.append(i_ins_list.instruction[i])
            block.opcode.append(i_ins_list.opcode[i])
            block.memory.append(i_ins_list.address[i])

            # If a branch instruction is found then finish this
            # block and start a new block
            if is_branch_instruction(line):
                self.blocks.append(block)
                block = Block(self.functions.f_names[item], len(self.blocks))

    def get_function_data_objdump(self, item):
        ##
        # Description: Gets all the instructions that are defined within a function call
        #              and fills the self.function_instructions
        function = Instructions(self.functions.f_names[item])
        for j in range(len(self.file_obj)):
            if not self.file_obj[j].startswith('   '):
                if function.name in self.file_obj[j]:
                    self.functions.f_address.append(self.file_obj[j + 1].strip().split(':')[0])
                    # Keep adding lines to the function until a new function starts
                    j += 1
                    while 1:
                        # line = self.f_obj[j]
                        if not self.file_obj[j].startswith('   '):
                            self.functions.f_instructions.append(function)
                            return

                        address, opcode, instruction = self.file_obj[j].split('\t', 2)
                        address = address.strip()[:-1]
                        opcode = opcode.strip()
                        function.addEntry(address, opcode, instruction)
                        j += 1

    def extract_function_names(self):
        ##
        # Description: Gets the function names from within the assembly file
        #
        # Create a copy of self.f_asm
        i_asm = self.file_asm
        for i in range(len(i_asm)):
            if (i_asm[i].startswith('\t')):
                continue
            elif (i_asm[i].startswith('.')):
                continue
            else:
                self.functions.f_names.append(i_asm[i].strip()[:-1])
        del i_asm


''' End of class definitions'''
