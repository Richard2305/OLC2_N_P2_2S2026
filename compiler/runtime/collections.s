// Arrays/slices use [u64 length][u64 data pointer]; nested fixed arrays are flat.
.text
// x0 = element count, x1 = stride in bytes.
ox_array_new:
    stp x29, x30, [sp, #-32]!
    str x0, [sp, #16]
    umulh x9, x0, x1
    cbnz x9, ox_heap_error
    mul x0, x0, x1
    adds x0, x0, #8
    b.cs ox_heap_error
    bl ox_alloc
    ldr x9, [sp, #16]
    str x9, [x0]
    add x9, x0, #16
    str x9, [x0, #8]
    ldp x29, x30, [sp], #32
    ret

// View descriptor only: x0 data pointer, x1 element count.
ox_array_view:
    stp x29, x30, [sp, #-32]!
    stp x0, x1, [sp, #16]
    mov x0, #8
    bl ox_alloc
    ldp x9, x10, [sp, #16]
    stp x10, x9, [x0]
    ldp x29, x30, [sp], #32
    ret

// Flat value copy preserving both the descriptor and its source data.
ox_array_clone:
    stp x29, x30, [sp, #-48]!
    stp x0, x1, [sp, #16]
    ldr x0, [x0]
    bl ox_array_new
    str x0, [sp, #32]
    ldr x1, [x0, #8]
    ldp x0, x2, [sp, #16]
    ldr x9, [x0]
    mul x2, x2, x9
    ldr x0, [x0, #8]
    bl ox_copy
    ldr x0, [sp, #32]
    ldp x29, x30, [sp], #48
    ret

// memmove, x0 source x1 destination x2 byte count. Elements may overlap.
ox_copy:
    cbz x2, .Lcopy_done
    cmp x1, x0
    b.ls .Lcopy_forward
    add x9, x0, x2
    cmp x1, x9
    b.hs .Lcopy_forward
    add x0, x0, x2
    add x1, x1, x2
.Lcopy_back:
    ldrb w9, [x0, #-1]!
    strb w9, [x1, #-1]!
    subs x2, x2, #1
    b.ne .Lcopy_back
    ret
.Lcopy_forward:
    ldrb w9, [x0], #1
    strb w9, [x1], #1
    subs x2, x2, #1
    b.ne .Lcopy_forward
.Lcopy_done:
    ret

// x0 destination, x1 number of scalar slots, x2 fill value.
ox_fill:
    cbz x1, .Lfill_done
.Lfill_next:
    str x2, [x0], #8
    subs x1, x1, #1
    b.ne .Lfill_next
.Lfill_done:
    ret

// Repeat scalar value x0 into x1 destination, x2 times.
ox_repeat_slot:
    cbz x2, .Lrepeat_slot_done
.Lrepeat_slot:
    str x0, [x1], #8
    subs x2, x2, #1
    b.ne .Lrepeat_slot
.Lrepeat_slot_done:
    ret

// Repeat x3-byte block at x0 to x1, x2 times.
ox_repeat_block:
    cbz x3, .Lrepeat_block_done
    mov x10, x0
    cbz x2, .Lrepeat_block_done
.Lrepeat_block:
    mov x11, x10
    mov x12, x3
    cbz x12, .Lrepeat_block_advance
.Lrepeat_block_byte:
    ldrb w9, [x11], #1
    strb w9, [x1], #1
    subs x12, x12, #1
    b.ne .Lrepeat_block_byte
.Lrepeat_block_advance:
    subs x2, x2, #1
    b.ne .Lrepeat_block
.Lrepeat_block_done:
    ret

// Reverse elements in place. x0 descriptor, x1 stride (whole rows for matrices).
ox_array_reverse:
    cbz x1, .Lreverse_done
    ldr x9, [x0]
    cmp x9, #2
    b.lo .Lreverse_done
    ldr x10, [x0, #8]
    sub x9, x9, #1
    madd x11, x9, x1, x10
.Lreverse_outer:
    cmp x10, x11
    b.hs .Lreverse_done
    mov x12, #0
.Lreverse_bytes:
    cmp x12, x1
    b.hs .Lreverse_advance
    ldrb w13, [x10, x12]
    ldrb w14, [x11, x12]
    strb w14, [x10, x12]
    strb w13, [x11, x12]
    add x12, x12, #1
    b .Lreverse_bytes
.Lreverse_advance:
    add x10, x10, x1
    sub x11, x11, x1
    b .Lreverse_outer
.Lreverse_done:
    ret

// Inclusive i32 random range, using Linux getrandom, with rejection sampling.
ox_random:
    stp x29, x30, [sp, #-48]!
    str x0, [sp, #16]
    sub x9, x1, x0
    add x9, x9, #1
    str x9, [sp, #24]
    // threshold = 2^64 mod range; discard values below it to avoid modulo bias.
    neg x10, x9
    udiv x11, x10, x9
    msub x10, x11, x9, x10
    str x10, [sp, #32]
.Lrandom_retry:
    add x0, sp, #40
    mov x1, #8
    mov x2, #0
    mov x8, #278
    svc #0
    cmn x0, #4
    b.eq .Lrandom_retry
    cmp x0, #0
    b.lt ox_random_error
    cmp x0, #8
    b.ne .Lrandom_retry
    ldr x10, [sp, #40]
    ldr x9, [sp, #32]
    cmp x10, x9
    b.lo .Lrandom_retry
    ldr x9, [sp, #24]
    udiv x11, x10, x9
    msub x10, x11, x9, x10
    ldr x0, [sp, #16]
    add x0, x0, x10
    ldp x29, x30, [sp], #48
    ret
ox_random_error:
    adrp x1, ox_random_message
    add x1, x1, :lo12:ox_random_message
    mov x2, #ox_random_message_length
    b ox_fail

// Write source-positioned diagnostics to stderr, never to program stdout.
ox_write_error:
    ldr x2, [x0]
    add x1, x0, #8
.Lerror_write:
    mov x0, #2
    mov x8, #64
    svc #0
    cmn x0, #4
    b.eq .Lerror_write
    cmp x0, #0
    b.le ox_io_error
    add x1, x1, x0
    subs x2, x2, x0
    b.ne .Lerror_write
    ret
.section .rodata
ox_random_message: .ascii "No fue posible obtener números aleatorios.\n"
.equ ox_random_message_length, . - ox_random_message
