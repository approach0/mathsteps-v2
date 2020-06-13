import rich
import expression
from copy import deepcopy


def operator_identical(root1, root2, strict=False):
    if strict:
        return root1 == root2
    else:
        return root1[1] == root2[1]


def narr_identical(narr1, narr2):
    """
    递归比较两个表达式 (nested arrary) 是否相等（按照顺序不交换）
    """
    root1, root2 = narr1[0], narr2[0]
    children1, children2 = narr1[1:], narr2[1:]

    if not operator_identical(root1, root2):
        return False
    elif len(children1) != len(children2):
        return False

    for i, c1 in enumerate(children1):
        c2 = children2[i]
        is_identical = False
        if isinstance(c1, float) or isinstance(c1, str):
            is_identical = (c1 == c2)
        else:
            is_identical = narr_identical(c1, c2)

        if not is_identical:
            return False
    return True


def reverse_sign(narr):
    """
    表达式变号，从加号变成减号或者减号改成加号。加法会让每一项变号。
    """
    root = narr[0]
    sign, t = root[0], root[1]
    # handle addition
    if t == 'add':
        for i, c in enumerate(narr[1:]):
            narr[1 + i] = reverse_sign(c)
        return narr
    else:
        # handle others
        if sign == '+':
            narr[0] = ('-', t)
        else:
            narr[0] = ('+', t)
        return narr


def test_polynomial_var(narr):
    """
    检测表达式是不是多项式的未知数项
    """
    # either [('+', 'VAR'), 'x']
    # or [('+', 'sup'), [('+', 'VAR'), 'x'], [('+', 'NUMBER'), 2.0]]
    root = narr[0]
    sign, Type = root
    if Type == 'VAR' and sign == '+':
        return True
    elif Type == 'sup':
        child1 = narr[1]
        return child1[0][1] == 'VAR'
    else:
        return False


def test_alpha_equiv(narr1, narr2, alpha={}):
    """
    测试表达式的替换相似性，在变量可以替换的情况下是否表达式结构相等。
    （不考虑内部顺序）
    """
    root1, root2 = narr1[0], narr2[0]
    sign1, sign2 = root1[0], root2[0]
    type1, type2 = root1[1], root2[1]

    alpha = deepcopy(alpha)

    if type1 == 'NUMBER':
        return type1 == type2 and sign1 == sign2 and narr1[1] == narr2[1], alpha
    elif type1 in ['VAR', 'WILDCARDS']:

        name1 = narr1[1]
        narr2 = deepcopy(narr2[:])

        #print(name1, sign1, sign2)
        #print(narr2)
        #print()

        if sign1 == '-' and sign2 == '+':
            narr2 = reverse_sign(narr2)
        elif sign1 == '+' and sign2 == '-':
            pass
        elif sign1 == '-' and sign2 == '-':
            narr2 = reverse_sign(narr2)

        if name1 in alpha and not narr_identical(alpha[name1], narr2):
            return False, alpha
        else:
            # uppercase pattern such as X, Y only match variables
            if name1.isupper() and not test_polynomial_var(narr2):
                return False, alpha
            else:
                alpha[name1] = narr2
                return True, alpha

    children_tokens = [c[0][1] for c in narr1[1:]]
    has_wildcards = ('WILDCARDS' in children_tokens)

    if not operator_identical(root1, root2):
        return False, alpha
    elif len(narr1[1:]) != len(narr2[1:]) and not has_wildcards:
        return False, alpha

    for i, c1 in enumerate(narr1[1:]):
        if 1 + i >= len(narr2): return False, alpha # safe-guard

        if c1[0][1] == 'WILDCARDS':
            # wildcards match
            c2 = [narr2[0]] + narr2[1 + i:]
            #rich.print('[yellow] wildcards match:[/]')
            #print(c1)
            #print(c2)
            #print()

            # ensure matched group is positive
            if sign2 == '-': c2 = reverse_sign(c2)
            # unwrap matched group if necessary
            if len(c2[1:]) == 1:
                c2 = c2[1]
        else:
            c2 = narr2[1 + i]

        is_instance, new_alpha = test_alpha_equiv(
            c1, c2, alpha=alpha
        )
        if not is_instance:
            return False, alpha
        else:
            alpha = new_alpha

    return True, alpha


def replace_or_pass_children(narr, i, substitute):
    """
    表达式 narr 的第 i 个子节点，用 substitute 替换。
    如果表达式有相同的 root 操作符，且满足交换律，则把两个表达式合并。
    """
    root = narr[0]
    sign, Type = root
    if Type == substitute[0][1] and Type in ['add', 'mul']:
        # pass children of commutative operators
        del narr[1 + i]
        narr += substitute[1:]
    else:
        # replacement at i
        narr[1 + i] = substitute
    return narr


def rewrite_by_alpha(narr, alpha):
    """
    按照重写规则 alpha 进行变量替换，重写表达式 narr
    """
    root = narr[0]
    sign, Type = root
    children = narr[1:]

    if Type in ['VAR', 'WILDCARDS']:
        name = children[0]
        subst = deepcopy(alpha[name])
        if sign == '+':
            return subst
        else:
            return reverse_sign(subst)

    elif Type == 'NUMBER':
        return deepcopy(narr)

    new_narr = [root]
    for i, c in enumerate(narr[1:]):
        substitute = rewrite_by_alpha(c, alpha)

        i = len(new_narr) - 1
        new_narr.append(None)
        replace_or_pass_children(new_narr, i, substitute)

        #print('[rewrite from]', expression.narr2tex(c))
        #print('[root]', root)
        #print('[alpha]', alpha)
        #print('[new_narr]', new_narr)
        #print()

    return new_narr


if __name__ == '__main__':
    narr1 = expression.tex2narr('\\frac{a}{b}')
    narr2 = expression.tex2narr('-\\frac{1+x}{x^{2}}')
    is_equiv, rewrite_rules = test_alpha_equiv(narr1, narr2)
    if is_equiv:
        print('alpha-equivalent')
        print(rewrite_rules)
    else:
        print('Not alpha-equivalent')
