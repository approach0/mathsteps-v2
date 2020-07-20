import rich
import re
import itertools
import functools
import mathjs
import expression
from expression import NarrRoot
from copy import deepcopy
from alpha_equiv import rewrite_by_alpha, test_alpha_equiv, alpha_prettyprint
import numpy as np


class Axiom:

    def __init__(self, name=None, max_results=10,
        recursive_apply=False, root_sign_reduce=True, allow_complication=False, strict_simplify=False):

        self.rules = {}
        self.dp = {}
        self.animation = {}
        self.animation_mode = False
        self.narrs = {}
        self.signs = {}
        self.wildcards_idx = {}
        self.root_sign_reduce = root_sign_reduce
        self.recursive_apply = recursive_apply
        self.allow_complication = allow_complication
        self.strict_simplify = strict_simplify
        self._name = name
        self.tests = []
        self.max_results = max_results


    @staticmethod
    def _preprocess(a, b):
        n_var_sign = a.count('#')
        var_sign = []
        A, B, C = [], [], []

        for _ in range(n_var_sign):
            var_sign.append([+1, -1])

        for signs in itertools.product(*var_sign):
            if len(signs) == 0: break
            copy_a = a
            copy_b = b
            reduce_sign = functools.reduce((lambda x, y: x * y), signs)
            for i in range(n_var_sign):
                # replace sharps in a
                sign_a = '+' if signs[i] > 0 else '-'
                copy_a = copy_a.replace('#', sign_a, 1)

                # replace sharps in b
                def b_replace(m):
                    reverse_sign = m.group(1)
                    t = -1 if reverse_sign == '~' else +1

                    pound_num = m.group(2)
                    if pound_num == '0':
                        return '+' if (reduce_sign * t) > 0 else '-'
                    else:
                        extract_sign = signs[int(pound_num) - 1]
                        return '+' if (extract_sign * t) > 0  else '-'
                copy_b = re.sub(r'#(~?)([0-9])', b_replace, copy_b)

            A.append(copy_a)
            B.append(copy_b)
            C.append(signs)

        if len(A) == 0 or len(B) == 0:
            return [a], [b], [()]
        else:
            return A, B, C


    def add_rule(self, src, dest, dynamic_procedure=None, animation=None):
        dests = dest if isinstance(dest, list) else [dest]

        for i, dest_output in enumerate(dests):
            A, B, C = self._preprocess(src, dest_output)

            for (a, b, signs) in zip(A, B, C):
                if a not in self.rules:
                    self.rules[a] = b
                elif isinstance(self.rules[a], list):
                    self.rules[a].append(b)
                else:
                    self.rules[a] = [self.rules[a], b]

                self.dp[a] = dynamic_procedure
                self.signs[a] = signs

                # cache some results for speedup
                self.narrs[a] = expression.tex2narr(a)
                self.narrs[b] = expression.tex2narr(b)
                self.wildcards_idx[a] = expression.get_wildcards_index(self.narrs[a])

            if animation:
                ani_output = animation[i] if isinstance(dest, list) else animation
                A, B, _ = self._preprocess(src, ani_output)
                for (a, b) in zip(A, B):
                    if a not in self.animation:
                        self.animation[a] = b
                    elif isinstance(self.animation[a], list):
                        self.animation[a].append(b)
                    else:
                        self.animation[a] = [self.animation[a], b]

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


    def test(self, tex=None, debug=False, render=True, printNarr=False, printTrim=False, printJSON=False):
        # construct test pairs (TeX, expected TeX)
        tests = self.tests if tex is None else [(tex, None)]
        if len(tests) == 0: print('[no test case]')
        # test through each testcase for this axiom ...
        for test, expect in tests:
            expr = test if isinstance(test, str) else expression.narr2tex(test)
            narr = expression.tex2narr(expr) if isinstance(test, str) else test
            results = self.apply(narr, debug=debug)
            # render texs is for HTML preview
            render_texs = [expr]

            rich.print('[bold cyan][[test]][/]', end=" ")
            print(expr)
            #if printNarr:
            #    expression.narr_prettyprint(narr)

            for applied_narr, ani_narr in results:
                # print transition animations
                if ani_narr:
                    ani_tex = expression.narr2tex(ani_narr)
                    rich.print('[bold cyan][[transition]][/]', end=" ")
                    print(ani_tex)
                else:
                    rich.print('[bold cyan][[transition]][/]', None)

                # print result expression
                applied_tex = expression.narr2tex(applied_narr)
                rich.print('[bold cyan][[result]][/]', end=" ")
                print(applied_tex, end=" ")
                if expect is not None:
                    if applied_tex in expect:
                        rich.print('[bold green]pass[/]')
                    else:
                        rich.print('[bold red]failed[/]')
                else:
                    print()

                # render texs is for HTML preview
                render_texs.append(applied_tex)

                if printNarr:
                    rich.print("[red]narr[/]:")
                    expression.narr_prettyprint(applied_narr)

                if printTrim:
                    rich.print("[red]trim[/]:")
                    expression.trim_animations(applied_narr)
                    expression.narr_prettyprint(applied_narr)

                if printJSON:
                    rich.print('[red]JSON[/]:')
                    json = mathjs.tex2json(applied_tex, indent=4)
                    print(json)

            if render:
                import render_math
                render_math.render_equations(render_texs)


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

            if self.strict_simplify:
                retstr += '\033[92m'
                retstr += ' strict_simplify'
                retstr += '\033[0m'

            if self.recursive_apply:
                retstr += '\033[92m'
                retstr += ' recursive_apply'
                retstr += '\033[0m'

            if not self.root_sign_reduce:
                retstr += '\033[92m'
                retstr += ' no-root_sign_reduce'
                retstr += '\033[0m'

            if self.dp[k] is not None:
                retstr += '\033[91m'
                retstr += ' dynamic_rule'
                retstr += '\033[0m'

            if k in self.animation:
                retstr += '\033[94m'
                retstr += (' animation: %s' % self.animation[k])
                retstr += '\033[0m'

            if i != len(self.rules) - 1: retstr += '\n'
        return retstr


    def name(self):
        return 'Axiom (anonymous)' if self._name is None else self._name


    @staticmethod
    def _extract_weight(narr):
        sign, Type = narr[0].get()
        if Type == 'mul':
            num = sign
            for c in narr[1:]:
                if c[0][1] == 'NUMBER':
                    w = Axiom()._extract_weight(c)
                    if w is None:
                        continue
                    num *= w
            return num
        elif Type == 'NUMBER':
            num = narr[1]
            if num.is_integer():
                num_sign, _ = narr[0].get()
                return num_sign * num
            else:
                return None
        else:
            return None


    @staticmethod
    def _extract_weights(narr):
        _, Type = narr[0].get()
        if Type == 'add':
            return [Axiom()._extract_weight(c) for c in narr[1:]]
        elif Type in ['mul', 'NUMBER']:
            return [Axiom()._extract_weight(narr)]
        else:
            return [None]


    @staticmethod
    def _restore_weights(weights, narr):
        def gen_num(n):
            return [NarrRoot(+1 if n >= 0 else -1, 'NUMBER'), float(abs(n))]
        children = narr[1:] if narr[0][1] == 'add' else [narr]
        for i, c in enumerate(children):
            sign, Type = c[0].get()
            # turn to positive term
            c[0].set(+1, Type)
            if Type == 'NUMBER':
                w = weights[i]
                children[i] = gen_num(w)
            elif Type == 'mul':
                # remove numbers
                c[1:] = [gc for gc in c[1:] if gc[0][1] != 'NUMBER' or not gc[1].is_integer()]
                # insert weight if it is non-one value
                w = weights[i]
                if w != 1:
                    children[i] = [c[0].copy()] + [gen_num(w)] + c[1:]
                    c = children[i]
                # trim the tree if it has zero or only one operand
                if len(c) == 1:
                    children[i] = gen_num(w)
                elif len(c) == 2:
                    children[i] = c[1]
        if narr[0][1] == 'add':
            narr[1:] = children
        else:
            narr[:] = children[0]


    @staticmethod
    def _fraction_cancel(narr, debug=False):
        sign, Type = narr[0].get()
        if Type != 'frac':
            return narr

        # extract weights
        numerator_weights = Axiom()._extract_weights(narr[1])
        if any([x is None for x in numerator_weights]):
            return narr

        denominator_weights = Axiom()._extract_weights(narr[2])
        if any([x is None for x in denominator_weights]):
            return narr

        # cancel weights
        L = len(numerator_weights)
        weights = np.array(numerator_weights + denominator_weights, dtype=int)
        gcd = np.gcd.reduce(weights)
        weights = (weights // gcd).tolist()

        # restore weights
        numerator_weights = weights[:L]
        denominator_weights = weights[L:]

        if debug:
            rich.print('[yellow]cancel fraction:',  expression.narr2tex(narr))
            print('numerator:', numerator_weights)
            print('denominator:', denominator_weights)

        Axiom()._restore_weights(numerator_weights, narr[1])
        Axiom()._restore_weights(denominator_weights, narr[2])

        if debug:
            rich.print('[yellow]after:',  expression.narr2tex(narr))
            expression.narr_prettyprint(narr)
        return narr


    def _exact_apply(self, pattern, narr, debug=False):
        # refuse to apply when rule is not animation compatible in animation mode.
        if self.animation_mode and pattern not in self.animation:
            return narr, False

        # apply pattern transformation to nested array
        pattern_narr = self.narrs[pattern]
        is_match, rewrite_rules = test_alpha_equiv(pattern_narr, narr, debug=False)

        if debug:
            # Example:
            # Axiom: (a+b)(a-b) => (a)^{2} - (b)^{2}
            #          pattern   =>  destination
            # narr: (-xy - z)(-xy + z)
            # rewrite_rules:
            #    a -> -xy
            #    b -> -z
            print()
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

            dest = self.animation[pattern] if self.animation_mode else self.rules[pattern]
            dest_narr = [self.narrs[d] for d in dest] if isinstance(dest, list) else self.narrs[dest]

            if debug:
                print('dest:', dest)

            call = self.dp[pattern]
            if call is not None: # dynamical axiom
                signs = self.signs[pattern]
                rewritten_narr, is_applied = call(pattern_narr, signs, narr, rewrite_rules[0], dest_narr)
            else:
                rewritten_narr, is_applied = rewrite_by_alpha(dest_narr, rewrite_rules[0]), True

            if debug:
                rich.print('applied:', is_applied, end=': ')
                if False:
                    print(rewritten_narr)
                else:
                    print(expression.narr2tex(rewritten_narr))

            # if a rule with higher priority get applied, later ones are ignored
            if is_applied:
                # post processes
                rewritten_narr = self._fraction_cancel(rewritten_narr)
                return rewritten_narr, True

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


    def _children_permutation(self, narr, no_permute=False):
        root = narr[0]
        children = narr[1:]
        animation_tree = None
        if len(children) == 1 or no_permute:
            # generate unary operations
            construct_tree = deepcopy(narr)
            yield construct_tree, [], animation_tree
        else:
            is_commutative = True if root[1] in expression.commutative_operators() else False
            # generate binary operations
            for (cl, cr), (i, j) in self._children_choose_two(children, is_commutative):
                construct_tree = [root.copy(), cl, cr]

                if self.animation_mode and (i > 1 or j > 1):
                    children_copy = deepcopy(children)
                    construct_copy = deepcopy(construct_tree)

                    children_copy[i][0].animation = 'moveBefore'
                    children_copy[i][0].animatGrp = 1

                    children_copy[j][0].animation = 'moveBefore'
                    children_copy[j][0].animatGrp = 2

                    construct_copy[1][0].animation = 'moveAfter'
                    construct_copy[1][0].animatGrp = 1

                    construct_copy[2][0].animation = 'moveAfter'
                    construct_copy[2][0].animatGrp = 2

                    animation_tree = construct_copy + children_copy

                brothers = [c for k, c in enumerate(children) if k != i and k != j and j >= 0]
                yield deepcopy(construct_tree), deepcopy(brothers), animation_tree


    @staticmethod
    def _uniq_append(result_narrs, new_narr, max_results):
        full = False
        if len(result_narrs) + 1 > max_results:
            return True, False
        applied_set = set([expression.narr2tex(narr) for narr in result_narrs])
        new_tex = expression.narr2tex(new_narr)
        append = False
        if new_tex not in applied_set:
            result_narrs.append(new_narr)
            append = True
        return full, append


    def _level_apply(self, narr, debug=False):
        ret_narrs = [] # store possible results
        ani_narrs = [] # store transition animations
        root_sign, root_type = narr[0].get()

        # ignore terminal tokens (no rule has a single terminal token as pattern)
        if root_type in expression.terminal_tokens():
            return [], []

        for pattern in self.rules:
            wildcards_idx = self.wildcards_idx[pattern]
            no_permute = (wildcards_idx != None) or root_type in expression.no_permute_tokens()

            if debug: rich.print(f'\n[red]level apply[/] {pattern} wildcards_idx={wildcards_idx},' +
                f' no_permute={no_permute} [red]to[/]', expression.narr2tex(narr))

            # extract and try partial one or two operands to match against pattern
            for construct_tree, brothers, ani_tree in self._children_permutation(narr, no_permute=no_permute):
                rewritten_narr, is_applied = self._exact_apply(pattern, construct_tree, debug=debug)
                if is_applied:
                    new_narr = [] # construct a new father
                    if len(brothers) > 0:
                        if self.root_sign_reduce:
                            # always positive new father, in case the negative
                            # sign of father is also reduced, e.g. -abc => (ab)c
                            new_root = NarrRoot(+1, root_type)
                        else:
                            # in addition case, we will need to keep father sign,
                            # e.g. -(1+2+3) => -(3+3)
                            new_root = NarrRoot(root_sign, root_type)

                        new_narr = [new_root, None, *brothers]
                        expression.replace_or_pass_children(new_narr, 0, rewritten_narr)
                    else:
                        # the entire expression in this level gets reduced
                        new_narr = rewritten_narr
                        if not self.root_sign_reduce and root_sign < 0:
                            new_narr[0].apply_sign(-1)

                    #print('[animat]', expression.narr2tex(ani_tree))
                    #print('[result]', expression.narr2tex(new_narr))
                    #print()
                    if False:
                        rich.print('[red]level apply[/]:')
                        print('[origin]', expression.narr2tex(narr))
                        print('[pattern]', pattern)
                        print('[result]', expression.narr2tex(new_narr))
                        print()

                    _, append = Axiom()._uniq_append(ret_narrs, new_narr, self.max_results)
                    if append: ani_narrs.append(ani_tree)
        return ret_narrs, ani_narrs


    def _recursive_apply(self, narr0, debug=False, applied_times=0, max_times=4, bfs_bandwith=5, level=0):
        # safe guard
        if applied_times >= max_times:
            return []

        # apply at this level for max_times
        Q = [(applied_times, narr0)]
        candidates = [(applied_times, narr0)]
        while len(Q) > 0:
            depth, narr = Q.pop(0)
            if depth >= max_times:
                #rich.print('[red]maxtime[/]', depth)
                break

            narrs, _ = self._level_apply(narr, debug=debug)

            # keep adding next level or dead ends to candidates
            if len(narrs) > 0:
                tmp = [(depth + 1, n) for n in narrs]
                candidates += tmp
            elif depth > applied_times:
                candidates.append((depth, narr))
                continue
            else:
                continue

            # update Q
            Q += tmp
            if len(Q) > bfs_bandwith:
                Q = Q[-bfs_bandwith:]

        #if True:
        #    print(expression.narr2tex(narr0))
        #    for d,n in candidates:
        #        print(f'candidate: {d}/{max_times}:', expression.narr2tex(n))
        #    print()

        # for recursive sub-expressions
        result_narrs = []
        for depth, narr in candidates:
            _, root_type = narr[0].get()
            none_applied = True

            # has any sub-tree ?
            if root_type not in expression.terminal_tokens():
                children = narr[1:]
                for i, child in enumerate(children):
                    applied_narrs = self._recursive_apply(child, debug=debug, level=level+1,
                        applied_times=depth, max_times=max_times, bfs_bandwith=bfs_bandwith)

                    #if len(applied_narrs) > 1:
                    #    print(expression.narr2tex(child))
                    #    for n in applied_narrs:
                    #        print('=>', expression.narr2tex(n))
                    #    print()

                    for applied_narr in applied_narrs:
                        none_applied = False
                        # substitute with sub-routine expression
                        new_narr = deepcopy(narr)
                        expression.replace_or_pass_children(new_narr, i, applied_narr)

                        # append new result
                        full, _ = Axiom()._uniq_append(result_narrs, new_narr, self.max_results)
                        if full: return result_narrs
            # append dead-end result
            if none_applied and depth > 0:
                new_narr = deepcopy(narr)
                full, _ = Axiom()._uniq_append(result_narrs, new_narr, self.max_results)
                if full: return result_narrs

        #if level == 0:
        #    for n in result_narrs:
        #        print(f'{level}>', expression.narr2tex(n))
        #    print()
        return result_narrs


    @staticmethod
    def _print_results_in_tex(narrs):
        for n in narrs:
            print(expression.narr2tex(n))
        print()


    def _onetime_apply(self, narr0, debug=False):
        if narr0[0][1] in expression.terminal_tokens():
            return []

        # apply at this level
        applied_narrs, ani_narrs = self._level_apply(narr0, debug=debug)
        if len(applied_narrs) > 0:
            return zip(applied_narrs, ani_narrs)

        # apply to children recursively
        children = narr0[1:]
        results = []
        for i, child in enumerate(children):
            applied_tuples = self._onetime_apply(child, debug=debug)
            for narr, ani_narr in applied_tuples:
                # attach applied subexpression
                new_res_narr = deepcopy(narr0)
                expression.replace_or_pass_children(new_res_narr, i, narr)
                # attach applied transition animation
                new_ani_narr = None
                if ani_narr:
                    new_ani_narr = deepcopy(narr0)
                    expression.replace_or_pass_children(new_ani_narr, i, ani_narr)
                # append to results
                results.append((new_res_narr, new_ani_narr))
            # only apply once in this function
            if len(results) > 0:
                break

        return results


    def apply(self, narr, debug=False):
        if self.recursive_apply and not self.animation_mode:
            results = self._recursive_apply(narr, debug=debug)
            return [(r, None) for r in results]
        else:
            return self._onetime_apply(narr, debug=debug)


if __name__ == '__main__':
    import dynamic_axioms
    #a = (
    #    Axiom(name='分母为一的分式化简')
    #    .add_rule('#\\frac{k}{#1}', '#0 k', animation='`#1 \\frac{k}{#2 1}`[replace]{#0 k}')
    #)
    a = dynamic_axioms.calc_add

    a.animation_mode = True
    print(a)

    a.test('2 + 7 + 8', debug=False, printNarr=False, printTrim=False)
    #a.test(debug=True, printNarr=True, printTrim=True)
