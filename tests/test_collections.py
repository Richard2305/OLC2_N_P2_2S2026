import json
from pathlib import Path
import pytest
from compiler.pipeline import execute_source


def run(body, functions=""):
    return execute_source("fn main(){\n" + body + "\n}" + functions)


def assert_output(body, expected, functions=""):
    result = run(body, functions)
    assert result["success"], (result["diagnostics"], result["stderr"])
    assert result["stdout"] == expected
    return result


def test_official_error_fixture_recovers_all_control_statements():
    root = Path(__file__).parent / "fixtures"
    result = execute_source((root / "entradas/8_errores.ox").read_text())
    expected = (root / "esperadas/8_errores.esperado.txt").read_text().split("## SALIDA ESTANDAR\n")[1]
    assert result["stdout"] == expected
    assert result["executed"] and result["exit_code"] == 0
    assert not result["success"]
    assert not result["stderr"]
    assert len(result["diagnostics"]) == 11
    assert {d["category"] for d in result["diagnostics"]} == {"Léxico", "Sintáctico", "Semántico"}
    assert any(d["position"] == {"line": 57, "column": 15} for d in result["diagnostics"])
    assert any(d["position"] == {"line": 45, "column": 20} for d in result["diagnostics"])


def test_fixed_array_and_row_assignments_are_value_copies():
    assert_output('let mut a=[[1,2],[3,4]]; let mut b=a; b[0][0]=9; b[1]=a[0]; a[0][1]=7; println!(a); println!(b);',
                  '[[1, 7], [3, 4]]\n[[9, 2], [1, 2]]\n')


def test_multidimensional_parameters_returns_and_recursive_calls():
    assert_output('let a=[[[1,2],[3,4]],[[5,6],[7,8]]]; let mut b=copy(a,2); b[1][0][1]=99; println!(a[1][0]); println!(b[1][0]);',
                  '[5, 6]\n[5, 99]\n',
                  'fn copy(a:[[[i32;2];2];2],n:i32)->[[[i32;2];2];2]{if n==0{return a;} return copy(a,n-1);}')


def test_array_parameters_cannot_mutate_caller():
    result = run('let mut a=[1,2]; bad(a); println!(a);', 'fn bad(a:[i32;2]){a[0]=9;}')
    assert not result["success"]
    assert result["stdout"] == '[1, 2]\n'
    assert any('inmutable' in d["message"] for d in result["diagnostics"])


def test_slices_share_storage_and_can_be_rebound_without_writing_elements():
    assert_output('let mut a=[1,2,3,4]; let mut s=&a[0..3]; let tail=&s[1..3]; a[1]=9; println!(tail); s=&a[2..4]; println!(s);',
                  '[9, 3]\n[3, 4]\n')


@pytest.mark.parametrize('operation', ['a[0]=9;', 'a.reverse();', 's[0]=9;', 's.reverse();', 'b[0..1].reverse();'])
def test_mutability_is_enforced_for_arrays_and_readonly_slices(operation):
    result = run('let a=[1,2]; let mut b=[3,4]; let mut s=&b[0..2];' + operation + 'println!(a); println!(b);')
    assert not result['success']
    assert result['stdout'] == '[1, 2]\n[3, 4]\n'


def test_empty_and_repeated_arrays_with_nested_zero_length_rows():
    assert_output('let empty:[i32;0]=[]; println!(empty); let mut rows:[[i32;0];3]=[[];3]; rows.reverse(); println!(rows); let a=[[1,2];3]; println!(a);',
                  '[]\n[[], [], []]\n[[1, 2], [1, 2], [1, 2]]\n')


def test_default_arrays_and_numeric_array_inference():
    assert_output('let a:[[i32;2];2]; let s:[String;2]; let b=[1,2.5]; println!(a); println!(s); println!(b);',
                  '[[0, 0], [0, 0]]\n["", ""]\n[1.0, 2.5]\n')


def test_empty_array_arguments_and_returns_use_signature_context():
    assert_output('println!(empty([]));', '[]\n', 'fn empty(a:[i32;0])->[i32;0]{return [];}')


@pytest.mark.parametrize('body', [
    'let a=[1,"bad"];', 'let a=[[1,2],[3]];', 'let a:[i32;3]=[1,2];',
    'let a=[1; -1];', 'let n=2; let a=[1;n];', 'let a=[1,2]; println!(a[true]);',
    'let a=[1,2]; println!(a[-1]);', 'let a=[1,2]; println!(&a[2..1]);',
    'let a=[1;2147483647];', 'let a=[];',
])
def test_invalid_shapes_indices_and_sizes_are_diagnosed(body):
    result = run(body + 'println!("fin");')
    assert result['diagnostics']
    assert result['exit_code'] == 0, result['stderr']
    assert result['stdout'].endswith('fin\n')


