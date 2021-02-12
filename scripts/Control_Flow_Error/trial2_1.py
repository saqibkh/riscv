import datetime
import random
import subprocess
import utils
import compileUtil
import fileinput
import execute_spike
from os import path

###################################################################################################################
#
# This is a new type of CFE detection technique where the compile time signature of a basic block is
# generated by XOR'ing the instruction opcodes within that basic block except the branch instruction
# at the end. This method takes care of inter-block CFEs, intra-block CFEs, and some types of DFE
# errors as well.
#
# The basic block that has two incoming edges requires an extended signature (D_sig) which is generated
# is a similar fashion as a CFCSS technique.
#
# After compilation, the opcodes might change due to added instructions (stack might grow in size), which
# could affect the offset within each instruction. Therefore, compile the program again, and re-calculate
# the signatures and then match it with the existing signatures. This is a new feature that is essential
# for DFE detection techniques.
#
# This is an upgraded implementation which was done in TRIAL2. The only difference is that the expected signatures
# are loaded from memory instruction of being loaded via multiple instructions. This helps in reducing the overall
# memory requirements for the implementation
#
#
###################################################################################################################


def store_signature_in_memory(i_file):
    signature_number = 0
    signature_list = []
    l_file = utils.readfile(i_file)

    # Get the signatures in a list
    for i in range(len(l_file)):
        i_line = l_file[i]
        if '\tli\tt6' in i_line:
            l_signature_name = '.VR' + str(signature_number)
            l_signature_value = i_line.split(',')[-1]
            signature_list.append([l_signature_name, l_signature_value])
            signature_number += 1

            # Load signature from a variable stored in memory
            l_file.insert(i + 0, '\tlui\ts9,%hi(' + l_signature_name + ')')
            l_file.insert(i + 1, '\taddi\ts9,s9,%lo(' + l_signature_name + ')')
            l_file.insert(i + 2, '\tld\tt6,0(s9)')
            i += 3
            del l_file[i]

    # We have now reached the end of file. This is a safe place to store the signature variables
    for i in range(len(signature_list)):
        l_signature_name = signature_list[i][0]
        l_signature_value = int(signature_list[i][1], 16)
        l_file.append(l_signature_name + ":")
        l_file.append('\t.dword\t' + str(l_signature_value) + "\t#" + str(hex(l_signature_value)))
        l_file.append('\t.text')
        l_file.append('\t.align 1')

    # Rewrite the file
    with open(i_file, 'w') as filehandle:
        for listitem in l_file:
            filehandle.write('%s\n' % listitem)

    # Now compile the new file
    compileUtil.compile_s(i_file)
    del filehandle, i, i_line, l_file, l_signature_name, l_signature_value, listitem, signature_list, signature_number

    # Now this is a bit of a hack
    # The signature has changed because we add/changed a few instructions.
    # Therefore run the simulator and modify signatures as needed
    update_needed = True
    while update_needed:
        l_output = execute_spike.execute_spike_without_debug(i_file.rsplit(".s", 1)[0])

        if 'User fetch segfault @ 0x' in l_output:
            l_file = utils.readfile(i_file)
            t6 = (l_output.split('t6 ', 1)[-1]).split('\r\n')[0]
            while t6.startswith('0') and (t6 != '0'):
                t6 = t6.split('0', 1)[-1]
            s11 = (l_output.split('sB ', 1)[-1]).split('\r\n')[0]
            new_signature_int = int(t6, 16) ^ int(s11, 16)
            new_signature_hex = (hex(new_signature_int)).split('0x')[-1]

            # Update the signatures in the assembly file
            for i in range(len(l_file)):
                line = l_file[i]
                if line.startswith('\t.dword\t' + str(int(t6, 16))):

                    # It is possible that there are two same signatures.
                    # Take a guess as to which one to update
                    if random.random() < 0.5:
                        line = '\t.dword\t' + str(new_signature_int) + "\t#0x" + str(new_signature_hex)
                        l_file[i] = line
            # Rewrite the file
            with open(i_file, 'w') as filehandle:
                for listitem in l_file:
                    filehandle.write('%s\n' % listitem)
            # Compile the file again
            compileUtil.compile_s(i_file)
        else:
            update_needed = False


