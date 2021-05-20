#!/usr/bin/python

import os
import pexpect
import subprocess
import tempfile
import testlib
import unittest
import sys
import time
import registers

''' Start of class definitions'''


def store_register_values_in_list(i_list, i_register, i_value):

    # The first value in the list needs  to be initialized so that it can work
    if len(i_list[0]) == 0:
        i_list[0] = [i_register, i_value]
    else:
        # Loop through the list to check if register is already declared
        for i in range(len(i_list)):
            if (i_list[i][0] == i_register) and (i_value not in i_list[i]):
                i_list[i].append(i_value)
                break
        # If register is not declared then declare the register and value
        i_list.append([i_register, i_value])

    return i_list


# This function will create start the RISCV simulator and then step to the desired address,
# where it will get all the register values and store it in a list. The list will be returned
# to the calling function.
def get_registers_values_at_address(i_executable_file, i_address):
    i_reg_list = [[]]

    if isinstance(i_address, list):
        print("Please provide a string of address instead of a list")
        return None

    if i_address is None:
        print("Failed to provide address.")
        return None
    else:
        # Create an address that holds 64-bits
        while len(i_address) != 16:
            i_address = '0' + i_address

    # child is a process that triggers the spike simulator
    child = execute_spike_address(i_executable_file, i_address)

    while True:
        for i in range(len(registers.regular_registers)):
            # Get the register values
            cmd = "reg 0 " + registers.regular_registers[i]
            child.sendline(cmd)
            child.expect([cmd + '\r\n', pexpect.EOF])
            i_reg_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]

            # It is possible that we never call this function, which is why we can't get the registers for it.
            # In this case the reg_vale is '', so change it to None
            if i_reg_value == '':
                i_reg_value = None
            i_reg_list = store_register_values_in_list(i_reg_list, registers.regular_registers[i], i_reg_value)

        for i in range(len(registers.fp_registers)):
            # Get the register values
            cmd = "fregs 0 " + registers.fp_registers[i]
            child.sendline(cmd)
            child.expect([cmd + '\r\n', pexpect.EOF])
            i_reg_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
            i_reg_list = store_register_values_in_list(i_reg_list, registers.fp_registers[i], i_reg_value)

        # Step one instruction and then try to go again at the given address to see if this address is reached again
        cmd = 'r 1'
        child.sendline(cmd)
        child.expect([cmd + '\r\n', pexpect.EOF])

        cmd = 'until pc 0 ' + i_address
        child.sendline(cmd)
        child.expect([cmd + '\r\n', pexpect.EOF])

        cmd = 'pc 0 '
        child.sendline(cmd)
        child.expect([cmd + '\r\n', pexpect.EOF])
        pc = (child.readline()).decode("utf-8")
        if pc != '0x' + i_address + "\r\n":
            break

    sys.stdout.flush()
    return i_reg_list


def get_register_at_address(i_executable_file, i_address, i_register):
    if i_address is None:
        print("Failed to provide address.")
        return None

    child = execute_spike_address(i_executable_file, i_address)

    cmd = "reg 0 " + i_register
    child.sendline(cmd)
    child.expect([cmd + '\r\n', pexpect.EOF])
    i_reg_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
    return i_reg_value


def get_floating_point_register_at_address(i_executable_file, i_address, i_floating_register):
    if i_address is None:
        print("Failed to provide address.")
        return None

    child = execute_spike_address(i_executable_file, i_address)
    cmd = "fregs 0 " + i_floating_register
    child.sendline(cmd)
    child.expect([cmd + '\r\n', pexpect.EOF])
    i_reg_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
    return i_reg_value


# Get the memory data after reaching the specified address
def get_memory_data_at_address(i_executable_file, i_address, i_mem_location):
    if i_address is None:
        print("Failed to provide address.")
        return None

    if i_mem_location is None:
        print("Failed to provide memory address.")
        return None

    child = execute_spike_address(i_executable_file, i_address)
    cmd = "mem " + i_mem_location
    child.sendline(cmd)
    child.expect([cmd + '\r\n', pexpect.EOF])
    i_mem_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
    return i_mem_value


# Returns the data stored in the memory location
def get_memory_data(i_executable_file, i_mem_location):
    if i_mem_location is None:
        print("Failed to provide memory address.")
        return None

    child = execute_spike(i_executable_file)
    cmd = "mem " + i_mem_location
    child.sendline(cmd)
    child.expect([cmd + '\r\n', pexpect.EOF])
    i_mem_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
    return i_mem_value


def execute_spike_address(i_executable_file, i_address):
    if i_address is None:
        print("Failed to provide address.")
        return None

    cmd = '/opt/riscv/bin/spike -d /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + i_executable_file
    child = pexpect.spawn(cmd)
    child.expect([':', pexpect.EOF])

    # Proceed to the desired address
    child.sendline("until pc 0 " + i_address)
    child.expect(['\r\n', pexpect.EOF])
    return child


def execute_spike(i_executable_file):
    cmd = '/opt/riscv/bin/spike -d /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + i_executable_file
    child = pexpect.spawn(cmd)
    child.expect([':', pexpect.EOF])
    return child


def execute_spike_without_debug(i_executable_file):
    l_output = ''
    cmd = '/opt/riscv/bin/spike /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + i_executable_file
    child = pexpect.spawn(cmd)
    child.expect(['\r\n', pexpect.EOF])

    l_last_return = 'XXXX'
    l_return = (child.readline()).decode("utf-8")
    while (l_return != '') or (l_last_return != l_return):
        l_output += l_return
        l_last_return = l_return
        l_return = (child.readline()).decode("utf-8")


    return l_output


# Gets the execution time from the executable by read keyword
# "Total Execution time:". Returns None if the keyword is not present
def execute_spike_get_execution_time(i_executable_file):
    l_return = None
    cmd = '/opt/riscv/bin/spike /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + i_executable_file
    child = pexpect.spawn(cmd)

    while l_return is not '':
        child.expect(['\r\n', pexpect.EOF])
        l_return = (child.readline()).decode("utf-8")
        if "Total Execution time:" in l_return:
            return l_return.split("Total Execution time:")[-1].split(" ")[1]
    return None
