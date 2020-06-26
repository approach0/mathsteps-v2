import expression
import rich
import axiom
import state
import sys
from axiom import Axiom
from timer import Timer
from common_axioms import common_axioms

def possible_next_steps(narr, axioms, state_value,
                        debug=False, restrict_rules=None, fast_return=False):
    return_steps = []
    if debug:
        tex = expression.narr2tex(narr)
        value = state_value(narr)
        rich.print(f'[light]{value:.2f}', end=' ')
        print(tex)

    for axiom_idx, axiom in enumerate(axioms):
        possible_applied_narrs = axiom.apply(narr)
        #print(axiom.name(), len(possible_applied_narrs))

        value_constrain_narrs = []
        for applied_narr in possible_applied_narrs:
            if not axiom.allow_complication:
                curr_value = state_value(narr)
                next_value = state_value(applied_narr)
                if ((axiom.strict_simplify and next_value <= curr_value) or
                   next_value < curr_value):
                    if debug:
                        rich.print('[grey50][[x]]', end=' ')
                        value = state_value(applied_narr)
                        tex = expression.narr2tex(applied_narr)
                        print(axiom.name(), end=' ')
                        rich.print(f'[light]{value:.2f}', end=' ')
                        print(tex)
                    continue
            value_constrain_narrs.append((applied_narr, axiom, axiom_idx))

        return_steps += value_constrain_narrs

        if fast_return and len(value_constrain_narrs) > 0: break

    return_steps.sort(key=lambda x: (x[2], -state_value(x[0])))

    if debug:
        for i, (narr, axiom, axiom_idx) in enumerate(return_steps):
            # print axiom name
            if i == 0:
                rich.print(f'[bright_green][[✓]]', end=' ')
            else:
                rich.print(f'[grey50][[ ]]', end=' ')
            print(axiom.name(), end=" ")
            # print value
            value = state_value(narr)
            rich.print(f'[light]{value:.2f}', end=' ')
            # print tex
            tex = expression.narr2tex(narr)
            print(tex)
        print()
    return return_steps


def dfs(narr, axioms, debug=False, maxsteps=150):
    any_err = False
    try:
        next_steps = [(narr, Axiom(name='原式'), -1)]
        return_steps = []
        cnt = 0
        while len(next_steps) > 0:
            narr, axiom, axiom_idx = next_steps[0]
            return_steps.append((narr, axiom, axiom_idx))
            next_steps = possible_next_steps(narr, axioms, state.value_v1,
                                             fast_return=True, debug=debug)
            if cnt > maxsteps:
                any_err = True
                break
            cnt += 1
    except KeyboardInterrupt:
        pass

    return return_steps, any_err


def test():
    from render_math import render_steps
    from test_cases import test_cases_x3_rational, test_cases_wiki131278697

    all_axioms = common_axioms()

    testcases = []

    tmp, _ = test_cases_x3_rational()
    testcases += tmp

    tmp, _ = test_cases_wiki131278697()
    testcases += tmp

    testcases += [
        '\\frac{12a}{3a + a + 20a} - \\frac{1}{4}',
        '1 + \\frac{7}{3}',
        '4 -3 \\frac{1}{2}',
        '\\frac{(-3)^{3}}{2 \cdot \\frac{1}{4} \cdot (-\\frac{2}{3})^{2}} + 4 -4 \cdot \\frac{1}{3}',
        '\\frac{11}{2} (- \\frac{1}{6}) \\frac{3}{11} \\frac{4}{3}',
        'a - x^{2} + x^{2} \\times 0.609 + 1 = 0',

        "25 \cdot 48 + 103 \cdot 25 - 25 \cdot 51",
        "-13 \\times \\frac{2}{3} - 0.34 \\frac{2}{7} + \\frac{1}{3}(-13) - \\frac{5}{7} 0.34",
        '(-3\\frac{1}{3})\div2\\frac{1}{3}\\times\\frac{7}{10}',

        "(-18) \div ((2\\frac{1}{4}) \\times (1 - \\frac{3}{4}))",

        #"(-3 - \\frac{4}{17}) (14\\frac{13}{15}) - (3\\frac{4}{17}) (2 + \\frac{2}{15})",
        "b + 3x^{2} +2b + 3b + x^{2}= 0"
        "(3 + \\frac{4}{17}) (-14\\frac{13}{15} - \\frac{2}{15}) - 2 \times 3 - 2 \\times \\frac{4}{17}",
        "(-2 - \\frac{2}{15} - 14\\frac{13}{15}) (3 + \\frac{4}{17})"
    ]


    if True:
        all_axioms = common_axioms(full=True)
        narr = expression.tex2narr(testcases[-1])
        next_steps = possible_next_steps(narr, all_axioms, state.value_v2, debug=True)
        render_steps(next_steps)
        quit()

    begin_from = 0

    n_steps = 0
    timer = Timer()

    #for i, test in enumerate(testcases):
    for i, test in enumerate(testcases[-1:]):
        if i < begin_from: continue

        test_narr = expression.tex2narr(test)

        with timer:
            steps, err = dfs(test_narr, all_axioms, debug=True)
            if err:
                print('DFS error!')
                render_steps(steps)
                quit()

        for narr, a, ai in steps:
            rich.print(f'[red]{a.name()}')
            print('\t', expression.narr2tex(narr))
            #print(narr, end='\n\n')

        render_steps(steps)

        n_steps += len(steps)
        print(f'steps: {len(steps)}')
        print(f'test case: {i} / {len(testcases)}')

        #input('Enter to continue...')

    timer.show_stats(n_steps=n_steps)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) > 0:
        tex = args[0]
        narr = expression.tex2narr(tex)
        all_axioms = common_axioms()
        steps = dfs(narr, all_axioms, debug=False)

        steps = [
            {
                'tex': expression.narr2tex(narr),
                'axiom': a.name(),
                'axiom_idx': ai
            }
        for narr, a, ai in steps]

        import json
        print(json.dumps(steps))

    else:
        #import cProfile
        #cProfile.run('test()')
        test()
