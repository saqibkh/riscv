#!/usr/bin/python

import sys
import logging
import time
import string
import datetime
import random
import subprocess
import utils
from os import path


# Check whether the input number is a prime number or not
def isPrime(i_num):
    for i in range(2, i_num):
        if i_num % i == 0:
            return False
    return True


# Checks whether i_num exists within the i_list
def isInList(i_list, i_num):
    for i in range(len(i_list)):
        if i_list[i] == i_num:
            return True
    return False


class ECCA:
    def __init__(self, i_map):
        self.original_map = i_map

        # Compile time signature (BID)
        # BID us a unique compile time signature and has to be a prime number larger than 2
        self.BID = []

        # Compile time signatures of the successor blocks of the current basic block.
        # Note that in case of only 1 successor block the NEXT2 entry will be NONE
        self.NEXT1 = [None] * len(i_map.blocks)
        self.NEXT2 = [None] * len(i_map.blocks)

        random.seed(a=1, version=2)
        self.generate_BID()

        # Now get the compile time signatures of the successor blocks
        self.generateSuccessorSig()

        return 0

    def generateSuccessorSig(self):
        for i in range(len(self.original_map.blocks)):

            next_block_1_id = None
            next_block_2_id = None

            # Not all blocks have successor blocks so wrap it with try/except statements
            try:
                next_block_1_id = self.original_map.blocks[i].next_block_id[0]
            except:
                print('Unable to find the successor block')

            try:
                next_block_2_id = self.original_map.blocks[i].next_block_id[1]
            except:
                print('Unable to find the successor block')

            if next_block_1_id != None:
                self.NEXT1[i] = self.BID[next_block_1_id]

            if next_block_2_id != None:
                self.NEXT2[i] = self.BID[next_block_2_id]

    def generate_BID(self):
        # loop until we fill the compile time variable list
        while len(self.BID) != len(self.original_map.blocks):

            # Get a random number
            i_num = random.sample(range(3, (len(self.BID) * 4) + 10), 1)[0]

            # Check if it is prime number
            if isPrime(i_num):
                # Check if the number already exists in the list. If not, then add to the list
                if not isInList(self.BID, i_num):
                    self.BID.append(i_num)
