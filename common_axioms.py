import rich
from axiom import Axiom
import dynamic_axioms


def common_axioms(full=False):
    """
    常用的规则集合（优先级已经按照数组元素的索引确定）
    """
    axioms = []

    axioms.append(dynamic_axioms.canonicalize)

    axioms.append(
        Axiom(name='一个数减去它本身是零', root_sign_reduce=False)
        .add_rule('#(n - n)', '0', animation='`#1(n - n)`[replace]{0}')
        .add_rule('#(a - \\frac{a}{1})', '0', animation='`#1(a - \\frac{a}{1})`[replace]{0}')
        .add_rule('#(\\frac{a}{1} - a)', '0', animation='`#1(\\frac{a}{1} - a)`[replace]{0}')

        .add_test('-(3 - 3 + 1)')
    )

    axioms.append(
        Axiom(name='任何数乘以零还是零', recursive_apply=True)
        .add_rule('# 0 \cdot *{1}', '0', animation='`#1 0 \cdot *{1}`[replace]{0}')
        .add_rule('#\\frac{#0}{x}', '0', animation='`#1 \\frac{#2 0}{x}`[replace]{0}')

        .add_test('0 a b')
    )

    axioms.append(
        Axiom(name='带分式的展开', allow_complication=True)
        .add_rule('# & \\frac{a}{b}', '#1 (v + \\frac{a}{b})', animation="`#1 & \\frac{a}{b}`[replace]{#1 (v + \\frac{a}{b})}")

        .add_test('-3 \\frac{-2}{4}', '-(3 + \\frac{-2}{4})')
        .add_test('-3 \\frac{1}{2}', '-(3 + \\frac{1}{2})')
    )

    axioms.append(
        Axiom(name='任何数加零还是它本身', recursive_apply=True, root_sign_reduce=False)
        .add_rule('#(0 + n)', 'n', animation='`0`[remove] + n')
        .add_rule('#(n - 0)', 'n', animation='n - `0`[remove]')

        .add_test('0+3+2')
        .add_test('-(0+3+2)')
    )

    axioms.append(
        Axiom(name='一乘以任何数还是它本身', recursive_apply=True)
        .add_rule('# 1 \\times *{1}', '#1 *{1}', animation='#1 `1`[remove] *{1}')

        .add_test('1 \cdot 4', '4')
        .add_test('-4 \\times 1', '-4')
        .add_test('- (a+b) \cdot 1', '-a - b')
        .add_test('- 1 \cdot 4 \cdot 1', '-4')
    )

    axioms.append(
        Axiom(name='根号的平方是其本身')
        .add_rule('#(#\\sqrt{x})^{2}', '#1 x', animation='`#1 (#2\\sqrt{x})^{2}`[replace]{#1 x}')
    )

    axioms.append(
        Axiom(name='一的平方还是一')
        .add_rule('#(# 1)^{2}', '#1 1', animation='`#1 (#2 1)^{2}`[replace]{#1 1}')

        .add_test('-1^{2}')
        .add_test('(-1)^{2}')
    )

    axioms.append(
        Axiom(name='负数的平方是其相反数的平方', strict_simplify=(not full))
        .add_rule('#(-a)^{2}', '#1 a^{2}', animation='`#1 (-a)^{2}`[replace]{#1 a^{2}}')

        .add_test('(-3)^{2} - (6 \div (-\\frac{2}{3})^{2}) -  (-2)^{2}')
        .add_test('(6 \div (-\\frac{2}{3})^{2})')
        .add_test('3^{2} - (1 + \\frac{1}{2}) \\times \\frac{2}{9} - (6 \div (-\\frac{2}{3})^{2}) - (-2)^{2}')
    )

    axioms.append(
        Axiom(name='除以一个数等于乘上它的倒数', allow_complication=True)
        .add_rule('# (#\\frac{w}{x}) \\div (# \\frac{y}{z})', '#0 \\frac{wz}{xy}',
        animation='`#1 (#2 \\frac{w}{x}) \\div (#3 \\frac{y}{z})`[replace]{#0 \\frac{wz}{xy}}')
        .add_rule('# x \\div (# \\frac{y}{z})', '#0 \\frac{xz}{y}',
        animation='`#1 x \\div (#2 \\frac{y}{z})`[replace]{#0 \\frac{xz}{y}}')

        .add_test('- 3 \\div (-\\frac{1}{2})', '-\\frac{3 \\times 2}{1}')
        .add_test('\\frac{2}{3} \div \\frac{4}{5}')
    )

    axioms.append(
        Axiom(name='以分数表示除法', allow_complication=True)
        .add_rule('# (#x) \\div (#y)', '#0 \\frac{x}{y}', animation="`#1(#2 x) \\div (#3 y)`[replace]{#0 \\frac{x}{y}}")

        .add_test('1 \\div 2x + 3')
        .add_test("6 \div 3")
    )

    axioms.append(
        Axiom(name='因子和分母消去')
        .add_rule('# x \\times \\frac{a}{x}', '#1 a', animation="#1 `x`[remove] \\times \\frac{a}{`x`[removeDenom]}")

        .add_test('-3 \\times \\frac{-2}{3}', '2')
        .add_test('3 \\times \\frac{-2}{3}', '-2')
    )

    axioms.append(
        Axiom(name='绝对值分配到分子分母中', allow_complication=True)
        .add_rule('# \\left| # \\frac{a}{b} \\right|', '#1 \\frac{\\left| a \\right|}{\\left| b \\right|}',
        animation='`#1 \\left| #2 \\frac{a}{b} \\right|`[replace]{#1 \\frac{\\left| a \\right|}{\\left| b \\right|}}')

        .add_test('\\left| - \\frac{1}{2} \\right|')
    )

    axioms.append(
        Axiom(name='根号分配到分子分母中', allow_complication=True)
        .add_rule('# \\sqrt{\\frac{a}{b}}', '#1 \\frac{\\sqrt{a}}{\\sqrt{b}}',
        animation='`#1 \\sqrt{\\frac{a}{b}}`[replace]{#1 \\frac{\\sqrt{a}}{\\sqrt{b}} }')

        .add_test('- \sqrt{\\frac{1}{2}}')
    )

    axioms.append(
        Axiom(name='分子分母消除公因子', recursive_apply=True)
        .add_rule('# \\frac{# x *{1} }{# x *{2} }', '#1 \\frac{#2 *{1}}{#3 *{2}}',
        animation='#1 \\frac{#2 `x`[remove] *{1}}{#3 `x`[remove] *{2}}')
        .add_rule('# \\frac{# x }{# x *{2} }', '#0 \\frac{1}{*{2}}',
        animation='#0 \\frac{`x`[replace]{1} \\times 1}{`x`[remove] *{2}}')
        .add_rule('# \\frac{# x *{1} }{# x }', '#0 *{1}',
        animation='#0 \\frac{`x`[remove] *{1} }{`x`[removeDenom]}')
        .add_rule('# \\frac{# x}{# x}', '#0 1',
        animation='`#1 \\frac{#2 x}{#3 x}`[replace]{#0 1}')

        .add_test('- \\frac{bx}{ax}', '-\\frac{b}{a}')
        .add_test('- \\frac{-bx}{xa}', '-\\frac{-b}{a}')
        .add_test('- \\frac{-bxy}{-xay}', '-\\frac{-b}{-a}')
        .add_test('- \\frac{-x}{ax}', '\\frac{1}{a}')
        .add_test('\\frac{-x}{xay}', '\\frac{-1}{a \\times y}')
        .add_test('\\frac{3xy}{-xy}', '-3')
        .add_test('-\\frac{-a}{-a}', '-1')
        .add_test('\\frac{-(a + b)}{a + b}', '-1')
        .add_test('\\frac{-3 - \\frac{1}{3}}{-(3 + \\frac{1}{3}) \\times x}', '\\frac{-1}{-x}')
    )

    axioms.append(
        Axiom(name='乘积写成乘方的形式', allow_complication=True)
        .add_rule('#(#X)(#X)', '#0 X^{2}',
        animation='`#1(#2 X)(#3 X)`[replace]{#0 X^{2}}')

        .add_test('xx')
        .add_test('-\\frac{1}{2} \cdot \\frac{1}{2}', '-(\\frac{1}{2})^{2}')
    )

    axioms.append(dynamic_axioms.calc_add)
    axioms.append(dynamic_axioms.calc_mul)
    axioms.append(dynamic_axioms.calc_pow)
    axioms.append(dynamic_axioms.calc_sqrt)
    axioms.append(dynamic_axioms.calc_abs)
    axioms.append(dynamic_axioms.collapse_fraction_add_float)
    axioms.append(dynamic_axioms.simplify_fraction)
    axioms.append(dynamic_axioms.collapse_fraction)
    axioms.append(dynamic_axioms.calc_sqrt)

    axioms.append(
        Axiom(name='等式移项')
        #.add_rule('#x # y = z', '#1 x #2 y -z=0', animation='#1 x #2 y - `z`[moveAfter,1] = `z`[moveBefore,1] + `0`[add]')
        .add_rule('x = z', 'x - z = 0', animation='x - `z`[add] = `z`[replace]{0}')

        .add_test('1 - 2 = -3 + 5', '1 - 2 + 3 - 5 = 0')
        .add_test('ax = bx', 'a \\times x - b \\times x = 0')
    )

    axioms.append(
        Axiom(name='等式两边同乘', allow_complication=True)
        .add_rule('#\\frac{x}{y} + *{1} = z', '#1 x + y(*{1}) = yz',
        animation='#1 \\frac{x}{`y`[removeDenom]} + `y`[add](*{1}) = `y`[add] z')
        .add_rule('#\\frac{x}{y} = z', '#1 x = yz',
        animation='#1 \\frac{x}{`y`[removeDenom]} = `y`[add] z')

        .add_test('-\\frac{-2}{-3} = -4', '2 = (-3) \\times (-4)')
        .add_test('\\frac{x}{2} + a - b = z', 'x + 2 \\times (a - b) = 2 \\times z')
    )

    if full:
        tmp_axiom = (
            Axiom(name='合并同类项', recursive_apply=True, allow_complication=True, root_sign_reduce=False, max_results=4)
            .add_rule('#(x + x)', '2x',
            animation='`#1(x + x)`[replace]{2x}')
            .add_rule('#(-x - x)', '-2x',
            animation='`#1(-x - x)`[replace]{-2x}')
            .add_rule('#(#x # kx)', '(#2 1 #3 k) x',
            animation='`#1(#2 x #3 kx)`[replace]{(#2 1 #3 k) x}')
            .add_rule('#(#x # xk)', '(#2 1 #3 k) x',
            animation='`#1(#2 x #3 xk)`[replace]{(#2 1 #3 k) x}')
            .add_rule('#(#x *{1} # x *{2})', '(#2 *{1} #3 *{2}) x',
            animation='`#1(#2 x *{1} #3 x *{2})`[replace]{(#2 *{1} #3 *{2}) x}')
        )
    else:
        tmp_axiom = (
            Axiom(name='合并同类项', recursive_apply=True, allow_complication=True, root_sign_reduce=False, max_results=4)
            .add_rule('#(X + X)', '2X',
            animation='`#1(X + X)`[replace]{2X}')
            .add_rule('#(-X - X)', '-2X',
            animation='`#1(-X - X)`[replace]{-2X}')
            .add_rule('#(#X # kX)', '(#2 1 #3 k) X',
            animation='`#1(#2 X #3 kX)`[replace]{(#2 1 #3 k) X}')
            .add_rule('#(#X # Xk)', '(#2 1 #3 k) X',
            animation='`#1(#2 X #3 Xk)`[replace]{(#2 1 #3 k) X}')
            .add_rule('#(#X *{1} # X *{2})', '(#2 *{1} #3 *{2}) X',
            animation='`#1(#2 X *{1} #3 X *{2})`[replace]{(#2 *{1} #3 *{2}) X}')
        )

    axioms.append(
        tmp_axiom
        .add_test('a + a', '2 \\times a')
        .add_test('-a - a', '2 \\times (-a)')
        .add_test('x^{2} + x^{2}', '2 \\times x^{2}')
        .add_test('-(-x + 3x)')
        .add_test('-x + 3x - 1x')
        .add_test('(-1-1)x')
        .add_test('-(-x + 3x - 1x)')
        .add_test('x + 2x + 3x')
        .add_test('x - 3 \cdot x', '(1 - 3) \\times x')
    )

    axioms.append(
        Axiom(name='负号提出括号', strict_simplify=True, disable=(not full))
        .add_rule('+(x + *{1})', '-(-x - *{1})',
        animation='`+(x + *{1})`[replace]{-(-x - *{1})}')

        .add_test("(1 + 2 + 3)")
        .add_test("(-a - b) x")
        .add_test("(-a + b)x")
        .add_test("(-a - b - c) x")
        .add_test('-3-\\frac{4}{17}')
        .add_test('(-3-\\frac{4}{17}) x')
        .add_test('(-3-\\frac{4}{17}) x + y')
        .add_test("(a - b - c) x")
    )

    axioms.append(
        Axiom(name='嵌套分式的化简')
        .add_rule('#\\frac{#\\frac{x}{y}}{#\\frac{a}{b}}', '#0 \\frac{bx}{ay}',
        animation='`#1 \\frac{#2 \\frac{x}{y}}{#3 \\frac{a}{b}}`[replace]{#0 \\frac{bx}{ay}}')
        .add_rule('#\\frac{#1}{#\\frac{x}{y}}', '#0 \\frac{y}{x}',
        animation='`#1 \\frac{#2 1}{#3 \\frac{x}{y}}`[replace]{#0 \\frac{y}{x}}')
        .add_rule('#\\frac{#\\frac{x}{y}}{#1}', '#0 \\frac{x}{y}',
        animation='`#1 \\frac{#2 \\frac{x}{y}}{#3 1}`[replace]{#0 \\frac{x}{y}}')
        .add_rule('#\\frac{a}{#\\frac{x}{y}}', '#0 \\frac{ay}{x}',
        animation='`#1 \\frac{a}{#2 \\frac{x}{y}}`[replace]{#0 \\frac{ay}{x}}')
        .add_rule('#\\frac{#\\frac{x}{y}}{a}', '#0 \\frac{x}{ay}',
        animation='`#1 \\frac{#2 \\frac{x}{y}}{a}`[replace]{#0 \\frac{x}{ay}}')

        .add_test('-\\frac{-\\frac{4}{3}}{-\\frac{4}{3}}', '-1')
        .add_test('-\\frac{-\\frac{4}{3}}{\\frac{1}{2}}', '\\frac{2 \\times 4}{1 \\times 3}')
        .add_test('-\\frac{-\\frac{4}{3}}{x}', '\\frac{4}{x \\times 3}')
        .add_test('-\\frac{4}{-\\frac{4}{3}}', '\\frac{4 \\times 3}{4}')
        .add_test('\\frac{-8}{\\frac{1}{4}}')
        .add_test('\\frac{-18}{\\frac{9 \\times (1 - \\frac{3}{4})}{4}}')
    )

    axioms.append(dynamic_axioms.fraction_addition)

    axioms.append(
        Axiom(name='分母为一的分式化简')
        .add_rule('#\\frac{k}{#1}', '#0 k', animation='`#1 \\frac{k}{#2 1}`[replace]{#0 k}')

        .add_test('\\frac{3}{-1}', '-3')
    )

    axioms.append(
        Axiom(name='分式的乘法', allow_complication=True)
        .add_rule('#\\frac{#1}{x} \\frac{#1}{y}', '#0 \\frac{1}{xy}',
        animation='`#1 \\frac{#2 1}{x} \\frac{#3 1}{y}`[replace]{#0 \\frac{1}{xy}}')
        .add_rule('#\\frac{#1}{x} \\frac{y}{#1}', '#0 \\frac{y}{x}',
        animation='`#1 \\frac{#2 1}{x} \\frac{y}{#3 1}`[replace]{#0 \\frac{y}{x}}')
        .add_rule('#\\frac{x}{#1} \\frac{y}{#1}', '#0 xy',
        animation='`#1 \\frac{x}{#2 1} \\frac{y}{#3 1}`[replace]{#0 xy}')
        .add_rule('#\\frac{a}{c} \\frac{b}{d}', '#1 \\frac{ab}{cd}',
        animation='`#1 \\frac{a}{c} \\frac{b}{d}`[replace]{#1 \\frac{ab}{cd}}')

        .add_test('-\\frac{1}{-2} \cdot \\frac{-2}{1}', '-\\frac{-2}{-2}')
    )

    axioms.append(
        Axiom(name='乘数的指数是各个因子指数的乘数', recursive_apply=True, allow_complication=True)
        .add_rule('# (# a *{1})^{k}', '#1 (#2 a)^{k} \\times (*{1})^{k}',
        animation='`#1 (#2 a *{1})^{k}`[replace]{#1 (#2 a)^{k} \\times (*{1})^{k}}')

        .add_test('-(-3xy)^{2}', '-(-3)^{2} \\times x^{2} \\times y^{2}')
    )

    axioms.append(
        Axiom(name='将指数分配进分子分母', allow_complication=True)
        .add_rule('#(-\\frac{#a}{#b})^{k}', '#1 (-1)^{k} \\frac{(#2 a)^{k}}{(#3 b)^{k}}',
        animation='`#1 (-\\frac{#2 a}{#3 b})^{k}`[replace]{#1 (-1)^{k} \\frac{(#2 a)^{k}}{(#3 b)^{k}}}')
        .add_rule('#(+\\frac{#a}{#b})^{k}', '#1 \\frac{(#2 a)^{k}}{(#3 b)^{k}}',
        animation='`#1 (+\\frac{#2 a}{#3 b})^{k}`[replace]{#1 \\frac{(#2 a)^{k}}{(#3 b)^{k}}}')

        .add_test('(-\\frac{-2}{3})^{2}', '(-1)^{2} \\times \\frac{(-2)^{2}}{3^{2}}')
        .add_test('-(\\frac{-2}{3})^{2}', '-\\frac{(-2)^{2}}{3^{2}}')
    )

    axioms.append(
        Axiom(name='系数乘进分式的分子', allow_complication=True)
        .add_rule('# a \\times \\frac{# 1}{b}', '#0 \\frac{a}{b}',
        animation='`#1 a \\times \\frac{#2 1}{b}`[replace]{#0 \\frac{a}{b}}')
        .add_rule('# a \\times \\frac{# c}{b}', '#0 \\frac{ac}{b}',
        animation='`#1 a \\times \\frac{#2 c}{b}`[replace]{#0 \\frac{ac}{b}}')

        .add_test('-\\frac{-1}{3} \\times 12', '\\frac{4}{1}')
        .add_test('12 \cdot \\frac{3}{2}', '\\frac{18}{1}')
        .add_test('\\frac{9}{4} \\times (1 - \\frac{3}{4})', '\\frac{9 \\times (1 - \\frac{3}{4})}{4}')
    )

    axioms.append(
        Axiom(name='乘法分配率', allow_complication=True, recursive_apply=True, max_results=4)
        .add_rule('#a(x + *{1})', '#1 ax #1 a *{1}',
        animation='`#1 a`[moveBefore,1] `(#1 `a`[moveAfter,1] x #1 `a`[moveAfter,1] *{1})`[removeOnly]')

        .add_test('3(a + b + c) + 1', '1 + 3 \\times a + 3 \\times b + 3 \\times c')
        .add_test('(a - b)(-2)', '-2 \\times a - 2 \\times (-b)')
        .add_test('2(a + 3(b + c))')
        #.add_test('\\frac{60 \\times (1 - \\frac{2}{5}) + 3}{2}')
    )

    axioms.append(
        Axiom(name='负号乘进因子', recursive_apply=True, strict_simplify=True, disable=(not full))
        .add_rule('-(x + *{1}) *{2} ', '(-x - *{1}) *{2}',
        animation='`-(x + *{1})`[replace]{-x - *{1}} *{2}')

        .add_test('-(3 - 2)x', '(-3 + 2) \\times x')
    )

    axioms.append(dynamic_axioms.fraction_int_addition)

    axioms.append(
        Axiom(name='和平方公式', allow_complication=True)
        .add_rule('#(#a + *{1})^{2}', '#1 ( a^{2} #2 2 a *{1} + (*{1})^{2} )',
        animation='`#1 (#2 a + *{1})^{2}`[replace]{#1 (a^{2} #2 2 a *{1} + (*{1})^{2})}')
        .add_rule('# \\left| #a + *{1} \\right|^{2}', '#1 ( a^{2} #2 2 a *{1} + (*{1})^{2} )',
        animation='`#1 \\left| #2 a + *{1} \\right|^{2}`[replace]{#1 ( a^{2} #2 2 a *{1} + (*{1})^{2} )}')

        .add_test('-(3 - 2)^{2}', '-(3^{2} + 2 \\times 3 \\times (-2) + (-2)^{2})')
    )

    axioms.append(
        Axiom(name='平方差公式', allow_complication=True)
        .add_rule('#(a + *{1})(a - *{1})', '#1( a^{2} - (*{1})^{2} )',
        animation='`#1 (a + *{1})(a - *{1})`[replace]{#1( a^{2} - (*{1})^{2} )}')

        .add_test('(3 + a + b)(-a - b + 3)', [
            '3^{2} - (a + b)^{2}',
            '3^{2} - (-a - b)^{2}'
        ])
    )

    return axioms


if __name__ == '__main__':
    axioms = common_axioms(full=True)

    for i, axiom in enumerate(axioms):
        #print(f'#{i}', axiom, end="\n\n")

        if axiom.name() in ['乘法分配率']:
            #import cProfile
            #cProfile.run('axiom.test(debug=False)')
            rich.print(f'[red]{axiom.name()}[/]')
            axiom.animation_mode = True
            axiom.test(debug=False, printNarr=True, printTrim=True)

    print(f'total {len(axioms)} axioms.')
