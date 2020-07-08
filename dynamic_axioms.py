from axiom import Axiom
from expression import NarrRoot
import expression
import rich
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
        return [NarrRoot(+1, 'NUMBER'), abs(num)]
    else:
        return [NarrRoot(-1, 'NUMBER'), abs(num)]


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

def _calc_add(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        c = a + b
        rewrite_rules['c'] = gen_atom_number(c)
        new_narr = rewrite_by_alpha(output_tempalate, rewrite_rules)
        return new_narr, True

    return narr, False

calc_add = (
    Axiom(name='加减法计算', root_sign_reduce=False)
    .add_rule('#(a + b)', 'c', animation='`#1(a + b)`[replace]{c}', dynamic_procedure=_calc_add)

    .add_test('-12 + 3', '-9')
    .add_test('(-12 - 3 - 1)', ['-15 - 1', '-13 - 3', '-4 - 12'])
    .add_test('-(12 - 1)', '-11')
    .add_test('-(1 + 14 + 2)', ['-(15 + 2)', '-(3 + 14)', '-(16 + 1)'])
    .add_test('0.25 - 3.25', '-3')
    .add_test('-(1 + 3) x + 3 y', '-4 \\times x + 3 \\times y')
)


def _calc_mul(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])

    if a != None and b != None:
        c = a * b
        rewrite_rules['c'] = gen_atom_number(c)
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

calc_mul = (
    Axiom(name='乘法计算')
    .add_rule('#ab', '#1 c', animation='`#1 ab`[replace]{#1 c}', dynamic_procedure=_calc_mul)

    .add_test('3(-2)')
    .add_test('-(3 \cdot (-2))')
    .add_test('-(3 \cdot 4)')
)


def _calc_pow(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
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

calc_pow = (
    Axiom(name='乘方计算')
    .add_rule('#a^{b}', '#1 c', animation='`#1 a^{b}`[replace]{#1 c}', dynamic_procedure=_calc_pow)

    .add_test('2^{3}', '8')
    .add_test('-2^{3}', '-8')
    .add_test('-2^{-2}', '-0.25')
    .add_test('-(-2)^{2}', '-4')
    .add_test('(-2)^{2}', '4')
)


def _calc_sqrt(pattern_narr, signs, narr, rewrite_rules, output_tempalates):
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

calc_sqrt = (
    Axiom(name='开方化简')
    .add_rule('#\sqrt{x}', ['#1 c', '#1 m \\sqrt{n}'], dynamic_procedure=_calc_sqrt,
    animation=[
        '`#1 \sqrt{x}`[replace]{#1 c}',
        '`#1 \sqrt{x}`[replace]{#1 m \\sqrt{n} }',
    ])

    .add_test('-\\sqrt{8}', '-2 \\times \sqrt{2}')
    .add_test('\\sqrt{16}', '4')
)


def _calc_abs(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
    x = get_atom_number(rewrite_rules['x'])

    if x != None:
        c = abs(x)
        rewrite_rules['c'] = gen_atom_number(c)
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

calc_abs = (
    Axiom(name='绝对值计算')
    .add_rule('#\\left| #x \\right|', '#1 c', animation='`#1 \\left| #2x \\right|`[replace]{#1 c}', dynamic_procedure=_calc_abs)

    .add_test('-\\left| 8 \\right|', '-8')
    .add_test('\\left| -8 \\right|', '8')
)


def _simplify_fraction(pattern_narr, signs, narr, rewrite_rules, output_tempalates):
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

simplify_fraction = (
    Axiom(name='化简分式')
    .add_rule('#\\frac{a}{b}', ['#1 c', '#1 \\frac{a}{b}'], dynamic_procedure=_simplify_fraction,
    animation=[
        '`#1 \\frac{a}{b}`[replace]{#1 c}',
        '`#1 \\frac{a}{b}`[replace]{#1 \\frac{a}{b} }',
    ])

    .add_test('-\\frac{-14}{-4}', '-\\frac{7}{2}')
    .add_test('\\frac{9}{-6}', '\\frac{-3}{2}')
    .add_test('-\\frac{-12}{6}', '2')
)


def _fraction_addition_same_denom(pattern_narr, signs, narr, rewrite_rules, output_tempalates):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])
    c = get_atom_number(rewrite_rules['c'])

    if a != None and b != None:
        if a.is_integer() and b.is_integer():
            a = a * signs[1]
            b = b * signs[2]
            z = a + b
            if c != None and c.is_integer() and c != 0:
                if (z / c).is_integer():
                    rewrite_rules['z'] = gen_atom_number(z / c)
                    return rewrite_by_alpha(output_tempalates[0], rewrite_rules), True

            rewrite_rules['z'] = gen_atom_number(z)
            return rewrite_by_alpha(output_tempalates[1], rewrite_rules), True

    return narr, False

