from axiom import Axiom


def common_axioms():
    """
    常用的规则集合（优先级已经按照数组元素的索引确定）
    """
    axioms = []

    axioms.append(
        Axiom(name='根号的平方是其本身')
        .add_rule('#(#\\sqrt{x})^{2}', '#1 x')
    )

    axioms.append(
        Axiom(name='一的平方还是一')
        .add_rule('#(# 1)^{2}', '#1 x')
    )

    axioms.append(
        Axiom(name='负数的平方是其相反数的平方')
        .add_rule('#(-a)^{2}', '#1 a')
    )

    axioms.append(
        Axiom(name='任何数加零还是它本身', recursive_apply=True)
        .add_rule('0 + n', 'n')
        .add_rule('n - 0', 'n')
    )

    axioms.append(
        Axiom(name='一个数减去它本身是零')
        .add_rule('n - n', '0')
        .add_rule('a - \\frac{a}{1}', '0')
        .add_rule('\\frac{a}{1} - a', '0')
    )

    axioms.append(
        Axiom(name='任何数乘以零还是零', recursive_apply=True)
        .add_rule('# 0 \\times n', '0')
        .add_rule('#\\frac{#0}{x}', '0')
    )

    axioms.append(
        Axiom(name='一乘以任何数还是它本身', recursive_apply=True)
        .add_rule('# 1 \\times *{1}', '#1 *{1}')

        .add_test('1 \cdot 4', '4')
        .add_test('-4 \\times 1', '-4')
        .add_test('- (a+b) \cdot 1', '-a - b')
        .add_test('- 1 \cdot 4 \cdot 1', '-4')
    )

    axioms.append(
        Axiom(name='除以一个数等于乘上它的倒数')
        .add_rule('# x \\div (# \\frac{y}{z})', '#0 \\frac{xz}{y}')
    )

    axioms.append(
        Axiom(name='以分数表示除法')
        .add_rule('(#x) \\div (#y)', '#0 \\frac{x}{y}')
    )

    axioms.append(
        Axiom(name='乘数的指数是各个因子指数的乘数', recursive_apply=True, allow_complication=True)
        .add_rule('# (# a *{1})^{k}', '#1 (#2 a)^{k} \\times (*{1})^{k}')
    )

    axioms.append(
        Axiom(name='因子和分母消去')
        .add_rule('# x \\frac{a}{x}', '#1 a')

        .add_test('-3 \\times \\frac{-2}{3}', '2')
        .add_test('3 \\times \\frac{-2}{3}', '-2')
    )

    axioms.append(
        Axiom(name='绝对值分配到分子分母中', allow_complication=True)
        .add_rule('# \\left| # \\frac{a}{b} \\right|', '#1 \\frac{\\left| a \\right|}{\\left| b \\right|}')

        .add_test('\\left| - \\frac{1}{2} \\right|')
    )

    axioms.append(
        Axiom(name='根号分配到分子分母中', allow_complication=True)
        .add_rule('# \\sqrt{\\frac{a}{b}}', '#1 \\frac{\\sqrt{a}}{\\sqrt{b}}')

        .add_test('- \sqrt{\\frac{1}{2}}')
    )

    axioms.append(
        Axiom(name='分子分母消除公因子', recursive_apply=True)
        .add_rule('# \\frac{# x *{1} }{# x *{2} }', '#1 \\frac{#2 *{1}}{#3 *{2}}')
        .add_rule('# \\frac{# x }{# x *{2} }', '#1 \\frac{#2 1}{#3 *{2}}')
        .add_rule('# \\frac{# x *{1} }{# x }', '#0 *{1}')
        .add_rule('# \\frac{# x }{# x }', '#0 1')

        .add_test('- \\frac{bx}{ax}', '-\\frac{b}{a}')
        .add_test('- \\frac{-bx}{xa}', '-\\frac{-b}{a}')
        .add_test('- \\frac{-bxy}{-xay}', '-\\frac{-b}{-a}')
        .add_test('\\frac{-x}{xay}', '\\frac{-1}{a \\times y}')
        .add_test('\\frac{3xy}{-xy}', '-3')
        .add_test('-\\frac{-a}{-a}', '-1')
    )

    axioms.append(
        Axiom(name='乘积写成乘方的形式')
        .add_rule('#(#X)(#X)', '#0 X^{2}')

        .add_test('xx')
        .add_test('-\\frac{1}{2} \cdot \\frac{1}{2}', '-(\\frac{1}{2})^{2}')
    )

    axioms.append(
        Axiom(name='合并同类项', recursive_apply=True)
        .add_rule('X + X', '2X')
        .add_rule('- X - X', '-2X')
        .add_rule('#X # kX', '(#1 1 #2 k) X')
        .add_rule('#X # Xk', '(#1 1 #2 k) X')
        .add_rule('#X *{1} # X *{2}', '(#1 *{1} #2 *{2}) X')

        .add_test('2 + 2', '2 + 2')
        .add_test('x^{2} + x^{2}', '2 \\times x^{2}')
        .add_test('x + 2x + 3x', [
            '(1 + 2 + 3) \\times x',
            '(3 + 2 + 1) \\times x',
            '(1 + 3 + 2) \\times x',
            '(2 + 1 + 3) \\times x',
            '(3 + 1 + 2) \\times x'
        ])
        .add_test('2 - 3 \cdot 2', '2 - 3 \\times 2')
    )

    axioms.append(
        Axiom(name='等式移项')
        .add_rule('#x # y = z', '#1 x #2 y -z=0')
        .add_rule('x = z', 'x - z = 0')

        .add_test('1 - 2 = -3 + 5', '1 - 2 + 3 - 5 = 0')
        .add_test('ax = bx', 'a \\times x - b \\times x = 0')
    )

    axioms.append(
        Axiom(name='等式两边同乘', allow_complication=True)
        .add_rule('#\\frac{x}{y} + *{1} = z', '#1 x + y(*{1}) = yz')
        .add_rule('#\\frac{x}{y} = z', '#1 x = yz')

        .add_test('-\\frac{-2}{-3} = -4', '2 = (-3) \\times (-4)')
        .add_test('\\frac{x}{2} + a - b = z', 'x + 2 \\times (a - b) = 2 \\times z')
    )

    axioms.append(
        Axiom(name='嵌套分式的化简')
        .add_rule('#\\frac{#\\frac{x}{y}}{#\\frac{x}{y}}', '#0 1')
        .add_rule('#\\frac{#\\frac{x}{y}}{#\\frac{a}{b}}', '#0 \\frac{bx}{ay}')

        .add_test('-\\frac{-\\frac{4}{3}}{-\\frac{4}{3}}', '-1')
        .add_test('-\\frac{-\\frac{4}{3}}{\\frac{1}{2}}', '\\frac{2 \\times 4}{1 \\times 3}')
    )

    return axioms


if __name__ == '__main__':
    axioms = common_axioms()
    for i, axiom in enumerate(axioms):
        print(f'#{i}', axiom, end="\n\n")

    axioms[-1].test(debug=False)
