#!/usr/bin/python

import logging
import time
import utils
import random
import execute_spike
import pexpect

hex_values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']


class Error_Injection:
    def __init__(self, i_file_s, i_file_objdump, simlog=None):
        self.file_s = i_file_s
        self.file_objdump = i_file_objdump
        self.executable_file = i_file_s.split(".s")[0]
        self.instruction_map = [[]]
        self.simlog = simlog
        self.result_passed = 0
        self.result_incorrect = 0
        self.result_exception = 0
        del i_file_s, i_file_objdump, simlog

        # Create a ControlFlowMap for pulling in all necessary instructions
        self.map = utils.ControlFlowMapRevised(utils.readfile(self.file_s), utils.readfile(self.file_objdump),
                                               simlog=self.simlog)

        # Get starting and ending addresses
        self.starting_address = self.map.blocks[0].memory[0]
        self.ending_address = self.map.blocks[-1].memory[-1]

        # Create a list of instruction from the map, that includes mem location, opcode and instruction
        for i in range(len(self.map.blocks)):
            for j in range(len(self.map.blocks[i].entries)):
                i_mem_location = self.map.blocks[i].memory[j]
                i_opcode = self.map.blocks[i].opcode[j]
                i_instruction = self.map.blocks[i].entries[j]
                self.instruction_map.append([i_mem_location, i_opcode, i_instruction])

        del i, j, i_mem_location, i_opcode, i_instruction

    def inject_error_return_result(self):
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
