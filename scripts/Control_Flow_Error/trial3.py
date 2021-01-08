import datetime
import random
import subprocess
import utils
import registers
import instructions
import fileinput
from os import path

###################################################################################################################
#
# This is a new type of CFE detection technique where the
# 1) We check that unused register values are not modified @ the end of program
# 2) return address (ra) and stack pointer (sp) are restored back to their value at end of each function
# 3)
#
#
###################################################################################################################

class TRIAL3:
    def __init__(self, i_map):
        self.original_map = i_map

        # Compile time signature
        self.compile_time_sig = []

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        # Generate instruction mapping between .s and .objdump file instructions
        utils.generate_instruction_mapping(self)

        self.registers_used = []
        self.registers_unused = []
        self.registers_modified = []
        self.registers_unmodified = []
        self.registers_different_value_at_end = []
        self.registers_same_value_at_end = []

        # Start processing the registers
        self.process_registers()

        # Generate the new assembly file
        #self.generate_TRIAL3_file_updated()
        print("Finished processing TRIAL3")

    def process_registers(self):

        # Get a list of registers that are used during the program execution
        self.registers_used = utils.registers_used(self.original_map)

        # Get a list of registers that are modified during the program execution
        self.registers_modified = utils.registers_modified(self.original_map)

        # Get a list of registers that are not modified during the program executions.
        # Make sure these registers are not defined within self.registers_modified
        for i in range(len(self.registers_used)):
            if self.registers_used[i] in self.registers_modified:
                pass
            else:
                self.registers_unmodified.append(self.registers_used[i])

        for i in range(len(registers.all_registers)):
            if not registers.all_registers[i] in self.registers_used:
                self.registers_unused.append(registers.all_registers[i])


    def process_blocks(self):
        pass

    def get_signature_based_on_id(self, i_id):
        for i in range(len(self.original_map.blocks)):
            if self.original_map.blocks[i].id == i_id:
                return self.compile_time_sig[i]

    def generate_TRIAL2_file_updated(self):
        i_block = 0
        i_line_num_new_asm_file = 0

        # 1. Loop the asm file lines until the end of file
        while (i_line_num_new_asm_file < len(self.new_asm_file)):

            # Return once all the blocks are processed
            if i_block == len(self.original_map.blocks):
                return

            block_found = False
            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]

            # There are two cases where a basic block can start from
            # 1. When a function beings within the asm file (make sure the first instruction within the function and the block matches one another)
            if not i_line_asm.startswith('\t'):
                # Make sure the first instruction in asm function matches the first instruction in the block
                # Get the first instruction in this particular block for comparison
                i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                # i_line_block_asm could get multiple hits
                i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                for i in range(len(i_line_block_asm)):
                    if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] in i_line_block_asm[i]:
                        block_found = True
                        del i_line_block_obj, i_line_block_asm
                        break

            # 2. When a branch instruction is present within the function itself
            #    and the next instruction is the starting instruction of the next block
            else:  # Line starts with '\t'
                i_line_asm = i_line_asm.split('\t', 1)[1]
                if not i_line_asm.startswith('.'):
                    if utils.is_branch_instruction(i_line_asm):
                        # Get the first instruction in the next block for comparison
                        try:
                            i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                        except:
                            print('done')
                        i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                        try:
                            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1]
                            for i in range(len(i_line_block_asm)):
                                if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] in \
                                        i_line_block_asm[i]:
                                    block_found = True
                                    break
                        except:
                            # unexpected line encountered
                            i_line_num_new_asm_file += 1
                            continue

            if block_found:
                i_line_num_new_asm_file += 1

                # If it is the first block or initial block then just set s10 and s11 to 0.
                # It has no incoming edges
                if len(self.original_map.blocks[i_block].previous_block_id) == 0:
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts11,0')
                    i_line_num_new_asm_file += 1

                # All blocks have at least one incoming edge
                else:
                    # If more than one incoming edge then use the extended signature
                    if len(self.original_map.blocks[i_block].previous_block_id) > 1:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    # Load expected signature value into register t6
                    i_compile_time_sig_incoming_block = self.compile_time_sig[
                        self.original_map.blocks[i_block].previous_block_id[0]]
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\tt6,' + i_compile_time_sig_incoming_block)
                    i_line_num_new_asm_file += 1
                    # Check the expected value
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,t6')
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tbnez\ts11,' + utils.exception_handler_address)
                    i_line_num_new_asm_file += 1

                inst = 0
                while inst < len(self.original_map.blocks[i_block].entries):

                    # Get the next set of instructions to load from memory
                    l_remaining_opcode_length = self.get_opcode_length_to_jump_signature_length(inst, i_block,
                                                                                                self.length_signature)

                    # When all possible instructions have been accounted for then break this while loop
                    if l_remaining_opcode_length == 0:
                        break

                    if l_remaining_opcode_length == 4:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlhu\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 8:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlwu\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 12:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tld\ts10,18(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tslli\ts10,s10,16')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tsrli\ts10,s10,16')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 16:
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tld\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1


                    elif l_remaining_opcode_length == 24:
                        print("Haven't been tested yet")
                        raise Error
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlq\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 28:
                        print("Haven't been tested yet")
                        raise Error
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlq\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 32:
                        print("Haven't been tested yet")
                        raise Error
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlq\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    else:
                        print("This case isn't possible or we haven't accounted for it.")
                        raise Exception

                    # Get the number of instructions to jump in the asm file
                    inst_to_jump = self.get_number_of_instructions_to_jump_asm_signature_length(inst, i_block,
                                                                                                l_remaining_opcode_length)
                    i_line_num_new_asm_file += inst_to_jump

                    # Get the number of instructions to jump in the basic blocks
                    inst_to_jump = self.get_number_of_instructions_to_jump_signature_length(inst, i_block,
                                                                                            l_remaining_opcode_length)
                    inst += inst_to_jump

                # We are already ahead of the last instruction in the block. Now get back before the last instruction
                # i_line_num_new_asm_file -= 1
                if len(self.original_map.blocks[i_block].next_block_id) != 0:
                    # loop through all the next blocks
                    for i in range(len(self.original_map.blocks[i_block].next_block_id)):
                        if self.D_sig[i_block] != None:
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(self.D_sig[i_block]))
                            break
                        else:
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,0')
                            break
                i_block += 1

            i_line_num_new_asm_file += 1

        if i_block != len(self.original_map.blocks):
            print('Failed to process all blocks. Currently at block id # ' + str(i_block))
            raise Exception

    def get_number_of_instructions_to_jump_asm_signature_length(self, i_inst, i_block, i_sig_length):
        num_inst = 0
        i_num_inst_combined = 0
        length_inst = 0
        while i_inst < len(self.original_map.blocks[i_block].opcode):

            # # # Get the first instruction in this particular block for comparison
            i_line_block_obj = self.original_map.blocks[i_block].entries[i_inst]
            # # # i_line_block_asm could get multiple hits
            i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
            i_num_inst_combined = len(i_line_block_asm[0].split(";"))

            length = len(self.original_map.blocks[i_block].opcode[i_inst])
            if (length + length_inst) > i_sig_length:
                return num_inst
            else:
                length_inst += length
                num_inst += i_num_inst_combined
            i_inst += 1
        return num_inst


    # Definition: gets the number of instructions to jump based on self.length_signature
    def get_number_of_instructions_to_jump_signature_length(self, i_inst, i_block, i_sig_length):
        num_inst = 0
        i_num_inst_combined = 0
        length_inst = 0
        while i_inst < len(self.original_map.blocks[i_block].opcode):

            length = len(self.original_map.blocks[i_block].opcode[i_inst])
            if (length + length_inst) > i_sig_length:
                return num_inst
            else:
                length_inst += length
                num_inst += 1
            i_inst += 1
        return num_inst

    def get_opcode_length_to_jump_signature_length(self, i_inst, i_block, i_sig_length):
        num_inst = 0
        length_inst = 0
        while i_inst < len(self.original_map.blocks[i_block].opcode):
            # Don't consider the final branch instruction within the basic block
            if utils.is_branch_instruction(self.original_map.blocks[i_block].entries[i_inst]):
                return length_inst

            length = len(self.original_map.blocks[i_block].opcode[i_inst])
            if (length + length_inst) > i_sig_length:
                return length_inst
            else:
                length_inst += length
                num_inst += 1
            i_inst += 1
        return length_inst

    # Definition: Gets the length of instructions that are remaining within the block
    def get_remaining_opcode_length(self, i_inst, i_block):
        l_length_opcode_left = 0
        while i_inst < len(self.original_map.blocks[i_block].opcode):

            # Don't consider the final branch instruction within the basic block
            if utils.is_branch_instruction(self.original_map.blocks[i_block].entries[i_inst]):
                return l_length_opcode_left

            length = len(self.original_map.blocks[i_block].opcode[i_inst])
            l_length_opcode_left += length
            i_inst += 1
        return l_length_opcode_left

    def get_matching_asm_line_using_objdump_line(self, i_line):
        # Definition: Checks for a matching line in the objdump file and returns the
        #             corresponding asm line
        line_instruction_map = 0
        list_matching_objects = []
        while line_instruction_map < len(self.instruction_map[0]):
            if i_line == self.instruction_map[1][line_instruction_map]:
                i_asm_instruction = self.instruction_map[0][line_instruction_map]
                list_matching_objects.append(i_asm_instruction)
            line_instruction_map += 1
        return list_matching_objects

    def remove_signature_checking(self, i_s_file, i_objdump_file):
        i = 0
        while i < len(i_s_file):
            l_found = False
            i_line = i_s_file[i]
            if i_line.startswith('\t'):
                i_line = i_line.strip()
                if not i_line.startswith('.'):
                    if utils.is_instruction_signature_checking_asm(i_line):
                        i_s_file.remove(i_s_file[i])
                        i -= 1
            i += 1

        # Just remove all lines from the objdump file that access signature checking registers like s11/s10/t6
        i = 0
        i_excpt_addr = hex(int(utils.exception_handler_address, 10)).split('0x')[-1]
        while i < len(i_objdump_file):
            i_line = i_objdump_file[i]
            if i_line.startswith("   "):
                address, opcode, instruction = i_objdump_file[i].split('\t', 2)
                l_params = instruction.split('\t')[-1]
                if utils.is_signature_checking_register(l_params):
                    i_objdump_file.remove(i_objdump_file[i])
                    i -= 1

                # We also need to remove the j to exception handler
                l_params = (l_params.split(' ')[0]).split(",")
                for j in range(len(l_params)):
                    if (i_excpt_addr == l_params[j]) and (utils.is_branch_instruction(instruction.split('\t')[0])):
                        i_objdump_file.remove(i_objdump_file[i])
                        i -= 1
            i += 1
        return i_s_file, i_objdump_file

    def update_opcodes(self, i_map, i_new_map):
        # Check the total number of official functions in both new and old maps
        if len(i_map.functions.f_instructions) != len(i_new_map.functions.f_instructions):
            print("We don't have the same number of functions")
            raise Exception

        # Check the total number of instructions in each function for both new and old maps
        for i in range(len(i_map.functions.f_instructions)):
            if len(i_map.functions.f_instructions[i].opcode) != len(i_new_map.functions.f_instructions[i].opcode):
                print(
                    "We don't have the same number of instructions in both the function:" + i_map.functions.f_names[i])
                raise Exception

        # Now check the opcodes in both old and new maps and then copy any changes from new to old map
        for i in range(len(i_map.functions.f_instructions)):
            for j in range(len(i_map.functions.f_instructions[i].opcode)):
                if i_map.functions.f_instructions[i].opcode[j] != i_new_map.functions.f_instructions[i].opcode[j]:
                    if not utils.is_branch_instruction(i_map.functions.f_instructions[i].instruction[j]):
                        x1 = i_map.functions.f_instructions[i].instruction[j]
                        y1 = i_new_map.functions.f_instructions[i].instruction[j]
                        old_opcode = i_map.functions.f_instructions[i].opcode[j]
                        new_opcode = i_new_map.functions.f_instructions[i].opcode[j]
                        i_map.functions.f_instructions[i].opcode[j] = i_new_map.functions.f_instructions[i].opcode[j]

                        # Also need to find a matching instruction in the blocks and update the opcode there
                        i_matching_instruction = 0
                        for k in range(len(i_map.blocks)):
                            for m in range(len(i_map.blocks[k].opcode)):
                                if old_opcode == i_map.blocks[k].opcode[m]:
                                    #print("We have a matching opcode that we have to update")
                                    i_map.blocks[k].opcode[m] = new_opcode
                                    i_matching_instruction += 1
                        #if i_matching_instruction > 1:
                            #print("Some how we updated the same opcode in two places. Please check manually")
                            #raise Exception
        return i_map