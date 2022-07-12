import utils
import fileinput
from os import path
import random

###################################################################################################################
#
# This is a new type of CFE detection technique. Each block must have two signatures.
# 1) Compile time signature (C_sig) is generated by XOR'ing the instruction opcodes within that basic block except the
#    branch instruction at end.
# 2) Random signature (R_sig) assigned at compile time, which will also act as the expected signature.
#
# Both signatures will be 16-bits(4 bytes) long. (Since load immediate(LI) has limited bandwidth)
#
# The initial block will have both C_sig set to 0 at the start of the block. Csig is stored in s11
# As we being executing the instructions in block-0, we will calculate the C_sig by XOR'ing instruction opcodes, and
# storing the result in s11.
# If the final instruction is not a conditional branch (i.e. is either an unconditional branch or not-a-branch
# instruction, then C_sig is XOR'ed with temporary signature (T_sig) defined as C_sig XOR R_sig_successor.
# This changes the value of C_sig stored in s10 to be equal to the R_sig of the successor block.
#
# Once the program execution reaches the correct signature block, we will load the expected signature in this case the
# R_sig into s11, and then XOR with s10. If the control flow was correct, both s10 and s11 will hold the same R_sig
# value, thus resulting in a zero. Any value besides a zero must trigger an exception as there has been a control flow
# error.
#
# Once the signatures are verified at the start of the basic block, the s10 will not hold zero, and we can again begin
# calculating the opcode signatures of the next block.
#
###################################################################################################################


