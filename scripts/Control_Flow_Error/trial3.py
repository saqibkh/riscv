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
#      Assuming that each function is called only once (i.e. registers could only hold 1 value)
# Inputs: input registers are those that are modified by parent function and used by calling function
# Output: output registers are those that are modified by calling function
#
#
# TODO: explore programs that call same functions multiple time and how to handle those cases.
#       One way is to ignore functions, that are called multiple times. i.e. only check inputs/outputs to functions
#       that are called only once.
#
###################################################################################################################

def update_registers(i_file):
    i_found = False

    with fileinput.FileInput(i_file, inplace=True, backup='.bak') as file:
        for line in file:
            if line.startswith("\tli\ts11") and not i_found:
                i_found = True
                continue

            if i_found:
                if line.startswith("\tbne\t"):
                    components = (line.strip()).split('\t')
                    inst = components[0]
                    operands = components[1]
                    operand_to_replace = operands.split(',')[0]
                    print(line.replace(operand_to_replace, "s11", 1), end='')
                    i_found = False
                    continue
                else:
                    print("Something unexpected occured")
                    raise Exception


def update_values(i_obj_old, i_obj_new, i_file):
    is_updated = False

    # First check for discrepancies in the inputs to be checked
    for i in range(len(i_obj_old.inputs_to_check)):
        for j in range(len(i_obj_old.inputs_to_check[i][1])):
            i_old_reg = i_obj_old.inputs_to_check[i][1][j][0]
            i_old_value = i_obj_old.inputs_to_check[i][1][j][1]

            i_new_reg = i_obj_new.inputs_to_check[i][1][j][0]
            i_new_value = i_obj_new.inputs_to_check[i][1][j][1]

            if (i_old_value == '') or (i_old_value is None):
                print("Unexpected Error. The vale is undefined")
                raise Exception

            if (i_new_value == '') or (i_new_value is None):
                print("Unexpected Error. The vale is undefined")
                raise Exception

            # The names of the old and new registers must match
            if i_old_reg != i_new_reg:
                print("There is a difference in the registers that are being used: "
                      + i_old_reg + "!=" + i_new_reg)
                raise Exception

            if i_old_value != i_new_value:
                is_updated = True
                with fileinput.FileInput(i_file, inplace=True, backup='.bak') as file:
                    for line in file:
                        print(line.replace(i_old_value, i_new_value), end='')

    # Next check for discrepancies in the outputs to be checked
    for i in range(len(i_obj_old.outputs_to_check)):
        for j in range(len(i_obj_old.outputs_to_check[i][1])):
            i_old_reg = i_obj_old.outputs_to_check[i][1][j][0]
            i_old_value = i_obj_old.outputs_to_check[i][1][j][1]

            i_new_reg = i_obj_new.outputs_to_check[i][1][j][0]
            i_new_value = i_obj_new.outputs_to_check[i][1][j][1]

            if i_old_value == '':
                print("Unexpected Error. The vale is undefined")
                raise Exception

            if i_new_value == '':
                print("Unexpected Error. The vale is undefined")
                raise Exception

            # The names of the old and new registers must match
            if i_old_reg != i_new_reg:
                print("There is a difference in the registers that are being used: "
                      + i_old_reg + "!=" + i_new_reg)
                raise Exception

            if i_old_value != i_new_value:
                is_updated = True
                with fileinput.FileInput(i_file, inplace=True, backup='.bak') as file:
                    for line in file:
                        print(line.replace(i_old_value, i_new_value), end='')

    return is_updated


