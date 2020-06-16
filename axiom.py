import rich
import re
import itertools
import functools
import expression
from copy import deepcopy
from alpha_equiv import rewrite_by_alpha, test_alpha_equiv, alpha_prettyprint, replace_or_pass_children


class Axiom:

    def __init__(self, recursive_apply=False, allow_complication=False, name=None):
        self.rules = {}
        self.narrs = {}
        self.recursive_apply = recursive_apply
        self.allow_complication = allow_complication
        self.contain_wildcards = False
        self.name = name
        self.tests = []


    def add_rule(self, a, b, direction='rewrite'):
        A, B = self._preprocess(a, b)
        for (a, b) in zip(A, B):
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
        return self


    def add_test(self, expr, expect=None):
        self.tests.append((expr, expect))
        return self


    def test(self, debug=False):
        if len(self.tests) == 0: print('[no test case]')
        for expr, expect in self.tests:
            rich.print('[bold cyan][[test]][/]', end=" ")
            print(expr)
            narr = expression.tex2narr(expr)
            applied_narr, if_applied = self._exact_apply(narr, debug=debug)
            if if_applied:
                applied_tex = expression.narr2tex(applied_narr)
                print('[applied]', applied_narr)
                print('[applied]', applied_tex)
                if expect is not None:
                    if applied_tex == expect:
                        rich.print('[bold green]pass[/]')
                    else:
                        rich.print('[bold red]failed[/]')
            else:
                print('[not applied]')


    def __str__(self):
        name = self.name
        retstr = 'Axiom (anonymous):\n' if name is None else f'{name}:\n'
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

            is_match, rewrite_rules = test_alpha_equiv(pattern_narr, narr, debug=False)

            if debug:
                rich.print('[red]pattern vs. narr')
                if False:
                    print('pattern:', pattern_narr)
                    print('subject:', narr)
                else:
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
    def _preprocess(a, b):
        n_var_sign = a.count('#')
        var_sign = []
        A, B = [], []

        for _ in range(n_var_sign):
            var_sign.append([+1, -1])

        for signs in itertools.product(*var_sign):
            if len(signs) == 0: break
            copy_a = a
            copy_b = b
            reduce_sign = functools.reduce((lambda x, y: x * y), signs)
            for i in range(n_var_sign):
                sign_a = '+' if signs[i] > 0 else '-'
                copy_a = copy_a.replace('#', sign_a, 1)

                def b_replace(m):
                    pound_num = m.group(1)
                    if pound_num == '0':
                        return '+' if reduce_sign > 0 else '-'
                    else:
                        extract_sign = signs[int(pound_num) - 1]
                        return '+' if extract_sign > 0  else '-'
                copy_b = re.sub(r'#([0-9])', b_replace, copy_b)
            A.append(copy_a)
            B.append(copy_b)

        if len(A) == 0 or len(B) == 0:
            return [a], [b]
        else:
            return A, B


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
                    # always positive new father, in case the negative
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
    # test-1
    #a = Axiom(recursive_apply=True)
    #a.add_rule('X *{1} + X *{2}', '(*{1} + *{2}) X')

    #test = expression.tex2narr('3ab^{2} + b^{2}2a')
    #possible_applied_narrs = a.apply(test, debug=True)
    #for narr in possible_applied_narrs:
    #    print(expression.narr2tex(narr))

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
    #a = Axiom(recursive_apply=False)
    #a.add_rule('0 \cdot *{1}', '0')

    #test = expression.tex2narr('12 \cdot 1 \cdot 0 \cdot 14')
    #possible_applied_narrs = a.apply(test, debug=True)
    #for narr in possible_applied_narrs:
    #    print(expression.narr2tex(narr))

    # test-6
    #a = Axiom(allow_complication=False, recursive_apply=False)
    #a.add_rule('(#a) (# b) (# c)', '#3 abc')
    #print(a)

    # test-7
    #a = Axiom(allow_complication=False, recursive_apply=False, name='分子分母消除')
    #a.add_rule('\\frac{x *{1} }{x *{2} }', '\\frac{*{1}}{*{2}}')
    #print(a)

    #test = expression.tex2narr('\\frac{2rx}{ry}')
    #test = expression.tex2narr('\\frac{xa}{ay}')
    #narr, _ = a._exact_apply(test, debug=False)
    #print(expression.narr2tex(narr))

    # test-8
    #a = Axiom(name='根号的平方是其本身')
    #a.add_rule('#(#\\sqrt{x})^{2}', '#1 x')
    #print(a)

    #test = expression.tex2narr('-(-\sqrt{3})^{2}')
    #narr, _ = a._exact_apply(test, debug=True)
    #print(expression.narr2tex(narr))


    #a = (Axiom(name='除以一个数等于乘上它的倒数', recursive_apply=True)
    #    .add_rule('# x \\div (# \\frac{y}{z})', '#0 \\frac{xz}{y}'))
    #test = expression.tex2narr('x \\div \\frac{1}{2}')
    #narr, _ = a._exact_apply(test, debug=True)
    #print(expression.narr2tex(narr))

    a = (Axiom(name='乘数的指数是各个因子指数的乘数', recursive_apply=True, allow_complication=True)
        .add_rule('# (# a *{1})^{k}', '#1 (#2 a)^{k} \\times (*{1})^{k}'))
    test = expression.tex2narr('(-3 a b)^{k}')
    possible_applied_narrs = a.apply(test, debug=False)
    for narr in possible_applied_narrs:
        print(expression.narr2tex(narr))
