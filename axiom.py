import rich
import itertools
import expression
from copy import deepcopy
from alpha_equiv import rewrite_by_alpha, test_alpha_equiv, alpha_prettyprint, replace_or_pass_children

somelists = [
   [1, 2, 3],
   ['a', 'b'],
   [4, 5]
]

for element in itertools.product(*somelists):
    print(element)


class Axiom:

    def __init__(self, recursive_apply=False, allow_complication=True):
        self.rules = {}
        self.narrs = {}
        self.recursive_apply = recursive_apply
        self.allow_complication = allow_complication
        self.contain_wildcards = False


    def add_rule(self, a, b, direction='rewrite'):
        if direction == 'rewrite':
            self.rules[a] = b
            if '*' in a: self.contain_wildcards = True
        elif direction == 'converse':
            self.rules[b] = a
            if '*' in b: self.contain_wildcards = True
        elif direction == 'equivalence':
            self.rules[a] = b
            self.rules[b] = a
            if '*' in a: self.contain_wildcards = True
            if '*' in b: self.contain_wildcards = True
        else:
            raise Exception('bad binary relation direction')

        # cache some results for speedup
        self.narrs[a] = expression.tex2narr(a)
        if not callable(b):
            self.narrs[b] = expression.tex2narr(b)


    def __str__(self):
        retstr = ''
        for i, k in enumerate(self.rules):
            if callable(self.rules[k]):
                retstr += f'rule[{i}]: ' + k
                retstr += '\033[90m'
                retstr += ' dynamical axiom'
                retstr += '\033[0m'
            else:
                retstr += f'[{i}]: ' + k
                retstr += '\033[91m'
                retstr += '  =>  '
                retstr += '\033[0m'
                retstr += self.rules[k]

            if self.allow_complication:
                retstr += '\033[92m'
                retstr += ' allow_complication'
                retstr += '\033[0m'

            if self.recursive_apply:
                retstr += '\033[92m'
                retstr += ' recursive_apply'
                retstr += '\033[0m'

            if i != len(self.rules) - 1: retstr += '\n'
        return retstr


    def _exact_apply(self, narr, debug=False):
        for origin in self.rules:
            # Example:
            # Axiom: (a+b)(a-b) => (a)^{2} - (b)^{2}
            #          origin   =>  destination
            # narr: (-xy - z)(-xy + z)
            # rewrite_rules:
            #    a -> -xy
            #    b -> -z
            pattern_narr = self.narrs[origin] # pattern

            is_match, rewrite_rules = test_alpha_equiv(pattern_narr, narr)

            if debug:
                rich.print('[red]pattern vs. narr')
                print('pattern:', expression.narr2tex(pattern_narr))
                print('subject:', expression.narr2tex(narr))
                rich.print('match:', is_match)

            if is_match:
                if debug:
                    alpha_prettyprint(rewrite_rules[0])

                dest = self.rules[origin]
                if callable(dest): # dynamical axiom
                    rewritten_narr, is_applied = dest(pattern_narr, narr, rewrite_rules[0])
                else:
                    # apply rewrite rules to destination expression. E.g., (a)^{2} - (b)^{2}
                    dest_narr = self.narrs[dest]
                    rewritten_narr, is_applied = rewrite_by_alpha(dest_narr, rewrite_rules[0]), True
                # only return when rule is actually applied
                if is_applied:
                    return rewritten_narr, is_applied
        return narr, False


    @staticmethod
    def _children_choose_two(children, is_commutative):
        """
        选取一对子表达式的组合

        1. 符合交换律的，会输出全组合
        2. 不符合交换律的，会输出顺序对

        """
        if is_commutative:
            for i, a in enumerate(children):
                for j, b in enumerate(children[i+1:]):
                    yield (a, b), (i, i + j + 1)
                    yield (b, a), (i + j + 1, i)
        else:
            for i, a in enumerate(children):
                if i + 1 < len(children):
                    b = children[i + 1]
                    yield (a, b), (i, i + 1)


    def _children_permutation(self, narr):
        root = narr[0]
        children = narr[1:]
        print(self.contain_wildcards)
        if self.contain_wildcards or len(children) == 1:
            # generate unary operations
            construct_tree = deepcopy(narr)
            yield construct_tree, []
        else:
            is_commutative = True if root[1] in expression.commutative_operators() else False
            # generate binary operations
            for (cl, cr), (i, j) in self._children_choose_two(children, is_commutative):
                construct_tree = deepcopy([root, cl, cr])
                brothers = [c for k, c in enumerate(children) if k != i and k != j and j >= 0]
                brothers = deepcopy(brothers)
                yield construct_tree, brothers


    @staticmethod
    def _uniq_append(possible_applied_narrs, new_narr):
        applied_set = set([expression.narr2tex(narr) for narr in possible_applied_narrs])
        new_tex = expression.narr2tex(new_narr)
        if new_tex not in applied_set:
            possible_applied_narrs.append(new_narr)


    def _onetime_apply(self, narr, debug=False):
        possible_applied_narrs = []
        tex_set = set()
        root_sign, root_type = narr[0]

        # for recursive sub-expressions
        if root_type not in expression.terminal_tokens():
            children = deepcopy(narr[1:])
            for i, child in enumerate(children):
                applied_narrs = self._onetime_apply(child, debug=debug)
                for applied_narr in applied_narrs:
                    # substitute with sub-routine expression
                    new_narr = deepcopy(narr)
                    replace_or_pass_children(new_narr, i, applied_narr)
                    # append result
                    Axiom()._uniq_append(possible_applied_narrs, new_narr)

        # match in this level
        for construct_tree, brothers in self._children_permutation(narr):
            rewritten_narr, is_applied = self._exact_apply(construct_tree, debug=debug)
            if is_applied:
                new_narr = [] # construct a new father
                if len(brothers) > 0:
                    # always postive new father, in case the negative
                    # sign of father is also reduced, e.g. -abc => (ab)c
                    positive_root = (+1, root_type)
                    new_narr = [positive_root] + [rewritten_narr] + brothers
                else:
                    # the entire expression in this level gets reduced
                    new_narr = rewritten_narr
                # append result
                Axiom()._uniq_append(possible_applied_narrs, new_narr)

        return possible_applied_narrs

    def apply(self, narr, debug=False):
        Q = [narr]
        final_narrs = []
        cnt = 0
        while len(Q) > 0:
            narr = Q.pop(0)
            narrs = self._onetime_apply(narr, debug=debug)
            if len(narrs) == 0:
                final_narrs.append(narr)
            elif not self.recursive_apply:
                return narrs
            else:
                Q += narrs
            cnt += 1
        return final_narrs


