// Linux AArch64 runtime, without libc. Strings: [u64 byte length][UTF-8 bytes].
// Public helpers use x0/x1 arguments and preserve x19-x29; SP remains aligned.
.text
ox_write:
    ldr x2, [x0]
    add x1, x0, #8
    b ox_write_bytes
ox_write_bytes:
    // Linux write may return a partial count or EINTR. Advance until exhausted.
    cbz x2, .Lwrite_done
.Lwrite_again:
    mov x0, #1
    mov x8, #64
    svc #0
    cmn x0, #4
    b.eq .Lwrite_again
    cmp x0, #0
    b.le ox_io_error
    add x1, x1, x0
    subs x2, x2, x0
    b.ne .Lwrite_again
.Lwrite_done:
    ret

ox_print_i32:
    sxtw x0, w0
ox_print_int:
    sub sp, sp, #48
    add x1, sp, #48
    mov x2, #0
    mov x10, #10
    cmp x0, #0
    cset x11, lt
    cneg x9, x0, lt
.Lint_digit:
    udiv x12, x9, x10
    msub x13, x12, x10, x9
    add w13, w13, #48
    strb w13, [x1, #-1]!
    add x2, x2, #1
    mov x9, x12
    cbnz x9, .Lint_digit
    cbz x11, .Lint_write
    mov w13, #45
    strb w13, [x1, #-1]!
    add x2, x2, #1
.Lint_write:
    stp x29, x30, [sp, #-16]!
    bl ox_write_bytes
    ldp x29, x30, [sp], #16
    add sp, sp, #48
    ret

ox_print_char:
    sub sp, sp, #16
    mov x1, sp
    cmp w0, #128
    b.hs .Lchar_two
    strb w0, [sp]
    mov x2, #1
    b .Lchar_write
.Lchar_two:
    and w9, w0, #63
    orr w9, w9, #128
    cmp w0, #2048
    b.hs .Lchar_three
    lsr w10, w0, #6
    orr w10, w10, #192
    strb w10, [sp]
    strb w9, [sp, #1]
    mov x2, #2
    b .Lchar_write
.Lchar_three:
    lsr w10, w0, #6
    and w10, w10, #63
    orr w10, w10, #128
    mov w12, #0xffff
    cmp w0, w12
    b.hi .Lchar_four
    lsr w11, w0, #12
    orr w11, w11, #224
    strb w11, [sp]
    strb w10, [sp, #1]
    strb w9, [sp, #2]
    mov x2, #3
    b .Lchar_write
.Lchar_four:
    lsr w11, w0, #12
    and w11, w11, #63
    orr w11, w11, #128
    lsr w12, w0, #18
    orr w12, w12, #240
    strb w12, [sp]
    strb w11, [sp, #1]
    strb w10, [sp, #2]
    strb w9, [sp, #3]
    mov x2, #4
.Lchar_write:
    stp x29, x30, [sp, #-16]!
    bl ox_write_bytes
    ldp x29, x30, [sp], #16
    add sp, sp, #16
    ret

// First-stage decimal formatter: six fractional digits, trailing zeros removed.
// Rejects nonfinite numbers and magnitudes >= 1e12 rather than printing corrupt data.
ox_print_float:
    stp x29, x30, [sp, #-64]!
    fmov d0, x0
    fcmp d0, d0
    b.vs ox_float_error
    fabs d0, d0
    ldr x9, =0x426d1a94a2000000 // 1e12
    fmov d1, x9
    fcmp d0, d1
    b.ge ox_float_error
    str x0, [sp, #16]
    fcvtzu x9, d0
    ucvtf d1, x9
    fsub d0, d0, d1
    ldr x10, =1000000
    ucvtf d1, x10
    fmul d0, d0, d1
    fcvtnu x11, d0
    cmp x11, x10
    b.ne .Lfloat_save
    add x9, x9, #1
    mov x11, #0
.Lfloat_save:
    stp x9, x11, [sp, #24]
    tbz x0, #63, .Lfloat_integer
    mov x0, #45
    bl ox_print_char
.Lfloat_integer:
    ldr x0, [sp, #24]
    bl ox_print_int
    mov x0, #46
    bl ox_print_char
    ldr x9, [sp, #32]
    add x1, sp, #54
    mov x10, #10
    mov x12, #6
.Lfloat_digit:
    udiv x11, x9, x10
    msub x13, x11, x10, x9
    add w13, w13, #48
    strb w13, [x1, #-1]!
    mov x9, x11
    subs x12, x12, #1
    b.ne .Lfloat_digit
    mov x2, #6
.Lfloat_trim:
    cmp x2, #1
    b.eq .Lfloat_write
    sub x9, x2, #1
    ldrb w10, [x1, x9]
    cmp w10, #48
    b.ne .Lfloat_write
    sub x2, x2, #1
    b .Lfloat_trim
.Lfloat_write:
    bl ox_write_bytes
    ldp x29, x30, [sp], #64
    ret

// Allocate x0 payload bytes plus its length header in a bounded bump heap.
ox_alloc:
    ldr x9, =1048560
    cmp x0, x9
    b.hi ox_heap_error
    add x10, x0, #15
    and x10, x10, #-8
    adrp x11, ox_heap_next
    add x11, x11, :lo12:ox_heap_next
    ldr x12, [x11]
    add x13, x12, x10
    adrp x14, ox_heap_end
    add x14, x14, :lo12:ox_heap_end
    cmp x13, x14
    b.hi ox_heap_error
    str x13, [x11]
    str x0, [x12]
    mov x0, x12
    ret

ox_clone:
    adrp x1, ox_empty
    add x1, x1, :lo12:ox_empty
    b ox_concat
ox_concat:
    stp x29, x30, [sp, #-48]!
    stp x0, x1, [sp, #16]
    ldr x9, [x0]
    ldr x10, [x1]
    add x0, x9, x10
    bl ox_alloc
    ldp x1, x2, [sp, #16]
    ldr x9, [x1], #8
    ldr x10, [x2], #8
    add x11, x0, #8
.Lconcat_first:
    cbz x9, .Lconcat_second
    ldrb w12, [x1], #1
    strb w12, [x11], #1
    sub x9, x9, #1
    b .Lconcat_first
.Lconcat_second:
    cbz x10, .Lconcat_done
    ldrb w12, [x2], #1
    strb w12, [x11], #1
    sub x10, x10, #1
    b .Lconcat_second
.Lconcat_done:
    ldp x29, x30, [sp], #48
    ret

// x0 string pointer, x1 signed repetition count.
ox_repeat:
    stp x29, x30, [sp, #-48]!
    cmp x1, #0
    csel x1, x1, xzr, gt
    stp x0, x1, [sp, #16]
    ldr x9, [x0]
    umulh x10, x9, x1
    cbnz x10, ox_heap_error
    mul x0, x9, x1
    bl ox_alloc
    ldp x1, x2, [sp, #16]
    ldr x9, [x1], #8
    add x10, x0, #8
    cbz x9, .Lrepeat_done
.Lrepeat_outer:
    cbz x2, .Lrepeat_done
    mov x11, x9
    mov x12, x1
.Lrepeat_inner:
    ldrb w13, [x12], #1
    strb w13, [x10], #1
    subs x11, x11, #1
    b.ne .Lrepeat_inner
    sub x2, x2, #1
    b .Lrepeat_outer
.Lrepeat_done:
    ldp x29, x30, [sp], #48
    ret

// Lexicographical comparison, returning -1, 0 or 1.
ox_compare_strings:
    ldr x9, [x0], #8
    ldr x10, [x1], #8
.Lcompare_next:
    cbz x9, .Lcompare_left_end
    cbz x10, .Lcompare_greater
    ldrb w11, [x0], #1
    ldrb w12, [x1], #1
    cmp w11, w12
    b.lo .Lcompare_less
    b.hi .Lcompare_greater
    sub x9, x9, #1
    sub x10, x10, #1
    b .Lcompare_next
.Lcompare_left_end:
    cbnz x10, .Lcompare_less
    mov x0, #0
    ret
.Lcompare_less:
    mov x0, #-1
    ret
.Lcompare_greater:
    mov x0, #1
    ret

ox_div_zero:
    adrp x1, ox_div_message
    add x1, x1, :lo12:ox_div_message
    mov x2, #ox_div_message_length
    b ox_fail
ox_heap_error:
    adrp x1, ox_heap_message
    add x1, x1, :lo12:ox_heap_message
    mov x2, #ox_heap_message_length
    b ox_fail
ox_float_error:
    adrp x1, ox_float_message
    add x1, x1, :lo12:ox_float_message
    mov x2, #ox_float_message_length
    b ox_fail
ox_io_error:
    adrp x1, ox_io_message
    add x1, x1, :lo12:ox_io_message
    mov x2, #ox_io_message_length
ox_fail:
    mov x0, #2
    mov x8, #64
    svc #0
    mov x0, #1
    mov x8, #93
    svc #0

.section .rodata
.balign 8
ox_empty: .quad 0
ox_div_message: .ascii "División entre cero.\n"
.equ ox_div_message_length, . - ox_div_message
ox_heap_message: .ascii "Heap agotado.\n"
.equ ox_heap_message_length, . - ox_heap_message
ox_float_message: .ascii "Impresión f64 fuera del rango admitido (magnitud < 1e12).\n"
.equ ox_float_message_length, . - ox_float_message
ox_io_message: .ascii "Error de escritura.\n"
.equ ox_io_message_length, . - ox_io_message
.data
.balign 8
ox_heap_next: .quad ox_heap
.bss
.balign 16
ox_heap: .skip 1048576
ox_heap_end:
.section .note.GNU-stack,"",@progbits
