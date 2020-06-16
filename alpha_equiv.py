import rich
import expression
from copy import deepcopy


def operator_identical(root1, root2, same_sign=True):
    if same_sign:
        return root1 == root2
    else:
        return root1[1] == root2[1]


def narr_identical(narr1, narr2, same_sign=True):
    """
    递归比较两个表达式 (nested arrary) 是否相等（按照顺序匹配，不考虑交换）
    """
    root1, root2 = narr1[0], narr2[0]
    children1, children2 = narr1[1:], narr2[1:]

    if not operator_identical(root1, root2):
        return False
    elif len(children1) != len(children2):
        return False

    for c1, c2 in zip(children1, children2):
        is_identical = False
        if isinstance(c1, float) or isinstance(c1, str):
            is_identical = (c1 == c2)
        else:
            is_identical = narr_identical(c1, c2, same_sign=same_sign)

        if not is_identical:
            return False
    return True


def apply_sign(narr, product):
    """
    表达式变号，从加号变成减号或者减号改成加号。加法会让每一项变号。
    """
    root = narr[0]
    old_sign, Type = root[0], root[1]
    if Type == 'add':
        for i, c in enumerate(narr[1:]):
            apply_sign(c, old_sign * product)
    else:
        narr[0] = (old_sign * product, Type)


def children_wildcards_permutation(narr):
    children = narr[1:]
    permutations = []
    for i, a in enumerate(children):
        brothers = [b for j, b in enumerate(children) if i != j]
        permutations.append([a, *brothers])
    return permutations


def alpha_universe_add_constraint(alpha_universe, name, narr):
    tmp_universe = deepcopy(alpha_universe)
    new_universe = []
    for alpha in tmp_universe:
        if name not in alpha or narr_identical(alpha[name], narr):
            alpha[name] = narr
            new_universe.append(alpha)
    return len(new_universe) > 0, new_universe


def test_alpha_equiv(narr1, narr2, alpha_universe=[{}], debug=False):
    root1, root2 = narr1[0], narr2[0]
    sign1, sign2 = root1[0], root2[0]
    type1, type2 = root1[1], root2[1]

    if debug:
        for alpha in alpha_universe:
            alpha_prettyprint(alpha)
        expression.narr_prettyprint(narr1)
        expression.narr_prettyprint(narr2)
        print()

    if type1 == 'NUMBER':
        return type1 == type2 and sign1 == sign2 and narr1[1] == narr2[1], alpha_universe

    elif type1 in ['VAR', 'WILDCARDS']:

        name1 = narr1[1] if type1 == 'VAR' else '*' + narr1[1]
        narr2 = deepcopy(narr2[:])

        # handle sign
        apply_sign(narr2, sign1 * sign2)

        # uppercase pattern such as X, Y only match variables
        if name1.isupper() and type2 == 'NUMBER':
            return False, []
        # same variables must match same structures
        else:
            return alpha_universe_add_constraint(alpha_universe, name1, narr2)

    children_tokens = [c[0][1] for c in narr1[1:]]
    try:
        wildcards_index = children_tokens.index('WILDCARDS')
    except ValueError:
        wildcards_index = None

    if not operator_identical(root1, root2):
        return False, []
    elif len(narr1[1:]) != len(narr2[1:]) and wildcards_index is None:
        return False, []

    alpha_universe_new = []
    permutations = [narr2[1:]] if wildcards_index == -1 else children_wildcards_permutation(narr2)
    for perm_children in permutations:
        match_perm = True
        alpha_universe_copy = deepcopy(alpha_universe)
        for i, c1 in enumerate(narr1[1:]):
            # safe-guard for long wildcards
            if i >= len(perm_children):
                match_perm = False
                break

            if c1[0][1] == 'WILDCARDS':
                # wildcards match
                c2 = [(+1, type2)] + perm_children[i:]
                # unwrap matched group if necessary
                if len(c2[1:]) == 1:
                    c2 = c2[1]
            else:
                c2 = perm_children[i]

            match_any, alpha_universe_copy = test_alpha_equiv(
                c1, c2, alpha_universe=alpha_universe_copy, debug=debug
            )

            if match_any:
                if c1[0][1] == 'WILDCARDS':
                    break
            else:
                match_perm = False
                break

        if match_perm:
            alpha_universe_new += alpha_universe_copy

    return len(alpha_universe_new) > 0, alpha_universe_new


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
        name = children[0] if Type == 'VAR' else "*" + children[0]
        subst = deepcopy(alpha[name])
        apply_sign(subst, sign)
        return subst

    elif Type == 'NUMBER':
        return deepcopy(narr)

    new_narr = [root]
    for i, c in enumerate(narr[1:]):
        substitute = rewrite_by_alpha(c, alpha)

        i = len(new_narr) - 1
        new_narr.append(None)
        replace_or_pass_children(new_narr, i, substitute)

    return new_narr


def alpha_prettyprint(alpha):
    print('rewrite rules:')
    if len(alpha) == 0:
        print('\t(empty)')
    else:
        for key in alpha:
            print(f'\t[{key}]:', end=' ')
            print(expression.narr2tex(alpha[key]))


if __name__ == '__main__':
    #narr1 = expression.tex2narr('\\frac{a}{b}')
    #narr2 = expression.tex2narr('\\frac{1+x}{x^{2}}')

    narr1 = expression.tex2narr('x + x')
    narr2 = expression.tex2narr('y^{2} + y^{2}')

    narr1 = expression.tex2narr('x + K')
    narr2 = expression.tex2narr('x - y^{2}')

    narr1 = expression.tex2narr('x + *{1}')
    narr2 = expression.tex2narr('x - 12 + 3')

    is_equiv, rewrite_rules = test_alpha_equiv(narr1, narr2)
    if is_equiv:
        print('alpha-equivalent')
        alpha_prettyprint(rewrite_rules[0])
    else:
        print('Not alpha-equivalent')