if __name__ == '__main__':
    ## test-1
    #a = Axiom(recursive_apply=True)
    #a.add_rule('a *{1} + a *{2}', '(*{1} + *{2})a')

    #test = expression.tex2narr('xaz + yaw')
    #a._exact_apply(test, debug=True)

    # test-2
    #a = Axiom(recursive_apply=True)
    #a.add_rule('\\frac{x}{y} + *{1} = z', 'x + *{1} y = z y')

    #test = expression.tex2narr('x + \\frac{x}{2} + 1 = 3')
    #possible_applied_narrs = a.apply(test, debug=True)
    #for narr in possible_applied_narrs:
    #    print(expression.narr2tex(narr))

    # test-3
    #a = Axiom(recursive_apply=True)
    #a.add_rule('a+0', 'a')

    #test = expression.tex2narr('x + 1 + 0 + 2 = 3')
    #possible_applied_narrs = a.apply(test, debug=False)
    #for narr in possible_applied_narrs:
    #    print(expression.narr2tex(narr))

    # test-4
    #a = Axiom(recursive_apply=True)
    #a.add_rule('a(x + *{1})', 'ax + a *{1}')

    #test = expression.tex2narr('3(a + b + c + x) + 1')
    #possible_applied_narrs = a.apply(test, debug=False)
    #for narr in possible_applied_narrs:
    #    print(expression.narr2tex(narr))

    # test-5
    a = Axiom(recursive_apply=False)
    a.add_rule('0 \cdot *{1}', '0')

    test = expression.tex2narr('12 \cdot 1 \cdot 0 \cdot 14')
    possible_applied_narrs = a.apply(test, debug=True)
    for narr in possible_applied_narrs:
        print(expression.narr2tex(narr))
