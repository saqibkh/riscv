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
# This validates the inputs and outputs to each function within the program
# Inputs: input registers are those that are modified by parent function and used by calling function
# Output: output registers are those that are modified by calling function
#
###################################################################################################################

class TRIAL3:
    def __init__(self, i_map):
        self.simlog = i_map.simlog
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

        # Generate the new assembly file
        self.generate_TRIAL3_file_updated()
        self.simlog.info("Finished processing TRIAL3")

    def generate_TRIAL3_file_updated(self):
        inputs_to_check = []
        outputs_to_check = []
        for i in range(len(self.original_map.function_map.functions)):
            i_func_name = self.original_map.function_map.functions[i].name
            input_regs_func_to_check = []
            output_regs_func_to_check = []

            # Processing the input registers first
            # Get a list of all registers modified by parent function
            # Get a list of all registers used by this function
            i_parent_name = self.original_map.function_map.functions[i].parent_function
            i_parent_func_id = self.original_map.function_map.get_function_id_matching_name(i_parent_name)
            # Main doesn't have a parent function
            if i_parent_func_id == None:
                i_reg_parent_modified = []
            else:
                i_reg_parent_modified = self.original_map.function_map.functions[i_parent_func_id].registers_modified
            i_reg_parent_modified = self.remove_registers_not_function_arguments(i_reg_parent_modified)
            i_reg_func_used = self.original_map.function_map.functions[i].registers_used
            i_reg_func_used = self.remove_registers_not_function_arguments(i_reg_func_used)
            for j in range(len(i_reg_func_used)):
                if i_reg_func_used[j] in i_reg_parent_modified:
                    reg_name = i_reg_func_used[j]
                    reg_value = self.get_register_value_from_list(self.original_map.function_map.functions[i].initial_register_values,reg_name)
                    input_regs_func_to_check.append([reg_name, reg_value])
            inputs_to_check.append([i_func_name, input_regs_func_to_check])

            # Processing the output registers now
            # Get a list of all registers that are modified by the function
            i_reg_func_modified = self.original_map.function_map.functions[i].registers_modified
            i_reg_func_modified = self.remove_registers_not_function_arguments(i_reg_func_modified)
            for j in range(len(i_reg_func_modified)):
                reg_name = i_reg_func_modified[j]
                reg_value = self.get_register_value_from_list(self.original_map.function_map.functions[i].final_register_values,reg_name)
                output_regs_func_to_check.append([reg_name, reg_value])
            outputs_to_check.append([i_func_name, output_regs_func_to_check])

        # CLear variables that will not be used anymore
        del i, i_func_name, i_parent_func_id, i_parent_name, i_reg_func_modified, i_reg_func_used
        del j, input_regs_func_to_check, output_regs_func_to_check, reg_name, reg_value, i_reg_parent_modified

    def get_register_value_from_list(self, i_list, i_reg):
        for i in range(len(i_list)):
            if i_list[i][0] == i_reg:
                return i_list[i][1]
        return None

    # Remove the registers from the given list that are not function arguments or return values
    # Must be a0-a7
    def remove_registers_not_function_arguments(self, i_list):
        i_new_list = []
        for i in range(len(i_list)):
            if i_list[i] in registers.function_arg_return_values:
                self.simlog.debug("Register:" + i_list[i] + " is a function_argument.")
                i_new_list.append(i_list[i])
            elif i_list[i] in registers.function_arguments:
                self.simlog.debug("Register:" + i_list[i] + " is a function_argument.")
                i_new_list.append(i_list[i])
            else:
                self.simlog.debug("Register:" + i_list[i] + " not a function_argument")
        return i_new_list