fraction_addition = (
    Axiom(name='分式 加法/减法', allow_complication=True, root_sign_reduce=False)
    .add_rule('#(#\\frac{a}{c} #\\frac{b}{c})', [
        'z',
        '\\frac{z}{c}'
    ], dynamic_procedure=_fraction_addition_same_denom, animation=[
        '`#1(#2 \\frac{a}{c} #3\\frac{b}{c})`[replace]{z}',
        '`#1(#2 \\frac{a}{c} #3\\frac{b}{c})`[replace]{ \\frac{z}{c} }',
    ])
    .add_rule('#\\frac{a}{b} #\\frac{c}{d}', '\\frac{#1 ad #2 cb}{bd}',
    animation='`(#1 \\frac{a}{b} #2\\frac{c}{d})`[replace]{ \\frac{#1 ad #2 cb}{bd} }')

    .add_test('-(\\frac{4}{3} - \\frac{1}{3})', '-1')
    .add_test('\\frac{4}{3} - \\frac{1}{3}', '1')
    .add_test('-\\frac{1}{3} - \\frac{5}{3}', '-2')
    .add_test('-\\frac{1}{3} + \\frac{5}{3}', '\\frac{4}{3}')
    .add_test('\\frac{1}{3a} - \\frac{5}{3a}', '\\frac{-4}{3 \\times a}')
    .add_test('-\\frac{1}{-2} - \\frac{-2}{3}')
)


def _fraction_int_addition(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])
    c = get_atom_number(rewrite_rules['c'])

    if a != None and a.is_integer():
        return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

fraction_int_addition = (
    Axiom(name='整数加分式的转换', allow_complication=True, root_sign_reduce=False)
    .add_rule('#(#a # \\frac{b}{c})', '\\frac{#2 ac #3 b}{c}', dynamic_procedure=_fraction_int_addition,
    animation='`#1(#2 a #3 \\frac{b}{c})`[replace]{\\frac{#2 ac #3 b}{c}}')

    .add_test('-(\\frac{1}{3} - \\frac{2}{3} + 2)')
    .add_test('- 1 - \\frac{-1}{2}', '\\frac{-2 + 1}{2}')
    .add_test('- \\frac{-1}{2} + 1', '\\frac{2 + 1}{2}')
    .add_test('\\left| -(5 + \\frac{1}{2})  \\right|', '\left|-\\frac{10 + 1}{2}\\right|')
)


def _collapse_fraction(pattern_narr, signs, narr, rewrite_rules, output_tempalates):
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

collapse_fraction = (
    Axiom(name='分式中带小数的化简')
    .add_rule('#\\frac{a}{b}', ['#1 c', '#1 kx'], dynamic_procedure=_collapse_fraction,
    animation=[
        '`#1 \\frac{a}{b}`[replace]{#1 c}',
        '`#1 \\frac{a}{b}`[replace]{#1 kx}',
    ])

    .add_test('-\\frac{-6.4}{3.2}', '2')
    .add_test('\\frac{9}{-2.5}', '-3.6')
    .add_test('-\\frac{-10.2}{-6}', '-1.7')
)


