import expression
import rich
import axiom
import state
from axiom import Axiom
from common_axioms import common_axioms

def possible_next_steps(narr, axioms, debug=False, restrict_rules=None, quick_return=False):
    return_steps = []
    if debug:
        tex = expression.narr2tex(narr)
        value = state.value(narr)
        rich.print(f'[light]{value:.2f}', end=' ') 
        print(tex)

    for axiom_idx, axiom in enumerate(axioms):
        possible_applied_narrs = axiom.apply(narr)

        value_constrain_narrs = []
        for applied_narr in possible_applied_narrs:
            if not axiom.allow_complication:
                curr_value = state.value(narr)
                next_value = state.value(applied_narr)
                if next_value < curr_value:
                    if debug:
                        rich.print('[grey50][[x]]', end=' ') 
                        tex = expression.narr2tex(applied_narr)
                        print(axiom.name(), tex)
                    continue
            value_constrain_narrs.append((applied_narr, axiom, axiom_idx))

        return_steps += value_constrain_narrs

        if quick_return and len(value_constrain_narrs) > 0: break

    return_steps.sort(key=lambda x: (x[2], -state.value(x[0])))

    if debug:
        for i, (narr, axiom, axiom_idx) in enumerate(return_steps):
            value = state.value(narr)
            if i == 0:
                rich.print(f'[bright_green][[✓]]', end=' ') 
            else:
                rich.print(f'[grey50][[ ]]', end=' ') 
            tex = expression.narr2tex(applied_narr)
            print(axiom.name(), end=" ")
            rich.print(f'[light]{value:.2f}', end=' ') 
            print(tex)
        print()
    return return_steps


def dfs(narr, axioms, debug=False):
    next_steps = [(narr, Axiom(name='原式'), -1)]
    return_steps = []
    while len(next_steps) > 0:
        narr, axiom, axiom_idx = next_steps[0]
        return_steps.append((narr, axiom, axiom_idx))
        next_steps = possible_next_steps(narr, axioms, quick_return=True, debug=debug)
    return return_steps


if __name__ == '__main__':
    all_axioms = common_axioms()
    test = expression.tex2narr('\\frac{12a}{3a + a + 20a} - \\frac{1}{4}')
    steps = dfs(test, all_axioms, debug=True)
    for narr, a, ai in steps:
        print(a.name(), '\n', expression.narr2tex(narr))