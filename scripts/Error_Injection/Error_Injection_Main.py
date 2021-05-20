#!/usr/bin/python


import sys
import logging
import time
import string
import datetime
import getopt
import random
import subprocess
import os
from os import path

# ---------Set sys.path for CFE_MAIN execution---------------------------------------
full_path = os.path.abspath(os.path.dirname(sys.argv[0])).split('riscv')[0]
sys.path.append(full_path)
# Walk path and append to sys.path
for root, dirs, files in os.walk(full_path):
    for dir in dirs:
        sys.path.append(os.path.join(root, dir))

import compileUtil
import utils
import instructions
import sim_logging
import helper


def usage():
    print("Usage: Please provide the absolute path for a .s program that matches <file>.s")
    print(
        "Example ./Error_Injection.py src/dir/test/bit_count.s")


def main(argv):
    l_test_count = 1000
    simlog = sim_logging.SIMLOG()

    if len(sys.argv) != 2:
        usage()
        sys.exit()

    simlog.info("Processing file: " + argv[0])
    sys.stdout.flush()

    file_s = argv[0]
    utils.checkFileExists(file_s)
    ''' Create an assembly file and an objdump file from the C program file provided to us '''
    compileUtil.compile_s(file_s)
    file_objdump = file_s.split(".s")[0] + ".objdump"

    l_object = helper.Error_Injection(file_s, file_objdump, simlog=simlog)

    for i in range(l_test_count):
        l_object.inject_error_return_result(i)
        # Print msg to let user know that we are alive
        if (i % 10) == 0:
            print("Still processing logs. Now at counter " + str(i))

    simlog.info("Total number of error injection tests: " + str(l_test_count))
    simlog.info("Total number of error injection tests that passed: " + str(l_object.result_passed))
    simlog.info("Total number of error injection tests that produced incorrect result: "+str(l_object.result_incorrect))
    simlog.info("Total number of error injection tests that went to correct error handler: " + str(l_object.result_exception_handler))
    simlog.info("Total number of error injection tests that went to incorrect error handler: " + str(l_object.result_exception))
    sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1:])