def test_dynamic_bounds_recover_stack_variables_and_following_statements():
    result = run('let mut a=[1,2]; let i=9; println!("prefix {}", a[i]+4); a[0]+=a[i]; let x=a[i]; println!(x); println!(a); println!("fin");')
    assert result['stdout'] == '0\n[1, 2]\nfin\n'
    assert len(result['diagnostics']) == 3
    assert not result['stderr']
    assert result['exit_code'] == 0
    assert all(d['position']['line'] == 2 for d in result['diagnostics'])
    assert all(d['fragment'] for d in result['diagnostics'])


def test_dynamic_invalid_slice_and_random_range_recover():
    result = run('let a=[1,2]; let end=5; println!(&a[0..end]); let lo=4; let hi=1; let n=random(lo,hi); println!(n); println!("fin");')
    assert result['stdout'] == '0\nfin\n'
    assert len(result['diagnostics']) == 2
    assert not result['stderr']


def test_short_circuit_avoids_dynamic_bounds_error():
    assert_output('let a=[true]; let i=9; println!(false && a[i]); println!(true || a[i]);', 'false\ntrue\n')


def test_recovery_inside_loop_function_and_nested_expression():
    result = run('let a=[1]; let mut i=0; while i<3 { i+=1; println!(probe(a,i)+5); } println!("fin");',
                 'fn probe(a:[i32;1],i:i32)->i32{let x=a[i]; return x;}')
    assert result['stdout'] == '5\n5\n5\nfin\n'
    assert len(result['diagnostics']) == 3
    assert not result['stderr']


def test_runtime_length_array_copy_reverse_and_primitive_contains():
    assert_output('let mut a="a,b,c".split(","); let b=a; a.reverse(); println!(a); println!(b); println!(a.contains("b")); println!([1.5,2.0].contains(2)); println!([true,false].contains(false)); println!([\'ñ\',\'x\'].contains(\'ñ\'));',
                  '["c", "b", "a"]\n["a", "b", "c"]\ntrue\ntrue\ntrue\ntrue\n')


def test_string_new_typeof_array_and_slice_lengths():
    assert_output('println!(String::new()); let a=[1,2,3]; let s=&a[1..3]; println!("{} {} {}", typeof(a), s.len(), "é".len());',
                  '\n[i32; 3] 2 2\n')


@pytest.mark.parametrize(('source','separator'), [('a,b,c',','), (',a,,b,',','), ('é漢😀',''), ('',''), ('','x'), ('aaaa','aa'), ('a--b--','--'), ('a\0b\0','\0'), ('no match','?')])
def test_split_handles_empty_fields_unicode_and_multibyte_separators(source, separator):
    if separator:
        expected = source.split(separator)
    else:
        expected = ['', *source, '']
    output = json.dumps(expected, ensure_ascii=False).replace('\\u0000', '\\0') + '\n'
    assert_output(f'println!({json.dumps(source, ensure_ascii=False)}.split({json.dumps(separator, ensure_ascii=False)}));', output)


@pytest.mark.parametrize(('source','old','new'), [('aaaa','aa','b'), ('abc','','-'), ('é😀','','!'), ('','','x'), ('abc','?','x'), ('a,b,',',',''), ('a\0b','\0','X'), ('aaaa','a','é'), ('ababab','ab','xy')])
def test_replace_all_and_empty_patterns(source, old, new):
    assert_output(f'println!({json.dumps(source, ensure_ascii=False)}.replace({json.dumps(old, ensure_ascii=False)}, {json.dumps(new, ensure_ascii=False)}));', source.replace(old, new) + '\n')


def test_unicode_case_conversion_expansions_and_empty_strings():
    assert_output('println!("áÑß漢😀".to_uppercase()); println!("ÁÑİ漢😀".to_lowercase()); println!("".to_uppercase());',
                  'ÁÑSS漢😀\náñi̇漢😀\n\n')


def test_array_debug_escapes_quotes_slashes_and_control_characters():
    value = ['a"b', 'x\ny', '\\', '\0']
    source = 'println!([' + ','.join(json.dumps(v) for v in value) + ']);'
    expected = json.dumps(value).replace('\\u0000', '\\0') + '\n'
    assert_output(source, expected)


def test_random_inclusive_equal_negative_and_full_i32_ranges():
    result = run('println!(random(7,7)); let mut i=0; while i<50{let x=random(-10,-1); println!(x); let y=random(-2147483648,2147483647); println!(y); i+=1;}')
    assert result['success'], result
    values = list(map(int, result['stdout'].splitlines()))
    assert values[0] == 7
    assert all(-10 <= value <= -1 for value in values[1::2])
    assert all(-2147483648 <= value <= 2147483647 for value in values[2::2])


@pytest.mark.parametrize('expression', ['random(2,1)', 'random(1.0,2)', 'typeof()', '"x".len(1)', '"x".contains(1)', '"x".replace("x")', '[1].reverse()', '[1].contains("x")'])
def test_builtin_signatures_reject_invalid_calls(expression):
    result = run(expression + '; println!("fin");')
    assert result['diagnostics']
    assert result['stdout'] == 'fin\n'
