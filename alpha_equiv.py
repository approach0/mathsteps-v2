import rich
import expression
from expression import NarrRoot
from copy import deepcopy


def narr_identical(narr1, narr2):
    root1, root2 = narr1[0], narr2[0]
    children1, children2 = narr1[1:], narr2[1:]

    if root1 != root2:
        return False
    elif len(children1) != len(children2):
        return False

    for c1, c2 in zip(children1, children2):
        is_identical = False
        if isinstance(c1, float) or isinstance(c1, str):
            is_identical = (c1 == c2)
        else:
            is_identical = narr_identical(c1, c2)

        if not is_identical:
            return False
    return True


def _apply_sign(narr, apply_product):
    """
    apply sign to `narr', distribute sign in addition case.
    """
    if apply_product > 0:
        return

    root = narr[0]
    old_sign, Type = root.get()
    narr[0].apply_sign(apply_product)

    if Type == 'add':
        # Distribute signs (i.e., make addition root positive)
        narr[:], _ = expression.passchildren(NarrRoot(+1, Type), [narr])


def children_wildcards_permutation(narr):
    """
    Generate O(n) number of permutations for wildcards matching
    """
    children = narr[1:]
    permutations = []
    for i, a in enumerate(children):
        brothers = [b for j, b in enumerate(children) if i != j]
        permutations.append([a, *brothers])
    return permutations


def alpha_universe_add_constraint(alpha_universe, name, narr):
    """
    Test constraint `alpha[name]=narr' against all alphas in alpha universe.
    Keep those not violating the new constraint.
    """
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
        print('test_alpha_equiv')
        #for alpha in alpha_universe:
        #    alpha_prettyprint(alpha)
        rich.print('[bold green]1[/]', end=" ")
        expression.narr_prettyprint(narr1)
        rich.print('[bold red]2[/]', end=" ")
        expression.narr_prettyprint(narr2)

    if type1 == 'NUMBER':
        return type1 == type2 and sign1 == sign2 and narr1[1] == narr2[1], alpha_universe

    elif type1 in ['VAR', 'WILDCARDS']:

        name1 = narr1[1] if type1 == 'VAR' else '*' + narr1[1]
        narr2 = deepcopy(narr2)

        # handle sign
        _apply_sign(narr2, sign1)

        #print(name1, end=' --> ')
        #print(narr2)
        #print()

        # uppercase pattern such as X, Y only match variables / polynomials
        if name1.isupper() and type2 not in ['VAR', 'sup']:
            return False, []
        # same variables must match same structures
        else:
            return alpha_universe_add_constraint(alpha_universe, name1, narr2)

    # quick test of identicalness for non-wildcards pattern
    wildcards_index = expression.get_wildcards_index(narr1)
    if root1 != root2:
        return False, []
    elif len(narr1[1:]) != len(narr2[1:]) and wildcards_index is None:
        return False, []

    alpha_universe_new = []
    # use exact order for concrete match or permuted order for wildcards match.
    # (the latter will possibly generate multiple universes/possibilities)
    permutations = [narr2[1:]] if wildcards_index == None else children_wildcards_permutation(narr2)
    for perm_children in permutations:
        match_perm = True # require all children get matched.
        alpha_universe_copy = deepcopy(alpha_universe)
        for i, c1 in enumerate(narr1[1:]):
            # safe-guard for long wildcards, e.g., 'abc*' matching 'ab'
            if i >= len(perm_children):
                match_perm = False
                break

            if c1[0][1] == 'WILDCARDS':
                # wildcards match (no sign reduce here)
                c2 = [NarrRoot(+1, type2)] + perm_children[i:]
                # unwrap matched group if necessary
                if len(c2[1:]) == 1:
                    c2 = c2[1]
            else:
                # concrete child match
                c2 = perm_children[i]

            # test subtree
            match_any, alpha_universe_copy = test_alpha_equiv(
                c1, c2, alpha_universe=alpha_universe_copy, debug=debug
            )

            if match_any:
                # stop early for wildcards match
                if c1[0][1] == 'WILDCARDS':
                    break
            else:
                match_perm = False
                break

        if match_perm:
            alpha_universe_new += alpha_universe_copy

    return len(alpha_universe_new) > 0, alpha_universe_new


