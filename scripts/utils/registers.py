#!/usr/bin/env python

# The following are registers x0->x31, with the ABI Names
hard_wire_zero = ['zero']
return_address = ['ra']
stack_pointer = ['sp']
global_pointer = ['gp']
thread_pointer = ['tp']
temporaries = ['t0', 't1', 't2']
saved_register_frame_pointer = ['s0'] #Both s0 and fp are the same register ==> x8
function_arg_return_values = ['a0', 'a1']
function_arguments = ['a2', 'a3', 'a4', 'a5', 'a6', 'a7']
saved_registers = ['s2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11']
temporaries = ['t3', 't4', 't5', 't6']

regular_registers = hard_wire_zero + return_address + stack_pointer + global_pointer + thread_pointer + temporaries \
                    + saved_register_frame_pointer + function_arg_return_values + function_arguments + saved_registers \
                    + temporaries

# These are floating point registers f0->f31 with the ABI Names
fp_temporaries = ['ft0', 'ft1', 'ft2', 'ft3', 'ft4', 'ft5', 'ft6', 'ft7', 'ft8', 'ft9', 'ft10', 'ft11']
fp_saved_registers = ['fs0', 'fs1']
fp_arguments_return_values = ['fa0', 'fa1']
fp_arguments = ['fa2', 'fa3', 'fa4', 'fa5', 'fa6', 'fa7']
fp_saved_registers = ['fs2', 'fs3', 'fs4', 'fs5', 'fs6', 'fs7', 'fs8', 'fs9', 'fs10', 'fs11']

fp_registers = fp_temporaries + fp_saved_registers + fp_arguments_return_values + fp_arguments + fp_saved_registers


all_registers = regular_registers + fp_registers


# This list will be used for DFE techniques in place of duplicate registers
possible_duplicate_registers = ['t3', 't4', 't5', 's2', 's3', 's4', 's5', 's6', 's7']
