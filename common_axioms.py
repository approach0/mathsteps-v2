from axiom import Axiom

def common_axioms():
    """
    常用的规则集合（优先级已经按照数组元素的索引确定）
    """
    axioms = []

    axioms.append(Axiom('#(#\\sqrt{x})^{2}', '#1 x', name='根号的平方是其本身'))
