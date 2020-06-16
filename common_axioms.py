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
        Axiom(name='以分数表示除法')
        .add_rule('# x \\frac{a}{x}', '#1 a')
        .add_test('-3 \\times \\frac{-2}{3}', '2')
        .add_test('3 \\times \\frac{-2}{3}', '-2')
    )

    return axioms


if __name__ == '__main__':
    axioms = common_axioms()
    for i, axiom in enumerate(axioms):
        print(f'#{i}', axiom, end="\n\n")

    axioms[-1].test(debug=False)
