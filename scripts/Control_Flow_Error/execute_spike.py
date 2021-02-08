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


# This function will create start the RISCV simulator and then step to the desired address,
# where it will get all the register values and store it in a list. The list will be returned
# to the calling function.
def get_registers_values_at_address(i_executable_file, i_address):
    i_reg_list = []

    if isinstance(i_address, list):
        print("Please provide a string of address instead of a list")
        return None

    if i_address is None:
        print("Failed to provide address.")
        return None

    # child is a process that triggers the spike simulator
    child = execute_spike_address(i_executable_file, i_address)

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
        i_reg_list.append([registers.regular_registers[i], i_reg_value])

    for i in range(len(registers.fp_registers)):
        # Get the register values
        cmd = "fregs 0 " + registers.fp_registers[i]
        child.sendline(cmd)
        child.expect([cmd + '\r\n', pexpect.EOF])
        i_reg_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
        i_reg_list.append([registers.fp_registers[i], i_reg_value])

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
