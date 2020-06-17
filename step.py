import expression
import axiom
from axiom import Axiom
from common_axioms import common_axioms

def possible_next_steps(narr, axioms, debug=False, restrict_rules=None, fastmode=False):
    return_steps = []
    for ai, a in enumerate(axioms):
        possible_applied_narrs = a.apply(narr)
        if len(possible_applied_narrs) > 0:
            return_steps += [(narr, a, ai) for narr in possible_applied_narrs]
            if fastmode: break
    return return_steps


def dfs(narr, axioms, debug=False):
    next_steps = [(narr, Axiom(name='原式'), -1)]
    return_steps = []
    while len(next_steps) > 0:
        narr, axiom, axiom_idx = next_steps[0]
        return_steps.append((narr, axiom, axiom_idx))
        next_steps = possible_next_steps(narr, axioms, fastmode=True)
    return return_steps


if __name__ == '__main__':
    all_axioms = common_axioms()
    test = expression.tex2narr('\\frac{12a}{3a + a + 20a} - \\frac{1}{4}')
    steps = dfs(test, all_axioms)
    for narr, a, ai in steps:
        print(a.name(), '\t', expression.narr2tex(narr))
