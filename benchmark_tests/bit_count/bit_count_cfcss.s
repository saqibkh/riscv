	.file	"bit_count.c"
	.option nopic
	.attribute arch, "rv64i2p0_m2p0_a2p0_f2p0_d2p0_c2p0"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.align	1
	.globl	countSetBits
	.type	countSetBits, @function
countSetBits:
	xori	s11,s11,8
	li	t6,3
	bne	s11,t6,100
	addi	sp,sp,-48
	sd	s0,40(sp)
	addi	s0,sp,48
	mv	a5,a0
	sw	a5,-36(s0)
	sw	zero,-20(s0)
	li	s10,0
	j	.L2
.L3:
	xori	s11,s11,8
	li	t6,10
	bne	s11,t6,100
	lw	a5,-36(s0)
	andi	a5,a5,1
	sext.w	a5,a5
	lw	a4,-20(s0)
	addw	a5,a4,a5
	sw	a5,-20(s0)
	lw	a5,-36(s0)
	srliw	a5,a5,1
	li	s10,9
	sw	a5,-36(s0)
.L2:
	xor	s11,s11,s10
	xori	s11,s11,1
	li	t6,2
	bne	s11,t6,100
	lw	a5,-36(s0)
	sext.w	a5,a5
	li	s10,0
	li	s10,0
	bne	a5,zero,.L3
	xori	s11,s11,7
	li	t6,5
	bne	s11,t6,100
	lw	a5,-20(s0)
	mv	a0,a5
	ld	s0,40(sp)
	addi	sp,sp,48
	li	s10,0
	jr	ra
	.size	countSetBits, .-countSetBits
	.section	.rodata
	.align	3
.LC0:
	.string	"%d"
	.text
	.align	1
	.globl	main
	.type	main, @function
main:
	xori	s11,s11,11
	li	t6,11
	bne	s11,t6,100
	addi	sp,sp,-32
	sd	ra,24(sp)
	sd	s0,16(sp)
	addi	s0,sp,32
	li	a5,9
	sw	a5,-20(s0)
	lw	a5,-20(s0)
	mv	a0,a5
	li	s10,0
	call	countSetBits
	xori	s11,s11,13
	li	t6,8
	bne	s11,t6,100
	mv	a5,a0
	sext.w	a5,a5
	mv	a1,a5
	lui	a5,%hi(.LC0)
	addi	a0,a5,%lo(.LC0)
	li	s10,0
	call	printf
	xori	s11,s11,15
	li	t6,7
	bne	s11,t6,100
	li	a5,0
	mv	a0,a5
	ld	ra,24(sp)
	ld	s0,16(sp)
	addi	sp,sp,32
	jr	ra
	.size	main, .-main
	.ident	"GCC: (GNU) 9.2.0"