def rewrite_by_alpha(narr, alpha):
    """
    按照重写规则 alpha 进行变量替换，重写表达式 narr
    """
    root = narr[0]
    sign, Type = root.get()
    children = narr[1:]

    if Type in ['VAR', 'WILDCARDS']:
        name = children[0] if Type == 'VAR' else "*" + children[0]
        subst = deepcopy(alpha[name])

        # if `x' is going to be replaced by `y', we need to keep `x' node animations
        subst[0].animation = root.animation
        subst[0].animatGrp = root.animatGrp

        _apply_sign(subst, sign)

        return subst

    elif Type == 'NUMBER':
        # number will not change, copy this number
        return deepcopy(narr)

    # construct new narr after children recursive replacement
    new_narr = [root.copy()]
    for i, c in enumerate(narr[1:]):
        child_root = c[0]
        substitute = rewrite_by_alpha(c, alpha)

        # if `x' is going to be replaced by `y', we need to keep `x' node animations
        substitute[0].animation = child_root.animation
        substitute[0].animatGrp = child_root.animatGrp

        #alpha_prettyprint(alpha)
        #print(c, '==>', substitute)

        # append substitute to new_narr, passing children if necessary
        i = len(new_narr) - 1
        new_narr.append(None)
        expression.replace_or_pass_children(new_narr, i, substitute)

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

    #narr1 = expression.tex2narr('x + x')
    #narr2 = expression.tex2narr('y^{2} + y^{2}')

    #narr1 = expression.tex2narr('x + K')
    #narr2 = expression.tex2narr('x - y^{2}')

    #narr1 = expression.tex2narr('x - *{1}')
    #narr2 = expression.tex2narr('x - 12 + 3')

    #narr1 = expression.tex2narr('(((3)(-2))(-1))')
    #narr2 = expression.tex2narr('3 \cdot 2 \cdot 1')

    #narr1 = expression.tex2narr('(-\\frac{x}{y})')
    #narr2 = expression.tex2narr('-\\frac{x}{y}')

    #narr1 = expression.tex2narr('-\\sqrt{x}^{2}')
    #narr2 = expression.tex2narr('-(\\sqrt{x})^{2}')

    #narr1 = expression.tex2narr('0 (-n)')
    #narr2 = expression.tex2narr('- 0 n')

    #narr1 = expression.tex2narr('-x \\times *{1} + x \\times *{2}')
    #narr2 = expression.tex2narr('-25 \\times 51 + 25 \\times 48')

    #narr1 = expression.tex2narr('+(-X)(-X)')
    #narr2 = expression.tex2narr('-yy')

    #narr1 = expression.tex2narr('a + *{1}')
    #narr1 = expression.tex2narr('- a - *{1}')
    narr1 = expression.tex2narr('-a')
    narr2 = [NarrRoot(1, 'add'),
            [NarrRoot(1, 'NUMBER'), 30.0],
            [NarrRoot(1, 'add'),
                [NarrRoot(1, 'NUMBER'), 1.0],
                [NarrRoot(1, 'NUMBER'), 3.0]
            ]
        ]

    is_equiv, rewrite_rules = test_alpha_equiv(narr1, narr2, debug=True)
    if is_equiv:
        rich.print('[bold green]Is alpha-equivalent')
        alpha = rewrite_rules[0]
        alpha_prettyprint(alpha)
        rewritten_narr = rewrite_by_alpha(narr1, alpha)
        rich.print('[[rewritten]]', expression.narr2tex(rewritten_narr))
    else:
        rich.print('[bold red]Not alpha-equivalent')
