#!/usr/bin/env python

########################################################################################################
branch_unconditional_instructions = ['b', 'j', 'jr', 'jal', 'ret', 'call', 'jalr'
                                     'c.jr', 'c.j', 'c.jalr']
branch_conditional_instructions = ['bne', 'beq', 'blt', 'bge', 'bnez', 'ble', 'bltz', 'bgtz', 'bgt', 'blez', 'beqz',
                                   'bltu', 'bgeu', 'bgez',
                                   'c.beqz', 'c.bnez']
branch_instructions = branch_unconditional_instructions + branch_conditional_instructions
########################################################################################################


########################################################################################################
arithmetic_instructions = ["add", "addi", "sub", "auipc", "lui", "andi", "addiw",
                           "li", "mv",
                           "c.add", "c.addi", "c.sub", "c.addiw", "c.addi16sp", "c.andi", "c.addi4spn",
                           "c.li", "c.mv", "c.lui"]
logical_instructions = ["xor", "xori", "or", "ori", "and", "andi", "not",
                        "c.or", "c.and"]
shift_instructions = ["sll", "slli", "srl", "srli", "sra", "srai", "sllw", "slliw", "srliw",
                      "c.slli", "c.srli"]
all_arithmetic_instructions = arithmetic_instructions + logical_instructions + shift_instructions
########################################################################################################


########################################################################################################
load_instructions = ["lb", "lh", "lw", "lbu", "lhu", "ld",
                     'c.ld', 'c.ldsp', 'c.lw']
store_instructions = ["sb", "sh", "sw", "sd",
                      "c.sd", "c.sdsp", "c.sw"]
load_store_instructions = load_instructions + store_instructions
########################################################################################################


########################################################################################################
# CSR Access (RV Privileged Instructions)
csr_instructions = ['csrrw', 'csrrs', 'csrrc', 'csrrwi', 'csrrsi', 'csrrci']
change_level = ['ecall', 'ebreak', 'eret']
mmu_instruction = ['fence']
extra_instructions = csr_instructions + change_level + mmu_instruction
########################################################################################################


all_instructions = all_arithmetic_instructions + branch_instructions + load_store_instructions + extra_instructions
