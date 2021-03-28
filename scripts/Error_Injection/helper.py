#!/usr/bin/python

import logging
import time
import utils
import random
import execute_spike
import pexpect
import compileUtil

hex_values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']


def split(word):
    return [char for char in word]


def get_new_opcode(i_original_opcode):
    # Convert hex to binary
    i_new_opcode = bin(int(i_original_opcode, 16))[2:].zfill(len(i_original_opcode)*4)

    # Pick a random bit number
    i_magic_bit_num = random.randint(0, len(i_new_opcode)-1)
    # Update the bit based on magic bit number
    i_new_opcode = split(i_new_opcode)
    i_bit = i_new_opcode[i_magic_bit_num]

    if i_bit == '0':
        i_new_opcode[i_magic_bit_num] = '1'
    else:
        i_new_opcode[i_magic_bit_num] = '0'
    # Rejoin the opcode to make it whole
    i_new_opcode = ''.join(i_new_opcode)

    # Convert binary to hex
    i_new_opcode = hex(int(i_new_opcode, 2)).split('0x')[-1]
    return i_new_opcode


class Error_Injection:
    def __init__(self, i_file_s, i_file_objdump, simlog=None):
        self.file_s = i_file_s

        compileUtil.compile_s(i_file_s)
        self.file_s_result = execute_spike.execute_spike_without_debug(i_file_s.split('.s')[0])
        # Remove the execution time
        self.file_s_result = self.file_s_result.split('\r\n')
        for i in range(len(self.file_s_result)):
            if 'Total Execution time' in self.file_s_result[i]:
                del self.file_s_result[i]
                break
        self.file_s_result = '\r\n'.join(self.file_s_result)

        self.file_objdump = i_file_objdump
        self.file_s_tmp = i_file_s.split(".s")[0] + "_tmp.s"
        self.instruction_map = [[]]
        self.simlog = simlog
        self.result_passed = 0
        self.result_incorrect = 0
        self.result_exception = 0
        self.result_exception_handler = 0
        del i_file_s, i_file_objdump, simlog

        # Create a ControlFlowMap for pulling in all necessary instructions
        self.map = utils.ControlFlowMapRevised(utils.readfile(self.file_s), utils.readfile(self.file_objdump),
                                               simlog=self.simlog)

        # Get starting and ending addresses
        self.starting_address = self.map.blocks[0].memory[0]
        self.ending_address = self.map.blocks[-1].memory[-1]

        # Delete any old file matching the same name
        compileUtil.delete_file_if_exists(self.file_s_tmp)

        self.generate_asm_with_opcodes()

        # Make sure both the asm files produce the same result
        compileUtil.compile_s(self.file_s)
        compileUtil.compile_s(self.file_s_tmp)
        l_original_result = execute_spike.execute_spike_without_debug(self.file_s.split('.s')[0])
        l_updated_result = execute_spike.execute_spike_without_debug(self.file_s_tmp.split('.s')[0])
        if l_original_result != l_updated_result:
            self.simlog.error("New and old results don't match")
            self.simlog.error("\n\nOriginal file:\n" + l_original_result)
            self.simlog.error("\n\nModified file:\n" + l_updated_result)

    # Locate the instructions in the asm file and find a corresponding instruction in the objdump file.
    # If there is match, then replace all instances of that instruction in the asm file
    def generate_asm_with_opcodes(self):
        # Generate an instruction map from the objdump file
        for i in range(len(self.map.blocks)):
            for j in range(len(self.map.blocks[i].entries)):
                i_mem_location = self.map.blocks[i].memory[j]
                i_opcode = self.map.blocks[i].opcode[j]
                i_instruction = self.map.blocks[i].entries[j]
                self.instruction_map.append([i_mem_location, i_opcode, i_instruction])
        del i, j, i_mem_location, i_opcode, i_instruction, self.instruction_map[0]

        new_asm_file = self.map.file_asm
        for i in range(len(new_asm_file)):
            i_line = new_asm_file[i]
            if utils.is_instruction_asm(i_line):
                i_line = i_line.strip()

                for j in range(len(self.instruction_map)):
                    i_objdump_instruction = self.instruction_map[j][2]
                    if i_line == i_objdump_instruction:
                        i_objdump_opcode = self.instruction_map[j][1]
                        # Replace the original instruction in the asm file with the opcode
                        if len(i_objdump_opcode) == 4:
                            new_asm_file[i] = "\t.short(0x" + i_objdump_opcode + ")" + " #INSTRUCTION: " + i_objdump_instruction
                        elif len(i_objdump_opcode) == 8:
                            new_asm_file[i] = "\t.long(0x" + i_objdump_opcode + ")" + " #INSTRUCTION: " + i_objdump_instruction
                        else:
                            simlog.errror("Unrecognized length of opcode detected")
                        break
        del i, j, i_objdump_instruction, i_objdump_opcode, i_line

        # Step2: Create a copy of <file>.s into <file>_tmp.s
        # Now create an exact copy of the original .s file
        with open(self.file_s_tmp, 'w') as filehandle:
            for listitem in new_asm_file:
                filehandle.write('%s\n' % listitem)
        del new_asm_file, listitem, filehandle

    # This attempt to update the asm file is not correct as it is not able to locate stored variables
    def generate_asm_with_opcodes_attempt_1(self):
        # Step1: Now we need to replace all instruction in the asm file with its opcode
        new_asm_file = self.map.file_asm
        i_function = 0
        i_func_name = self.map.functions.f_names[i_function]
        i_func_opcodes = self.map.functions.f_instructions[i_function].opcode
        i = 0
        while i < len(new_asm_file):
            l_line = new_asm_file[i]

            # Option:0 This line could be start of the main function.
            #if l_line == "main:":
            #    break
            # Option:1 This line could be start of a function
            if l_line == i_func_name + ":":

                # Start adding opcodes in hex right after the function declaration
                for j in range(len(i_func_opcodes)):
                    if len(i_func_opcodes[j]) == 4:
                        new_asm_file.insert(i+1+j, "\t.short(0x" + i_func_opcodes[j] + ")")
                    elif len(i_func_opcodes[j]) == 8:
                        new_asm_file.insert(i+1+j, "\t.long(0x" + i_func_opcodes[j] + ")")
                    else:
                        simlog.errror("Unrecognized length of opcode detected")

                i += len(i_func_opcodes)
                i_function += 1

                # An exception will be generated when fetching the next function name after the last function.
                # Thus catch this exception and continue with execution.
                try:
                    i_func_name = self.map.functions.f_names[i_function]
                    i_func_opcodes = self.map.functions.f_instructions[i_function].opcode
                except Exception as e:
                    continue

            # Option:2 This line could be an instruction. Remove any instruction that are found here
            elif utils.is_instruction_asm(l_line):
                new_asm_file.remove(l_line)
                i -= 1
            i += 1
        del i_function, i_func_name, i_func_opcodes, i, j, l_line

        # Step2: Create a copy of <file>.s into <file>_tmp.s
        # Now create an exact copy of the original .s file
        with open(self.file_s_tmp, 'w') as filehandle:
            for listitem in new_asm_file:
                filehandle.write('%s\n' % listitem)
        del new_asm_file, listitem, filehandle

        compileUtil.compile_s(self.file_s)
        compileUtil.compile_s(self.file_s_tmp)

    def inject_error_return_result(self, i_test_num):
        error_injected = False
        l_asm_file = utils.readfile(self.file_s_tmp)

        # Get a list of all instruction that have an opcode
        l_inst_list = []
        for i in range(len(l_asm_file)):
            l_line = l_asm_file[i]
            if l_line.startswith("\t.short(0x") or l_line.startswith("\t.long(0x"):
                l_inst_list.append(l_line)
        del l_line, i

        # Get a magic number between 0 and length of instructions whose opcodes we have
        i_magic_instruction = random.randint(0, len(l_inst_list))

        # Now change the opcode of the instruction whose number matches the magic_instruction
        i_instruction = 0
        for i in range(len(l_asm_file)):
            l_line = l_asm_file[i]
            if l_line.startswith("\t.short(0x") or l_line.startswith("\t.long(0x"):
                if i_instruction == i_magic_instruction:
                    i_original_opcode = (l_line.split('(0x')[-1]).split(")")[0]
                    i_new_opcode = get_new_opcode(i_original_opcode)
                    l_line = l_line.replace(i_original_opcode, i_new_opcode)
                    l_asm_file[i] = l_line + "Error injected here: " + i_original_opcode
                    error_injected = True
                    break
                else:
                    i_instruction += 1

        # It is possible that we didn't inject any error. Therefore check before progressing further
        if error_injected:
            # Write a new assembly file with the injected error and run the executable to get the result
            l_test_file = self.file_s_tmp.split('.s')[0] + "_test.s"
            with open(l_test_file, 'w') as filehandle:
                for listitem in l_asm_file:
                    filehandle.write('%s\n' % listitem)
            del l_asm_file, listitem, filehandle

            compileUtil.compile_s(l_test_file)
            try:
                l_result = execute_spike.execute_spike_without_debug(l_test_file.split('.s')[0])
                # Break the l_result into lines and remove the Execution time output
                l_result = l_result.split("\r\n")
                for i in range(len(l_result)):
                    if "Total Execution time:" in l_result[i]:
                        del l_result[i]
                        break
                l_result = '\r\n'.join(l_result)
            except Exception as e:
                self.result_exception += 1
                return

            # Check for exception
            if 'segfault @' in l_result:
                if 'segfault @ 0x0000000000000064' in l_result:
                    self.result_exception_handler += 1
                else:
                    self.result_exception += 1
            elif 'An illegal instruction was executed!' in l_result:
                self.result_exception += 1

            # Match the result with the expected result
            elif l_result == self.file_s_result:
                self.result_passed += 1

            # All other results are incorrect
            else:
                self.result_incorrect += 1

            #self.simlog.info("\n" + l_result)

        else:
            self.simlog.info("Didn't inject any error. Please check manually why")

    def inject_error_return_result_attemp1(self):
        # i_magic will be used as a random number to get the memory location where the error injection will take place
        i_magic = random.randint(0, len(self.instruction_map))

        i_mem_location = self.instruction_map[i_magic][0]
        i_opcode = self.instruction_map[i_magic][1]
        i_instruction = self.instruction_map[i_magic][2]

        # Spike is the name of the simulator
        l_spike_object = execute_spike.execute_spike_address(self.executable_file, self.starting_address)
        # Now get the contents of the memory location and match with the opcode
        i_cmd = 'mem 0 ' + i_mem_location
        l_spike_object.sendline(i_cmd)
        l_spike_object.expect([i_cmd + '\r\n', pexpect.EOF])
        i_opcode_from_memory = ((l_spike_object.readline()).decode("utf-8")).split("\r\n")[0]

        # Make sure the last 4 hex digits have the same value
        if i_opcode[-4:] != i_opcode_from_memory[-4:]:
            self.simlog.error("For some reason the opcode from the map and the memory location don't match.")
            self.simlog.error("Opcode from map:" + i_opcode)
            self.simlog.error("Opcode from memory:" + i_opcode_from_memory)
            raise Exception


        print("Here")
