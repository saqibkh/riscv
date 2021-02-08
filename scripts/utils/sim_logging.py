#!/usr/bin/python

import logging
import time
import string
import datetime


class SIMLOG:
    def __init__(self, debug=False, error=True, info=True, warning=True):
        self.debug_log = debug
        self.error_log = error
        self.info_log = info
        self.warning = warning

    def debug(self, i_msg):
        if self.debug_log:
            print("DEBUG LOG: " + str(i_msg))

    def error(self, i_msg):
        if self.error_log:
            print("ERROR LOG: " + str(i_msg))

    def info(self, i_msg):
        if self.info_log:
            print("INFO LOG: " + str(i_msg))

    def warning(self, i_msg):
        if self.info_warning:
            print("INFO WARNING: " + str(i_msg))