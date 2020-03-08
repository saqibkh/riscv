	.global main
        .text

main:
	add r1, r1, r3
	ld  r2, r3
	str r1, r2
	mov r2, r0
	sub r0, r1
	cmp r3, r2
	ble main
