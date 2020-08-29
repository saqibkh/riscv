#!/usr/bin/env python

import os
import pexpect
import subprocess
import tempfile
import testlib
import unittest
import sys
import time

def compile(*args):
    """Compile a single .c file into a binary."""
    dst = os.path.splitext(args[0])[0]
    cc = os.path.expandvars("/opt/riscv64/bin/riscv64-unknown-elf-gcc")
    cmd = [cc, "-g", "-O", "-o", dst]
    for arg in args:
        found = find_file(arg)
        if found:
            cmd.append(found)
        else:
            cmd.append(arg)
    cmd = " ".join(cmd)
    result = os.system(cmd)
    assert result == 0, "%r failed" % cmd
    return dst

def unused_port():
    # http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python/2838309#2838309
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    port = s.getsockname()[1]
    s.close()
    return port

def find_file(path):
    for directory in (os.getcwd(), os.path.dirname(testlib.__file__)):
        fullpath = os.path.join(directory, path)
        if os.path.exists(fullpath):
            return fullpath
    return None


class Spike(object):

    def __init__(self, i_binary):
        """Launch spike. Return tuple of its process and the port it's running on."""
        self.binary = i_binary

    def generate_logs(self):
        """Generates the stdout from running a binary."""
        fout = open(self.binary + "_logs", "w+")
        cmd = 'spike /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + self.binary
        self.child = pexpect.spawn(cmd, logfile=fout)
        self.child.expect(['%', pexpect.EOF])
        fout.close()

    def generate_extended_logs(self):
        """Generates the instruction traces from running a binary."""
        fout = open(self.binary + "_extended_logs", "w+")
        cmd = 'spike -l /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + self.binary
        self.child = pexpect.spawn(cmd, logfile=fout, timeout=3600) #3600s==60min
        self.child.expect(['%', pexpect.EOF])
        fout.close()


    def generate_extended_debug_logs(self):
        """Generates instruction traces along with SPR and GPR data."""
        # Command: spike -d $(which pk) <file>
        fout = open(self.binary + "_extended_debug_logs", "w+")
        cmd = 'spike -d /opt/riscv/toolchain/riscv64-unknown-linux-gnu/bin/pk ' + self.binary
        self.child = pexpect.spawn(cmd, logfile=fout)
        self.child.expect([':', pexpect.EOF])

        try:
            while(1):
                self.get_pc()
                self.get_registers()
                self.step_one_instruction()
        except Exception as e:
            print "error"
            fout.close()

    def wait(self):
        self.child.expect(['\r\n', pexpect.EOF])
        self.child.expect(['\r\n', pexpect.EOF])
        self.child.expect([':', pexpect.EOF])

    def get_registers(self):
        self.child.sendline("reg 0 zero")
        self.wait()
        self.child.sendline("reg 0 ra")
        self.wait()
        self.child.sendline("reg 0 sp")
        self.wait()
        self.child.sendline("reg 0 gp")
        self.wait()
        self.child.sendline("reg 0 tp")
        self.wait()
        self.child.sendline("reg 0 t0")
        self.wait()
        self.child.sendline("reg 0 t1")
        self.wait()
        self.child.sendline("reg 0 t2")
        self.wait()
        self.child.sendline("reg 0 t3")
        self.wait()
        self.child.sendline("reg 0 t4")
        self.wait()
        self.child.sendline("reg 0 t5")
        self.wait()
        self.child.sendline("reg 0 t6")
        self.wait()
        self.child.sendline("reg 0 s0")
        self.wait()
        self.child.sendline("reg 0 s1")
        self.wait()
        self.child.sendline("reg 0 s2")
        self.wait()
        self.child.sendline("reg 0 s3")
        self.wait()
        self.child.sendline("reg 0 s4")
        self.wait()
        self.child.sendline("reg 0 s5")
        self.wait()
        self.child.sendline("reg 0 s6")
        self.wait()
        self.child.sendline("reg 0 s7")
        self.wait()
        self.child.sendline("reg 0 s8")
        self.wait()
        self.child.sendline("reg 0 s9")
        self.wait()
        self.child.sendline("reg 0 s10")
        self.wait()
        self.child.sendline("reg 0 s11")
        self.wait()
        self.child.sendline("reg 0 a0")
        self.wait()
        self.child.sendline("reg 0 a1")
        self.wait()
        self.child.sendline("reg 0 a2")
        self.wait()
        self.child.sendline("reg 0 a3")
        self.wait()
        self.child.sendline("reg 0 a4")
        self.wait()
        self.child.sendline("reg 0 a5")
        self.wait()
        self.child.sendline("reg 0 a6")
        self.wait()
        self.child.sendline("reg 0 a7")
        self.wait()
        self.child.sendline("reg 0 a5")
        self.wait()


    def get_pc(self):
        self.child.sendline("pc 0")
        self.wait()

    def step_one_instruction(self):
        self.child.sendline("r 1")
        self.wait()




