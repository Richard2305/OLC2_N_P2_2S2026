 .global _start
 .section .rodata
message: .ascii "OxigenNative ARM64\n"
 .equ message_length, . - message
 .text
_start:
 mov x0, #1
 adr x1, message
 mov x2, #message_length
 mov x8, #64
 svc #0
 mov x0, #0
 mov x8, #93
 svc #0