class SEDIS_2_0:
    def __init__(self, i_map, i_generate_signature_only=False):
        self.simlog = i_map.simlog

        # Length of signature in bytes
        # 4-bytes  = 16  bits
        # 8-bytes  = 32  bits
        # 16-bytes = 64  bits
        # 32-bytes = 128 bits
        self.length_signature = 16

        self.original_map = i_map

        # Compile time signature (C_sig)
        self.compile_time_sig = []
        # Random signature (R_sig)
        self.random_sig = []
        # Temporary Signature (T_sig)
        self.temp_sig = []

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        self.process_blocks()
        utils.generate_instruction_mapping(self)

        # Generate the new assembly file
        self.generate_SEDIS_2_0_file_updated()

    def generate_SEDIS_2_0_file_updated(self):
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
            # 1. When a function beings within the asm file (make sure the first instruction within the function and
            # the block matches one another)
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
                    if utils.is_branch_instruction(i_line_asm) or \
                            i_line_asm.startswith('li\ts10,'):
                        # Get the first instruction in the next block for comparison
                        try:
                            i_line_block_obj = self.original_map.blocks[i_block].entries[0]
                        except:
                            self.simlog.info('done')
                        i_line_block_asm = self.get_matching_asm_line_using_objdump_line(i_line_block_obj)
                        try:
                            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1]
                            for i in range(len(i_line_block_asm)):
                                if self.original_map.file_asm[i_line_num_new_asm_file + 1].split('\t', 1)[1] in \
                                        i_line_block_asm[i]:
                                    block_found = True
                                    break
                        except Exception as e:
                            # unexpected line encountered
                            i_line_num_new_asm_file += 1
                            continue

            if block_found:
                i_line_num_new_asm_file += 1

                # If it is the first block or initial block then just set s11 to 0.
                # It has no incoming edges
                if len(self.original_map.blocks[i_block].previous_block_id) == 0:
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts11,0')
                    i_line_num_new_asm_file += 1

                # All other blocks have at least one incoming edge
                else:
                    # If this isn't the first basic block, then it must have a predecessor block
                    # and that block must have set the Csig and Tsig. Therefore calculate
                    # the new signature as Csig XOR Tsig, which must be equal to Rsig
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                    i_line_num_new_asm_file += 1

                    # Load expected random signature value into register s10
                    i_random_signature = self.random_sig[self.original_map.blocks[i_block].id]
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + i_random_signature)
                    i_line_num_new_asm_file += 1
                    # Check the expected value
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
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
                        self.simlog.error("Haven't been tested yet")
                        raise Error
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlq\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 28:
                        self.simlog.error("Haven't been tested yet")
                        raise Error
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlq\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    elif l_remaining_opcode_length == 32:
                        self.simlog.error("Haven't been tested yet")
                        raise Error
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tauipc\ts10,0')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tlq\ts10,12(s10)')
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\txor\ts11,s11,s10')
                        i_line_num_new_asm_file += 1

                    else:
                        self.simlog.error("This case isn't possible or we haven't accounted for it.")
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

                # We don't need to do anything if we are on the last block of the program
                if len(self.original_map.blocks[i_block].next_block_id) != 0:
                    # If the final instruction in this block is a load/store, arithmetic, or unconditional branch
                    # then we need to simply load Tsig into s10
                    last_line = self.new_asm_file[i_line_num_new_asm_file].strip()
                    if utils.is_unconditional_branch_instruction(last_line) or \
                            utils.is_arithmetic_instruction(last_line) or \
                            utils.is_load_store_instruction(last_line) or \
                            last_line.startswith("."): # If it is not a branch instruction then we have already
                                                       # reached the function declaration of the next block.
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(self.temp_sig[i_block]))

                    # The final instruction is a conditional branch instruction, which needs to be processed
                    # differently.
                    elif utils.is_conditional_branch_instruction(last_line):
                        new_line = last_line.replace(last_line.split('\t')[0], utils.get_opposite_branch_instruction(last_line))
                        new_line = new_line.rsplit(',', 1)[0]
                        new_line += ',.T' + str(i_block)
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\t' + new_line)
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(self.temp_sig[i_block]))
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tj\t' + str(last_line.split(',')[-1]))
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '.T' + str(i_block) + ":")
                        i_line_num_new_asm_file += 1
                        self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts10,' + str(self.temp_sig[i_block]))
                        i_line_num_new_asm_file += 1
                        del self.new_asm_file[i_line_num_new_asm_file]
                        i_line_num_new_asm_file -= 2

                    else:
                        self.simlog.error("Unrecognized instruction: " + str(last_line))
                        raise Exception

                i_block += 1

            i_line_num_new_asm_file += 1

        if i_block != len(self.original_map.blocks):
            self.simlog.error('Failed to process all blocks. Currently at block id # ' + str(i_block))
            raise Exception

    def process_blocks(self):
        # 1. Generate compile time signature for each block
        for i in range(len(self.original_map.blocks)):
            cum_sig = '0x0'
            compound_sig = ''
            j = 0
            while j < len(self.original_map.blocks[i].entries):

                # Don't consider branch instructions in the computation of compile time signature
                if utils.is_branch_instruction(self.original_map.blocks[i].entries[j]):
                    break

                sig = self.original_map.blocks[i].opcode[j]
                if len(compound_sig) + len(sig) <= self.length_signature:
                    compound_sig = sig + compound_sig
                    j = j + 1
                else:
                    cum_sig = hex(int(cum_sig, 16) ^ int(compound_sig, 16))
                    compound_sig = ''

            # Process remaining instruction signatures
            if compound_sig != '':
                cum_sig = hex(int(cum_sig, 16) ^ int(compound_sig, 16))
                compound_sig = ''
            # Finally add the cum_sig back to the list of compile time signatures (only store the last 16 bits (4-bytes)
            cum_sig = '0x' + cum_sig[-4:]
            self.compile_time_sig.append(cum_sig)
        del i, j, cum_sig, sig, compound_sig

        # 2. Assign random signature (R_sig)
        for i in range(len(self.original_map.blocks)):
            returnVal = "0x" + hex(random.sample(range(1, len(self.original_map.blocks) * 65421), 1)[0])[-4:]
            self.random_sig.append(returnVal)

        # Calculate the temporary signature (T_sig).
        # Tsig is the temporary signature generated by XOR'ing the Csig of the current block with the Rsig
        # of the first successor block
        for i in range(len(self.original_map.blocks)):
            if len(self.original_map.blocks[i].next_block_id) == 0:
                t_sig = "0x0"
            else:
                t_sig = hex(int(self.random_sig[self.original_map.blocks[i].next_block_id[0]], 16) ^
                            int(self.compile_time_sig[i], 16))
            self.temp_sig.append(t_sig)

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
            self.simlog.error("We don't have the same number of functions")
            raise Exception

        # Check the total number of instructions in each function for both new and old maps
        for i in range(len(i_map.functions.f_instructions)):
            if len(i_map.functions.f_instructions[i].opcode) != len(i_new_map.functions.f_instructions[i].opcode):
                self.simlog.error(
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