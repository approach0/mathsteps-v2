from axiom import Axiom
from alpha_equiv import rewrite_by_alpha, alpha_prettyprint


def get_atom_number(narr):
    """
    常量表达式 narr 转换为数字，不是常量表达式则返回 None
    """
    root = narr[0]
    if root[1] == 'NUMBER':
        Value = narr[1] if root[0] > 0 else -narr[1]
        return Value
    else:
        return None


def gen_atom_number(num):
    """
    生成一个常量表达式，输入是数字。小数点后至多保留 3 位。
    """
    num = float(num)
    if not num.is_integer():
        num = round(num, 3) # avoid infinity decimals

    if num >= .0:
        return [(+1, 'NUMBER'), abs(num)]
    else:
        return [(-1, 'NUMBER'), abs(num)]


###
# Dynamic Axioms
###

def calc_add(pattern_narr, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        c = a + b
        rewrite_rules = {}
        rewrite_rules['c'] = gen_atom_number(c)
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

axiom_calc_add = (
    Axiom(name='加法计算')
    .add_rule('#(a + b)', '#1 c', dynamic_procedure=calc_add)

    .add_test('-12 + 3')
    .add_test('(-12 - 3 - 1)')
    .add_test('-(12 - 1)')
)

def calc_mul(pattern_narr, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        c = a * b
        rewrite_rules = {}
        rewrite_rules['c'] = gen_atom_number(c)
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

axiom_calc_mul = (
    Axiom(name='乘法计算')
    .add_rule('#ab', '#1 c', dynamic_procedure=calc_mul)

    .add_test('3(-2)')
    .add_test('-(3 \cdot (-2))')
    .add_test('-(3 \cdot 4)')
)

def calc_pow(pattern_narr, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        try:
            c = a ** b
            if abs(c) > 2000: raise OverflowError

            rewrite_rules = {}
            rewrite_rules['c'] = gen_atom_number(c)
            return rewrite_by_alpha(output_tempalate, rewrite_rules), True

        except OverflowError:
            pass
        except ZeroDivisionError:
            pass

    return narr, False

axiom_calc_pow = (
    Axiom(name='乘方计算')
    .add_rule('#a^{b}', '#1 c', dynamic_procedure=calc_pow)

    .add_test('2^{3}', '8')
    .add_test('-2^{3}', '-8')
    .add_test('-2^{-2}', '-0.25')
    .add_test('-(-2)^{2}', '-4')
    .add_test('(-2)^{2}', '4')
)
