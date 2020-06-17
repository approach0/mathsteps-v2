from axiom import Axiom
import expression
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


def factorizations(num):
    """
    生成一个整数类型常量的因子分解。
    """
    num = abs(num)
    factors = []
    p = 2
    while num >= p:
        if num % p == 0:
            num = num  / p
            factors.append(p)
        else:
            p = p + 1
    return factors


def sqrt_draw(num):
    """
    将 sqrt(n) 提出为 m sqrt(n') 的形式
    """
    m = 1
    n = 1
    factors = factorizations(num)
    factors.sort()
    while len(factors) > 0:
        a = factors.pop(0)
        b = factors[0] if len(factors) > 0 else -1
        if a == b:
            factors.pop(0)
            m = m * a
        else:
            n = n * a
    return m, n


def Euclidean_gcd(x, y):
    """
    欧拉最大公約數
    """
    while(y):
        x, y = y, x % y
    return x


def Euclidean_lcm(a, b):
    """
    欧拉最小公倍数
    """
    if Euclidean_gcd(a, b) == 0:
        return 0
    else:
        return a * b / Euclidean_gcd(a, b)


###
# Dynamic Axioms
###

def calc_add(pattern_narr, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        c = a + b
        rewrite_rules['c'] = gen_atom_number(c)
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

axiom_calc_add = (
    Axiom(name='加法计算')
    .add_rule('#(a + b)', '#1 c', dynamic_procedure=calc_add)

    .add_test('-12 + 3', '-9')
    .add_test('(-12 - 3 - 1)')
    .add_test('-(12 - 1)', '-11')
    .add_test('0.25 - 3.25', '-3')
)


def calc_mul(pattern_narr, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        c = a * b
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


def calc_sqrt(pattern_narr, narr, rewrite_rules, output_tempalates):
    x = get_atom_number(rewrite_rules['x'])

    if x != None and x > 0 and x.is_integer():
        m, n = sqrt_draw(x)
        if n == 1:
            rewrite_rules['c'] = gen_atom_number(m)
            return rewrite_by_alpha(output_tempalates[0], rewrite_rules), True
        elif m > 1:
            rewrite_rules['m'] = gen_atom_number(m)
            rewrite_rules['n'] = gen_atom_number(n)
            return rewrite_by_alpha(output_tempalates[1], rewrite_rules), True

    return narr, False

axiom_calc_sqrt = (
    Axiom(name='开方化简')
    .add_rule('#\sqrt{x}', ['#1 c', '#1 m \\sqrt{n}'], dynamic_procedure=calc_sqrt)

    .add_test('-\\sqrt{8}', '-2 \\times \sqrt{2}')
    .add_test('\\sqrt{16}', '4')
)


def calc_abs(pattern_narr, narr, rewrite_rules, output_tempalate):
    x = get_atom_number(rewrite_rules['x'])

    if x != None:
        c = abs(x)
        rewrite_rules['c'] = gen_atom_number(c)
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

axiom_calc_abs = (
    Axiom(name='绝对值计算')
    .add_rule('#\\left| x \\right|', '#1 c', dynamic_procedure=calc_abs)

    .add_test('-\\left| 8 \\right|', '-8')
    .add_test('\\left| -8 \\right|', '8')
)


def simplify_fraction(pattern_narr, narr, rewrite_rules, output_tempalates):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None and a.is_integer() and b.is_integer():
        a, b = a, b
        gcd = Euclidean_gcd(a, b)
        if gcd != 0 and gcd != 1:
            a = a / gcd
            b = b / gcd
            if b == 1:
                rewrite_rules['c'] = gen_atom_number(a)
                return rewrite_by_alpha(output_tempalates[0], rewrite_rules), True
            elif b != 0:
                rewrite_rules['a'] = gen_atom_number(a)
                rewrite_rules['b'] = gen_atom_number(b)
                return rewrite_by_alpha(output_tempalates[1], rewrite_rules), True

    return narr, False

axiom_simplify_fraction = (
    Axiom(name='化简分式')
    .add_rule('#\\frac{a}{b}', ['#1 c', '#1 \\frac{a}{b}'], dynamic_procedure=simplify_fraction)

    .add_test('-\\frac{-14}{-4}', '-\\frac{7}{2}')
    .add_test('\\frac{9}{-6}', '\\frac{-3}{2}')
    .add_test('-\\frac{-12}{6}', '2')
)


def collapse_fraction(pattern_narr, narr, rewrite_rules, output_tempalates):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if b != 0:
        if a != None and b != None and not (a.is_integer() and b.is_integer()):
            rewrite_rules['c'] = gen_atom_number(a / b)
            return rewrite_by_alpha(output_tempalates[0], rewrite_rules), True

        elif b != None and not b.is_integer():
            rewrite_rules['k'] = gen_atom_number(1 / b)
            rewrite_rules['x'] = rewrite_rules['a']
            return rewrite_by_alpha(output_tempalates[1], rewrite_rules), True

    return narr, False

axiom_collapse_fraction = (
    Axiom(name='分式中带小数的化简')
    .add_rule('#\\frac{a}{b}', ['#1 c', '#1 kx'], dynamic_procedure=collapse_fraction)

    .add_test('-\\frac{-6.4}{3.2}', '2')
    .add_test('\\frac{9}{-2.5}', '-3.6')
    .add_test('-\\frac{-10.2}{-6}', '-1.7')
)


def collapse_fraction_add_float(pattern_narr, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])
    c = get_atom_number(rewrite_rules['c'])

    if a != None and b != None and c != None:
        if b != 0 and not c.is_integer():
            rewrite_rules['x'] = gen_atom_number(a / b)
            return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

axiom_collapse_fraction_add_float = (
    Axiom(name='分式加小数的化简')
    .add_rule('#\\frac{a}{b} # c', '#1 x #2 c', dynamic_procedure=collapse_fraction_add_float)

    .add_test('3.25 - \\frac{1}{4}', '-0.25 + 3.25')
    .add_test('-3.25 + \\frac{1}{4}', '0.25 - 3.25')
)
