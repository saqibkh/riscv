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

    cmd = '/opt/riscv/bin/spike -d /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + i_executable_file
    child = pexpect.spawn(cmd)
    child.expect([':', pexpect.EOF])

    # Proceed to the desired address
    child.sendline("until pc 0 " + i_address)
    child.expect(['\r\n', pexpect.EOF])

    for i in range(len(registers.regular_registers)):
        # Get the register values
        cmd = "reg 0 " + registers.regular_registers[i]
        child.sendline(cmd)
        child.expect([cmd + '\r\n', pexpect.EOF])
        i_reg_value = ((child.readline()).decode("utf-8")).split("\r\n")[0]
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
