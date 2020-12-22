#!/usr/bin/env python


branch_unconditional_instructions = ['b', 'j', 'jr', 'jal', 'ret', 'call']
branch_conditional_instructions = ['bne', 'beq', 'blt', 'bge', 'bnez', 'ble', 'bltz', 'bgtz', 'bgt', 'blez', 'beqz']
branch_instructions = branch_unconditional_instructions + branch_conditional_instructions
