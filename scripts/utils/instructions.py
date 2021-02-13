#!/usr/bin/env python

########################################################################################################
branch_unconditional_instructions = ['b', 'j', 'jr', 'jal', 'ret', 'call', 'jalr',
                                     'c.jr', 'c.j', 'c.jalr']
branch_conditional_instructions = ['bne', 'beq', 'blt', 'bge', 'bnez', 'ble', 'bltz', 'bgtz', 'bgt', 'blez', 'beqz',
                                   'bltu', 'bgeu', 'bgez',
                                   'c.beqz', 'c.bnez']
branch_instructions = branch_unconditional_instructions + branch_conditional_instructions
########################################################################################################


########################################################################################################
arithmetic_instructions = ["add", "addi", "sub", "auipc", "lui", "andi", "addiw", "addw", "subw",
                           "remu", "rem", "mul", "mulh", "div", "divu", "remw", "remuw", "divw", "divuw", "mulw",
                           "li", "mv",
                           "c.add", "c.addi", "c.sub", "c.addiw", "c.addi16sp", "c.andi", "c.addi4spn", "c.subw",
                           "c.li", "c.mv", "c.lui", "c.addw",
                           'amoadd.w', 'sext.w']
logical_instructions = ["xor", "xori", "or", "ori", "and", "andi", "not",
                        "c.or", "c.and", "c.xor"]
shift_instructions = ["sll", "slli", "srl", "srli", "sra", "srai", "sllw", "slliw", "srliw", "sraiw",
                      "c.slli", "c.srli"]
swap_instructions = ['amoswap.w']
compare_instructions = ['slt', 'slti', 'sltu', 'sltiu', 'seqz', 'snez', 'sltz', 'sgtz']
all_arithmetic_instructions = arithmetic_instructions + logical_instructions + shift_instructions + \
                              swap_instructions + compare_instructions
########################################################################################################


########################################################################################################
load_instructions = ["lb", "lh", "lw", "lbu", "lhu", "ld", "lwu",
                     'c.ld', 'c.ldsp', 'c.lw', 'c.lwsp',
                     'lr.w', 'lr.d']
store_instructions = ["sb", "sh", "sw", "sd",
                      "c.sd", "c.sdsp", "c.sw", "c.swsp",
                      'sc.w', 'sc.d']
load_store_instructions = load_instructions + store_instructions
########################################################################################################


########################################################################################################
# CSR Access (RV Privileged Instructions)
csr_instructions = ['csrr', 'csrw', 'csrrw', 'csrrs', 'csrrc', 'csrrwi', 'csrrsi', 'csrrci', 'csrwi']
change_level = ['ecall', 'ebreak', 'eret']
mmu_instruction = ['fence', 'sfence.vma', 'fence.i']
other_instructions = ['c.nop', 'sret', 'mret']
extra_instructions = csr_instructions + change_level + mmu_instruction + other_instructions
########################################################################################################

########################################################################################################
floating_point_instructions = ['fmv.w.x']
floating_point_arithmetic = ['fcvt.d.lu', 'fdiv.d', 'fdiv.s', 'fcvt.s.l', 'fcvt.s.w', 'fmul.s', 'fmul.d',
                             'fcvt.l.s', 'fsub.s', 'fadd.s', 'fcvt.d.s', 'fmv.x.d', 'fcvt.s.d']
floating_point_comparision = ['flt.s', 'fle.s']
floating_point_load = ['fld', 'flw']
floating_point_store = ['fsd', 'fsw']
########################################################################################################


all_instructions = all_arithmetic_instructions + branch_instructions + load_store_instructions +\
                   extra_instructions + floating_point_instructions

reg_modified_instructions = all_arithmetic_instructions + load_instructions + branch_unconditional_instructions + \
                            floating_point_load + floating_point_arithmetic + floating_point_comparision
reg_unmodified_instructions = store_instructions + branch_conditional_instructions + other_instructions + \
                              floating_point_store