def _collapse_fraction_add_float(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
    a = get_atom_number(rewrite_rules['a'])
    b = get_atom_number(rewrite_rules['b'])
    c = get_atom_number(rewrite_rules['c'])

    if a != None and b != None and c != None:
        if b != 0 and not c.is_integer():
            rewrite_rules['x'] = gen_atom_number(a / b)
            return rewrite_by_alpha(output_tempalate, rewrite_rules), True

    return narr, False

collapse_fraction_add_float = (
    Axiom(name='分式加小数的化简', root_sign_reduce=False)
    .add_rule('#(#\\frac{a}{b} # c)', '#2 x #3 c', dynamic_procedure=_collapse_fraction_add_float,
    animation='`#2\\frac{a}{b}`[replace]{#2 x} #3 c')

    .add_test('3.25 - \\frac{1}{4}', '-0.25 + 3.25')
    .add_test('-(-3.25 + \\frac{1}{4})', '-(0.25 - 3.25)')
    .add_test('-3.25 + \\frac{1}{4}', '0.25 - 3.25')
)


def _canonicalize(pattern_narr, signs, narr, rewrite_rules, output_tempalate):
    sign, Type = narr[0].get()
    if Type in expression.commutative_operators():
        new_narr, is_applied = expression.canonicalize(narr)

        if is_applied:
            rewrite_rules['X'] = new_narr
            return rewrite_by_alpha(output_tempalate, rewrite_rules), True
        else:
            return new_narr, False
    return narr, False

canonicalize = (
    Axiom(name='去括号')
    .add_rule('# a *{1}', 'X', animation='`#1 a *{1}`[replace]{X}', dynamic_procedure=_canonicalize)
    .add_rule('# a # *{1}', 'X', animation='`#1 a #2 *{1}`[replace]{X}', dynamic_procedure=_canonicalize)
    .add_rule('# a', 'X', animation='`#1 a`[replace]{X}', dynamic_procedure=_canonicalize)

    .add_test(
        [NarrRoot(1, 'add'),
            [NarrRoot(-1, 'NUMBER'), 30.0],
            [NarrRoot(1, 'add'),
                [NarrRoot(1, 'NUMBER'), 1.0],
                [NarrRoot(1, 'NUMBER'), 3.0]
            ]
        ]
    )

    .add_test(
        [NarrRoot(1, 'add'),
            [NarrRoot(-1, 'NUMBER'), 30.0],
            [NarrRoot(1, 'mul'),
                [NarrRoot(1, 'NUMBER'), 10.0],
                [NarrRoot(-1, 'frac'),
                    [NarrRoot(1, 'NUMBER'), 1.0],
                    [NarrRoot(1, 'NUMBER'), 3.0]
                ]
            ]
        ]
    )

    .add_test(
        [NarrRoot(1, 'add'),
            [NarrRoot(-1, 'NUMBER'), 30.0],
            [NarrRoot(-1, 'add'),
                [NarrRoot(1, 'NUMBER'), 10.0],
                [NarrRoot(-1, 'frac'),
                    [NarrRoot(1, 'NUMBER'), 1.0],
                    [NarrRoot(1, 'NUMBER'), 3.0]
                ]
            ]
        ]
    )

    .add_test(
        [NarrRoot(-1, 'add'),
            [NarrRoot(-1, 'NUMBER'), 30.0],
            [NarrRoot(1, 'NUMBER'), 1.0],
        ]
    )

    .add_test(
        [NarrRoot(1, 'frac'),
            [NarrRoot(1, 'add'),
                [NarrRoot(1, 'mul'),
                    [NarrRoot(1, 'NUMBER'), 30.0],
                    [NarrRoot(-1, 'frac'),
                        [NarrRoot(1, 'NUMBER'), 1.0], [NarrRoot(1, 'NUMBER'), 3.0]
                    ]
                ],
                [NarrRoot(-1, 'NUMBER'), 90.0]
            ],
            [NarrRoot(1, 'NUMBER'), 49.0]
        ]
    )
)


if __name__ == '__main__':
    a = calc_add
    a = fraction_int_addition
    a = calc_pow
    a = collapse_fraction_add_float
    a = canonicalize

    a.animation_mode = True
    a.test(debug=False)
    pass