class TRIAL3:
    def __init__(self, i_map, i_recalculate_reg_values=False):
        self.simlog = i_map.simlog
        self.original_map = i_map

        # Registers that are to be checked at the input and output of each functions
        self.inputs_to_check = []
        self.outputs_to_check = []

        # Compile time signature
        self.compile_time_sig = []

        # This instruction map will have a 1-to-1 mapping between instructions
        # in .s and .objdump files.
        # Elements in array 0 belongs to .s file
        # Elements in array 1 belongs to .objdump
        self.instruction_map = [[]]
        self.new_asm_file = self.original_map.file_asm

        self.gather_registers_to_be_checked()

        # Generate instruction mapping between .s and .objdump file instructions
        if i_recalculate_reg_values:
            return

        # Generate the new assembly file
        utils.generate_instruction_mapping(self)
        self.generate_TRIAL3_file_updated()

    def generate_TRIAL3_file_updated(self):
        i_function = 0
        i_line_num_new_asm_file = 0

        # 1. Loop the asm file lines until the end of file
        while i_line_num_new_asm_file < len(self.new_asm_file):

            # Return once all the functions are processed
            if i_function == len(self.original_map.functions.f_names):
                return

            function_found = False
            i_line_asm = self.original_map.file_asm[i_line_num_new_asm_file]

            # A function will start when the line matches the function name (such as "main:" or "countsetBits:")
            if i_line_asm == self.original_map.functions.f_names[i_function] + ":":
                function_found = True

            if function_found:
                # Move to the next line of the function
                i_line_num_new_asm_file += 1

                # Check the inputs to this particular function
                for i in range(len(self.inputs_to_check[i_function][1])):
                    l_register = self.inputs_to_check[i_function][1][i][0]
                    l_value = self.inputs_to_check[i_function][1][i][1]

                    # Make sure the register value exist
                    if l_value == '':
                        self.simlog.error("Register value is empty:" + l_register)
                        raise Exception

                    # If a None exists in the register value then skip this register as
                    # we will never go to this function
                    if not l_value:
                        self.simlog.debug('Not adding a check for register:' + l_register
                                          + 'because it is None')
                        continue

                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts11,' + l_value)
                    i_line_num_new_asm_file += 1
                    self.new_asm_file.insert(i_line_num_new_asm_file, '\tbne\t' + l_register + ','
                                             + l_register + "," + utils.exception_handler_address)
                    i_line_num_new_asm_file += 1

                # Find the instruction within the function that calls the return address ("jr ra")
                # There must be a jump to return address for each function.
                while 1:
                    i_line_asm = (self.original_map.file_asm[i_line_num_new_asm_file]).strip()
                    if i_line_asm == 'jr\tra':
                        # Now add the checks for output registers
                        for i in range(len(self.outputs_to_check[i_function][1])):
                            l_register = self.outputs_to_check[i_function][1][i][0]
                            l_value = self.outputs_to_check[i_function][1][i][1]

                            # Make sure the register value exist
                            if l_value == '':
                                self.simlog.error("Register value is empty:" + l_register)
                                raise Exception

                            # If a None exists in the register value then skip this register as
                            # we will never go to this function
                            if not l_value:
                                self.simlog.debug('Not adding a check for register:' + l_register
                                                  + 'because it is None')
                                continue

                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tli\ts11,' + l_value)
                            i_line_num_new_asm_file += 1
                            self.new_asm_file.insert(i_line_num_new_asm_file, '\tbne\t' + l_register + ','
                                                     + l_register + "," + utils.exception_handler_address)
                            i_line_num_new_asm_file += 1

                        # Now finish processing this function
                        function_found = False
                        break
                    else:
                        i_line_num_new_asm_file += 1

                # Finish processing the function
                i_function += 1
            i_line_num_new_asm_file += 1

    def gather_registers_to_be_checked(self):
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
                    reg_value = self.get_register_value_from_list(
                        self.original_map.function_map.functions[i].initial_register_values, reg_name)
                    input_regs_func_to_check.append([reg_name, reg_value])
            self.inputs_to_check.append([i_func_name, input_regs_func_to_check])

            # Processing the output registers now
            # Get a list of all registers that are modified by the function
            i_reg_func_modified = self.original_map.function_map.functions[i].registers_modified
            i_reg_func_modified = self.remove_registers_not_function_arguments(i_reg_func_modified)
            for j in range(len(i_reg_func_modified)):
                reg_name = i_reg_func_modified[j]
                reg_value = self.get_register_value_from_list(
                    self.original_map.function_map.functions[i].final_register_values, reg_name)
                output_regs_func_to_check.append([reg_name, reg_value])
            self.outputs_to_check.append([i_func_name, output_regs_func_to_check])

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