def update_signature(i_obj_old, i_obj_new, i_file):
    is_updated = False
    i_sig_old = i_obj_old.compile_time_sig
    i_sig_new = i_obj_new.compile_time_sig

    i_D_sig_old = i_obj_old.D_sig
    i_D_sig_new = i_obj_new.D_sig

    for i in range(len(i_sig_old)):
        # If signature is not the same then update the .s file
        if i_sig_old[i] != i_sig_new[i]:
            x = i_sig_old[i]
            y = i_sig_new[i]
            is_updated = True
            with fileinput.FileInput(i_file, inplace=True, backup='.bak') as file:
                for line in file:
                    print(line.replace(i_sig_old[i], i_sig_new[i]), end='')

    for i in range(len(i_D_sig_old)):
        # If signature is not the same then update the .s file
        if i_D_sig_old[i] != i_D_sig_new[i]:
            is_updated = True
            with fileinput.FileInput(i_file, inplace=True, backup='.bak') as file:
                for line in file:
                    print(line.replace(i_D_sig_old[i], i_D_sig_new[i]), end='')

    return is_updated

class TRIAL2_1:
    def __init__(self, i_map, i_generate_signature_only=False):
        self.simlog = i_map.simlog

        # Length of signature in bytes
        # 4-bytes  = 16  bits
        # 8-bytes  = 32  bits
        # 16-bytes = 64  bits
        # 32-bytes = 128 bits
        self.length_signature = 16

        self.original_map = i_map

        # Compile time signature
        self.compile_time_sig = []

        # Defines a valid branch to a block signature
        self.valid_branch_d = []

        # Extended signature
        self.D_sig = [None] * len(i_map.blocks)
        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        self.process_blocks()

        # If i_generate_signature_only is True, then don't proceed any further
        if i_generate_signature_only:
            return

        utils.generate_instruction_mapping(self)

        # Generate the new assembly file
        self.generate_TRIAL2_1_file_updated()

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
            # Finally add the cum_sig back to the list of compile time signatures
            self.compile_time_sig.append(cum_sig)

        # 2. Generate the valid branch for each block
        #    Valid branch (d_i) is calculated as: d_i = s_i XOR s_pred1 (predecessor 1)
        # for i in range(len(self.original_map.blocks)):
        #     s_i = self.compile_time_sig[i]
        #     # First make sure that a predecessor block exist which might not always be true
        #     # Main will not have an incoming block.
        #     if not self.original_map.blocks[i].previous_block_id:
        #         s_pred1 = s_i
        #         d_i = s_i
        #     else:
        #         # 0th elements points to first predecessor
        #         s_pred1 = self.get_signature_based_on_id(self.original_map.blocks[i].previous_block_id[0])
        #         d_i = hex(int(s_i, 16) ^ int(s_pred1, 16))
        #     self.valid_branch_d.append(d_i)
        #     del d_i, s_i, s_pred1

        # 3. Generate D (run-time adjusting signature). When a basic block has multiple incoming edges,
        # the signature uses an extra variable D. This variable is updated by the predecessor basic blocks
        # and ensures that the run-time signature can be updated to the correct value,
        # regardless of which predecessor has executed.
        for i in range(len(self.original_map.blocks)):
            if len(self.original_map.blocks[i].previous_block_id) > 1:
                # Get the signature of the first incoming block
                predesessor_block_id_1 = self.original_map.blocks[i].previous_block_id[0]
                D_sign = self.compile_time_sig[predesessor_block_id_1]

                for j in range(len(self.original_map.blocks[i].previous_block_id) - 1):
                    predesessor_block_id_next = self.original_map.blocks[i].previous_block_id[j + 1]
                    # Get the ID of the incoming blocks
                    incoming_block_id = self.original_map.blocks[i].previous_block_id[j + 1]
                    self.D_sig[incoming_block_id] = hex(int(D_sign, 16) ^
                                                        int(self.compile_time_sig[predesessor_block_id_next], 16))

    def get_signature_based_on_id(self, i_id):
        for i in range(len(self.original_map.blocks)):
            if self.original_map.blocks[i].id == i_id:
                return self.compile_time_sig[i]

    def generate_TRIAL2_1_file_updated(self):
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
                            self.simlog.info('done')
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
            self.simlog.error('Failed to process all blocks. Currently at block id # ' + str(i_block))
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