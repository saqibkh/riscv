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
                      "c.slli", "c.srli", "c.srai"]
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
floating_point_move = ['fmv.h.x', 'fmv.s.x', 'fmv.d.x', 'fmv.q.x',
                       'fmv.x.h', 'fmv.x.s', 'fmv.x.d', 'fmv.x.q',
                       'fmv.w.x']

floating_point_convert = ['fcvt.h.w', 'fcvt.s.w', 'fcvt.d.w', 'fcvt.q.w',
                          'fcvt.h.l', 'fcvt.s.l', 'fcvt.d.l', 'fcvt.q.l',
                          'fcvt.h.t', 'fcvt.s.t', 'fcvt.d.t', 'fcvt.q.t',
                          'fcvt.h.wu', 'fcvt.s.wu', 'fcvt.d.wu', 'fcvt.q.wu',
                          'fcvt.h.lu', 'fcvt.s.lu', 'fcvt.d.lu', 'fcvt.q.lu',
                          'fcvt.h.tu', 'fcvt.s.tu', 'fcvt.d.tu', 'fcvt.q.tu',
                          'fcvt.w.h', 'fcvt.w.s', 'fcvt.w.d', 'fcvt.w.q',
                          'fcvt.l.h', 'fcvt.l.s', 'fcvt.l.d', 'fcvt.l.q',
                          'fcvt.t.h', 'fcvt.t.s', 'fcvt.t.d', 'fcvt.t.q',
                          'fcvt.wu.h', 'fcvt.wu.s', 'fcvt.wu.d', 'fcvt.wu.q',
                          'fcvt.lu.h', 'fcvt.lu.s', 'fcvt.lu.d', 'fcvt.lu.q',
                          'fcvt.tu.h', 'fcvt.tu.s', 'fcvt.tu.d', 'fcvt.tu.q',
                          'fcvt.d.s', 'fcvt.s.d']
floating_point_arithmetic = ['fadd.s', 'fadd.d', 'fadd.q',
                             'fsub.s', 'fsub.d', 'fsub.q',
                             'fmul.s', 'fmul.d', 'fmul.q',
                             'fdiv.s', 'fdiv.d', 'fdiv.q',
                             'fsqrt.s', 'fsqrt.d', 'fsqrt.q',
                             'fmadd.s', 'fmadd.d', 'fmadd.q',
                             'fmsub.s', 'fmsub.d', 'fmsub.q',
                             'fnmadd.s', 'fnmadd.d', 'fnmadd.q',
                             'fnmsub.s', 'fnmsub.d', 'fnmsub.q']
floating_point_inject_sign = ['fsgnj.s', 'fsgnj.d', 'fsgnj.q',
                              'fsgnjn.s', 'fsgnjn.d', 'fsgnjn.q',
                              'fsgnjx.s', 'fsgnjx.d', 'fsgnjx.q']
floating_point_min_max = ['fmin.s', 'fmin.d', 'fmin.q',
                          'fmax.s', 'fmax.d', 'fmax.q']
floating_point_compare = ['feq.s', 'feq.d', 'feq.q',
                          'flt.s', 'flt.d', 'flt.q',
                          'fle.s', 'fle.d', 'fle.q']
all_floating_point_arithmetic = floating_point_move + floating_point_convert + floating_point_arithmetic + \
                                floating_point_inject_sign + floating_point_min_max + floating_point_compare

floating_point_load = ['flw', 'fld', 'flq',
                       'c.fld']
floating_point_store = ['fsw', 'fsd', 'fsq']
floating_point_load_store = floating_point_load + floating_point_store
########################################################################################################

all_instructions = all_arithmetic_instructions + branch_instructions + load_store_instructions +\
                   extra_instructions + all_floating_point_arithmetic + floating_point_load_store

reg_modified_instructions = all_arithmetic_instructions + load_instructions + branch_unconditional_instructions + \
                            all_floating_point_arithmetic + floating_point_load
reg_unmodified_instructions = store_instructions + branch_conditional_instructions + other_instructions + \
                              floating_point_store
