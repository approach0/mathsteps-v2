import rich
import itertools
import expression
from alpha_equiv import rewrite_by_alpha, test_alpha_equiv, alpha_prettyprint

somelists = [
   [1, 2, 3],
   ['a', 'b'],
   [4, 5]
]

for element in itertools.product(*somelists):
    print(element)


class Axiom:

    def __init__(self, recursive_match=False, allow_complication=True):
        self.rules = {}
        self.narrs = {}
        self.recursive_match = recursive_match
        self.allow_complication = allow_complication


    def add_rule(self, a, b, direction='rewrite'):
        if direction == 'rewrite':
            self.rules[a] = b
        elif direction == 'converse':
            self.rules[b] = a
        elif direction == 'equivalence':
            self.rules[a] = b
            self.rules[b] = a
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

            if self.recursive_match:
                retstr += '\033[92m'
                retstr += ' recursive_match'
                retstr += '\033[0m'

            if i != len(self.rules) - 1: retstr += '\n'
        return retstr


    def match(self, narr, debug=False):
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


a = Axiom(recursive_match=True)
a.add_rule('a *{1} + a *{2}', '(*{1} + *{2})a')

b = expression.tex2narr('xaz + yaw')

a.match(b, debug=True)
