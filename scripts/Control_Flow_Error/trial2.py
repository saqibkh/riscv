import datetime
import random
import subprocess
import utils
from os import path



class TRIAL2:
    def __init__(self, i_map):
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

        utils.generate_instruction_mapping(self)

        # Calculate the compile_time signature
        self.calculate_compile_time_sig()

        # Generate the new assembly file
        self.generate_TRIAL2_file_updated()

        print("Finished processing TRIAL2")

    def calculate_compile_time_sig(self):
        for i in range(len(self.original_map.blocks)):
            cum_sig = '0x0'
            compound_sig = ''
            for j in range(len(self.original_map.blocks[i].entries)):
                sig = self.original_map.blocks[i].opcode[j]

                if len(compound_sig) + len(sig) <= 16:
                    compound_sig = compound_sig + sig
                else:
                    cum_sig = hex(int(cum_sig, 16) ^ int(compound_sig, 16))
                    compound_sig = ''

            # Process remaining instruction signatures
            if compound_sig != '':
                cum_sig = hex(int(cum_sig, 16) ^ int(compound_sig, 16))
                compound_sig = ''

            # Finally add the cum_sig back to the list of compile time signatures
            self.compile_time_sig.append(cum_sig)

    def generate_TRIAL2_file_updated(self):
        print("Done")