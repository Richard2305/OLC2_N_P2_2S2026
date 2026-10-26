// String operations over length-prefixed UTF-8. No source interpretation.
.text
// Find a needle at/after byte offset x2. Returns byte index or -1.
ox_string_find:
    ldr x9, [x0]
    ldr x10, [x1]
    cmp x2, x9
    b.hi .Lfind_missing
    cbz x10, .Lfind_found
    sub x11, x9, x2
    cmp x10, x11
    b.hi .Lfind_missing
    add x3, x0, #8
    add x4, x1, #8
    sub x5, x9, x10
.Lfind_position:
    cmp x2, x5
    b.hi .Lfind_missing
    mov x6, #0
.Lfind_compare:
    cmp x6, x10
    b.hs .Lfind_found
    add x7, x2, x6
    ldrb w11, [x3, x7]
    ldrb w12, [x4, x6]
    cmp w11, w12
    b.ne .Lfind_advance
    add x6, x6, #1
    b .Lfind_compare
.Lfind_advance:
    add x2, x2, #1
    b .Lfind_position
.Lfind_found:
    mov x0, x2
    ret
.Lfind_missing:
    mov x0, #-1
    ret

ox_string_contains:
    stp x29, x30, [sp, #-16]!
    mov x2, #0
    bl ox_string_find
    cmp x0, #0
    cset x0, ge
    ldp x29, x30, [sp], #16
    ret

// Advance past a nonempty match; empty patterns advance one Unicode scalar.
// x0 source descriptor, x1 needle descriptor, x2 match index -> next byte index.
ox_advance_match:
    ldr x9, [x1]
    cbz x9, .Ladvance_empty
    add x0, x2, x9
    ret
.Ladvance_empty:
    ldr x9, [x0]
    cmp x2, x9
    b.hs .Ladvance_end
    add x10, x0, #8
    ldrb w11, [x10, x2]
    mov x9, #1
    cmp w11, #192
    b.lo .Ladvance_result
    mov x9, #2
    cmp w11, #224
    b.lo .Ladvance_result
    mov x9, #3
    cmp w11, #240
    b.lo .Ladvance_result
    mov x9, #4
.Ladvance_result:
    add x0, x2, x9
    ret
.Ladvance_end:
    add x0, x2, #1
    ret

// Allocate a byte substring. Callers only supply validated UTF-8 boundaries.
ox_substring:
    stp x29, x30, [sp, #-48]!
    stp x0, x1, [sp, #16]
    sub x0, x2, x1
    bl ox_alloc
    str x0, [sp, #32]
    ldr x2, [x0]
    add x1, x0, #8
    ldp x0, x9, [sp, #16]
    add x0, x0, #8
    add x0, x0, x9
    bl ox_copy
    ldr x0, [sp, #32]
    ldp x29, x30, [sp], #48
    ret

// Replace all non-overlapping occurrences, including empty-pattern boundaries.
ox_string_replace:
    stp x29, x30, [sp, #-112]!
    stp x0, x1, [sp, #16]
    str x2, [sp, #32]
    stp xzr, xzr, [sp, #48] // search, count
.Lreplace_count:
    ldp x0, x1, [sp, #16]
    ldr x2, [sp, #48]
    bl ox_string_find
    cmp x0, #0
    b.lt .Lreplace_allocate
    mov x2, x0
    ldp x0, x1, [sp, #16]
    bl ox_advance_match
    str x0, [sp, #48]
    ldr x9, [sp, #56]
    add x9, x9, #1
    str x9, [sp, #56]
    b .Lreplace_count
.Lreplace_allocate:
    ldp x9, x10, [sp, #16]
    ldr x11, [sp, #32]
    ldr x9, [x9]
    ldr x10, [x10]
    ldr x11, [x11]
    sub x11, x11, x10
    ldr x12, [sp, #56]
    madd x0, x11, x12, x9
    bl ox_alloc
    str x0, [sp, #64]
    add x9, x0, #8
    str x9, [sp, #88]
    str xzr, [sp, #48]
    str xzr, [sp, #80]
.Lreplace_copy:
    ldp x0, x1, [sp, #16]
    ldr x2, [sp, #48]
    bl ox_string_find
    cmp x0, #0
    b.lt .Lreplace_tail
    str x0, [sp, #72]
    ldr x9, [sp, #80]
    sub x2, x0, x9
    ldr x0, [sp, #16]
    add x0, x0, #8
    add x0, x0, x9
    ldr x1, [sp, #88]
    bl ox_copy
    ldr x0, [sp, #32]
    ldr x2, [x0], #8
    bl ox_copy
    str x1, [sp, #88]
    ldr x9, [sp, #24]
    ldr x9, [x9]
    ldr x2, [sp, #72]
    add x9, x9, x2
    str x9, [sp, #80]
    ldp x0, x1, [sp, #16]
    bl ox_advance_match
    str x0, [sp, #48]
    b .Lreplace_copy
.Lreplace_tail:
    ldr x0, [sp, #16]
    ldr x2, [x0], #8
    ldr x9, [sp, #80]
    sub x2, x2, x9
    add x0, x0, x9
    ldr x1, [sp, #88]
    bl ox_copy
    ldr x0, [sp, #64]
    ldp x29, x30, [sp], #112
    ret

// Split produces an owned runtime-length array of String pointers.
ox_string_split:
    stp x29, x30, [sp, #-96]!
    stp x0, x1, [sp, #16]
    mov x9, #1
    str x9, [sp, #40]
    str xzr, [sp, #32]
.Lsplit_count:
    ldp x0, x1, [sp, #16]
    ldr x2, [sp, #32]
    bl ox_string_find
    cmp x0, #0
    b.lt .Lsplit_allocate
    mov x2, x0
    ldp x0, x1, [sp, #16]
    bl ox_advance_match
    str x0, [sp, #32]
    ldr x9, [sp, #40]
    add x9, x9, #1
    str x9, [sp, #40]
    b .Lsplit_count
.Lsplit_allocate:
    ldr x0, [sp, #40]
    mov x1, #8
    bl ox_array_new
    str x0, [sp, #48]
    str xzr, [sp, #32] // search
    str xzr, [sp, #56] // source cursor
    str xzr, [sp, #64] // output index
.Lsplit_copy:
    ldp x0, x1, [sp, #16]
    ldr x2, [sp, #32]
    bl ox_string_find
    cmp x0, #0
    b.lt .Lsplit_tail
    str x0, [sp, #72]
    mov x2, x0
    ldr x0, [sp, #16]
    ldr x1, [sp, #56]
    bl ox_substring
    ldr x9, [sp, #48]
    ldr x9, [x9, #8]
    ldr x10, [sp, #64]
    str x0, [x9, x10, lsl #3]
    add x10, x10, #1
    str x10, [sp, #64]
    ldr x9, [sp, #24]
    ldr x9, [x9]
    ldr x2, [sp, #72]
    add x9, x9, x2
    str x9, [sp, #56]
    ldp x0, x1, [sp, #16]
    bl ox_advance_match
    str x0, [sp, #32]
    b .Lsplit_copy
.Lsplit_tail:
    ldr x0, [sp, #16]
    ldr x2, [x0]
    ldr x1, [sp, #56]
    bl ox_substring
    ldr x9, [sp, #48]
    ldr x9, [x9, #8]
    ldr x10, [sp, #64]
    str x0, [x9, x10, lsl #3]
    ldr x0, [sp, #48]
    ldp x29, x30, [sp], #96
    ret

// Decode one valid UTF-8 scalar: x0 pointer -> x0 scalar, x1 next pointer.
ox_utf8_decode:
    mov x1, x0
    ldrb w0, [x1], #1
    cmp w0, #128
    b.lo .Ldecode_done
    cmp w0, #224
    b.hs .Ldecode_three
    and w0, w0, #31
    ldrb w9, [x1], #1
    and w9, w9, #63
    lsl w0, w0, #6
    orr w0, w0, w9
    ret
.Ldecode_three:
    cmp w0, #240
    b.hs .Ldecode_four
    and w0, w0, #15
    mov x10, #2
    b .Ldecode_continuation
.Ldecode_four:
    and w0, w0, #7
    mov x10, #3
.Ldecode_continuation:
    ldrb w9, [x1], #1
    and w9, w9, #63
    lsl w0, w0, #6
    orr w0, w0, w9
    subs x10, x10, #1
    b.ne .Ldecode_continuation
.Ldecode_done:
    ret

// Binary search scalar mappings. x0 scalar, x1 table, x2 record count.
ox_case_lookup:
    mov x3, #0
.Lcase_search:
    cmp x3, x2
    b.hs .Lcase_unmapped
    add x4, x3, x2
    lsr x4, x4, #1
    lsl x5, x4, #4
    add x5, x1, x5
    ldp x6, x7, [x5]
    cmp x0, x6
    b.eq .Lcase_mapped
    b.lo .Lcase_search_lower
    add x3, x4, #1
    b .Lcase_search
.Lcase_search_lower:
    mov x2, x4
    b .Lcase_search
.Lcase_mapped:
    mov x0, x7
    ret
.Lcase_unmapped:
    mov x0, #0
    ret

// Two-pass Unicode scalar case conversion: exact allocation, expanding mappings.
ox_string_case:
    stp x29, x30, [sp, #-96]!
    stp x0, x1, [sp, #16]
    str x2, [sp, #32]
    ldr x9, [x0]
    add x0, x0, #8
    str x0, [sp, #40]
    add x9, x9, x0
    str x9, [sp, #48]
    str xzr, [sp, #80]
.Lcase_count:
    ldr x0, [sp, #40]
    ldr x9, [sp, #48]
    cmp x0, x9
    b.hs .Lcase_allocate
    str x0, [sp, #72]
    bl ox_utf8_decode
    str x1, [sp, #40]
    ldr x1, [sp, #24]
    ldr x2, [sp, #32]
    bl ox_case_lookup
    cbz x0, .Lcase_original_length
    ldr x9, [x0]
    b .Lcase_add_length
.Lcase_original_length:
    ldr x9, [sp, #40]
    ldr x10, [sp, #72]
    sub x9, x9, x10
.Lcase_add_length:
    ldr x10, [sp, #80]
    add x10, x10, x9
    str x10, [sp, #80]
    b .Lcase_count
.Lcase_allocate:
    ldr x0, [sp, #80]
    bl ox_alloc
    str x0, [sp, #56]
    add x9, x0, #8
    str x9, [sp, #64]
    ldr x0, [sp, #16]
    add x0, x0, #8
    str x0, [sp, #40]
.Lcase_copy:
    ldr x0, [sp, #40]
    ldr x9, [sp, #48]
    cmp x0, x9
    b.hs .Lcase_done
    str x0, [sp, #72]
    bl ox_utf8_decode
    str x1, [sp, #40]
    ldr x1, [sp, #24]
    ldr x2, [sp, #32]
    bl ox_case_lookup
    cbz x0, .Lcase_original_bytes
    ldr x2, [x0], #8
    b .Lcase_copy_bytes
.Lcase_original_bytes:
    ldr x0, [sp, #72]
    ldr x2, [sp, #40]
    sub x2, x2, x0
.Lcase_copy_bytes:
    ldr x1, [sp, #64]
    bl ox_copy
    str x1, [sp, #64]
    b .Lcase_copy
.Lcase_done:
    ldr x0, [sp, #56]
    ldp x29, x30, [sp], #96
    ret

// Debug escaping for String/char elements within arrays.
ox_debug_string:
    stp x29, x30, [sp, #-48]!
    ldr x9, [x0]
    add x0, x0, #8
    add x9, x9, x0
    stp x0, x9, [sp, #16]
    mov x0, #34
    bl ox_print_char
.Ldebug_string_next:
    ldp x0, x9, [sp, #16]
    cmp x0, x9
    b.hs .Ldebug_string_end
    bl ox_utf8_decode
    str x1, [sp, #16]
    mov x1, #34
    bl ox_debug_scalar
    b .Ldebug_string_next
.Ldebug_string_end:
    mov x0, #34
    bl ox_print_char
    ldp x29, x30, [sp], #48
    ret
ox_debug_char:
    stp x29, x30, [sp, #-32]!
    str x0, [sp, #16]
    mov x0, #39
    bl ox_print_char
    ldr x0, [sp, #16]
    mov x1, #39
    bl ox_debug_scalar
    mov x0, #39
    bl ox_print_char
    ldp x29, x30, [sp], #32
    ret
ox_debug_scalar:
    cmp x0, x1
    b.eq .Ldebug_slash
    cmp x0, #92
    b.eq .Ldebug_slash
    cmp x0, #10
    b.eq .Ldebug_newline
    cmp x0, #13
    b.eq .Ldebug_return
    cmp x0, #9
    b.eq .Ldebug_tab
    cbz x0, .Ldebug_null
    b ox_print_char
.Ldebug_newline:
    mov x0, #110
    b .Ldebug_slash
.Ldebug_return:
    mov x0, #114
    b .Ldebug_slash
.Ldebug_tab:
    mov x0, #116
    b .Ldebug_slash
.Ldebug_null:
    mov x0, #48
.Ldebug_slash:
    stp x29, x30, [sp, #-32]!
    str x0, [sp, #16]
    mov x0, #92
    bl ox_print_char
    ldr x0, [sp, #16]
    bl ox_print_char
    ldp x29, x30, [sp], #32
    ret
