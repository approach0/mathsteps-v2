import rich
import re
import itertools
import functools
import expression
from copy import deepcopy
from alpha_equiv import rewrite_by_alpha, test_alpha_equiv, alpha_prettyprint, replace_or_pass_children, get_wildcards_index


class Axiom:

    def __init__(self, recursive_apply=False, allow_complication=False, name=None):
        self.rules = {}
        self.dp = {}
        self.narrs = {}
        self.recursive_apply = recursive_apply
        self.allow_complication = allow_complication
        self._name = name
        self.tests = []


    def add_rule(self, src, dest, dynamic_procedure=None):
        dest = dest if isinstance(dest, list) else [dest]

        for dest_pattern in dest:
            A, B = self._preprocess(src, dest_pattern)

            for (a, b) in zip(A, B):
                if a not in self.rules:
                    self.rules[a] = b
                elif isinstance(self.rules[a], list):
                    self.rules[a].append(b)
                else:
                    self.rules[a] = [self.rules[a], b]

                self.dp[a] = dynamic_procedure

                # cache some results for speedup
                self.narrs[a] = expression.tex2narr(a)
                self.narrs[b] = expression.tex2narr(b)
        return self


    def add_test(self, expr, expect=None):
        if expect is None:
            self.tests.append((expr, None))
        elif isinstance(expect, list):
            self.tests.append((expr, expect))
        else:
            self.tests.append((expr, [expect]))
        return self


    def test(self, debug=False):
        if len(self.tests) == 0: print('[no test case]')
        for expr, expect in self.tests:
            rich.print('[bold cyan][[test]][/]', end=" ")
            print(expr)
            narr = expression.tex2narr(expr)
            possible_applied_narrs = self.apply(narr, debug=debug)
            for applied_narr in possible_applied_narrs:
                applied_tex = expression.narr2tex(applied_narr)
                print('[result]', applied_tex)
                if expect is not None:
                    if applied_tex in expect:
                        rich.print('[bold green]pass[/]')
                    else:
                        rich.print('[bold red]failed[/]')


    def __str__(self):
        retstr = self.name() + ':\n'
        for i, k in enumerate(self.rules):
            retstr += f'[{i}]: ' + k
            retstr += '\033[91m'
            retstr += '  =>  '
            retstr += '\033[0m'
            retstr += str(self.rules[k])

            if self.allow_complication:
                retstr += '\033[92m'
                retstr += ' allow_complication'
                retstr += '\033[0m'

            if self.recursive_apply:
                retstr += '\033[92m'
                retstr += ' recursive_apply'
                retstr += '\033[0m'

            if self.dp[k] is not None:
                retstr += '\033[91m'
                retstr += ' dynamic_rule'
                retstr += '\033[0m'

            if i != len(self.rules) - 1: retstr += '\n'
        return retstr


    def name(self):
        return 'Axiom (anonymous)' if self._name is None else f'{self._name}'


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
                dest_narr = [self.narrs[d] for d in dest] if isinstance(dest, list) else self.narrs[dest]
                call = self.dp[origin]
                if call is not None: # dynamical axiom
                    rewritten_narr, is_applied = call(pattern_narr, narr, rewrite_rules[0], dest_narr)
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


    def _children_permutation(self, narr, no_permute=False):
        root = narr[0]
        children = narr[1:]
        if len(children) == 1 or no_permute:
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
        wildcards_index = get_wildcards_index(narr)
        no_permute = (wildcards_index != None) or root_type in expression.no_permute_tokens()
        for construct_tree, brothers in self._children_permutation(narr, no_permute=no_permute):
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


    def apply(self, narr, debug=False, max_cnt=6):
        Q = [narr]
        final_narrs = []
        cnt = 0
        while len(Q) > 0:
            narr = Q.pop(0)
            narrs = self._onetime_apply(narr, debug=debug)
            if not self.recursive_apply:
                return narrs
            else:
                Q += narrs
                if len(narrs) == 0 and cnt > 0:
                    final_narrs.append(narr)
            if cnt + 1 >= max_cnt:
                break
            else:
                cnt += 1
        return final_narrs


if __name__ == '__main__':
    a = (
        Axiom(name='分子分母消除公因子', recursive_apply=True)
        .add_rule('# \\frac{# x *{1} }{# x *{2} }', '#1 \\frac{#2 *{1}}{#3 *{2}}')
        .add_rule('# \\frac{# x }{# x *{2} }', '#1 \\frac{#2 1}{#3 *{2}}')
        .add_rule('# \\frac{# x *{1} }{# x }', '#0 *{1}')
        .add_rule('# \\frac{# x }{# x }', '#0 1')

        .add_test('\\frac{-(a + b)}{a + b}')
    )

    a.test()
