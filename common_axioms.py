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
        Axiom(name='任何数加零还是它本身')
        .add_rule('0 + n', 'n')
        .add_rule('n - 0', 'n')
    )

    axioms.append(
        Axiom(name='任何数乘以零还是它本身')
        .add_rule('# 0 \\times n', '0')
        .add_rule('#\\frac{#0}{x}', '0')
    )

    return axioms


if __name__ == '__main__':
    for axiom in common_axioms():
        print(axiom)
