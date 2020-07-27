import expression
import rich
import axiom
import state
import sys
import mathjs
from copy import deepcopy
from axiom import Axiom
from timer import Timer

def possible_next_steps(narr, axioms, state_value, animation_mode=False,
                        debug=False, restrict_rules=None, fast_return=False):
    return_steps = []
    cur_value = state_value(narr)
    if debug:
        tex = expression.narr2tex(narr)
        rich.print(f'[light]{cur_value:.2f}', end=' ')
        print(tex)

    for axiom_idx, axiom in enumerate(axioms):
        axiom.animation_mode = animation_mode
        possible_applied_tuples = axiom.apply(narr)

        value_constrain_narrs = []
        for applied_narr, ani_narr in possible_applied_tuples:
            value = state_value(applied_narr)
            if not axiom.allow_complication:
                if ((axiom.strict_simplify and value <= cur_value) or
                   value < cur_value):
                    if debug:
                        rich.print('[grey50][[x]]', end=' ')
                        tex = expression.narr2tex(applied_narr)
                        print(axiom.name(), end=' ')
                        rich.print(f'[light]{value:.2f}', end=' ')
                        print(tex)
                    continue
            value_constrain_narrs.append((applied_narr, ani_narr, axiom, axiom_idx, value))

        return_steps += value_constrain_narrs

        if fast_return and len(value_constrain_narrs) > 0: break

    return_steps.sort(key=lambda x: (x[-2], -x[-1]))

    if debug:
        for i, (applied_narr, ani_narr, axiom, axiom_idx, value) in enumerate(return_steps):
            # print axiom name
            if i == 0:
                rich.print(f'[bright_green][[✓]]', end=' ')
            else:
                rich.print(f'[grey50][[ ]]', end=' ')
            print(axiom.name(), end=" ")
            # print value
            rich.print(f'[light]{value:.2f}', end=' ')
            # print tex
            tex = expression.narr2tex(applied_narr)
            print(tex)
        print()

    # trim value from tuples
    return [s[:-1] for s in return_steps]


def dfs(narr, axioms, debug=False, maxsteps=150, animation_mode=False, printTrim=False):
    any_err = None
    try:
        next_steps = [(narr, None, Axiom(name='原式'), -1)]
        return_steps = []
        cnt = 0
        while len(next_steps) > 0:
            narr, ani_narr, axiom, axiom_idx = next_steps[0]

            output_narr = deepcopy(narr)
            #print('[output narr]', narr)

            if animation_mode:
                if printTrim:
                    rich.print('[blue]before trim[/]')
                    expression.narr_prettyprint(narr)
                    print('[tex]', expression.narr2tex(narr))
                expression.trim_animations(narr)
                if printTrim:
                    rich.print('[blue]after trim[/]')
                    expression.narr_prettyprint(narr)
                    print('[tex]', expression.narr2tex(narr))

            return_steps.append((output_narr, ani_narr, axiom, axiom_idx))
            next_steps = possible_next_steps(narr, axioms, state.value_v1,
                animation_mode=animation_mode, fast_return=True, debug=debug)
            if cnt > maxsteps:
                any_err = "maximum steps reached."
                break
            cnt += 1
    except KeyboardInterrupt:
        pass

    return return_steps, any_err


def test(all_axioms):
    from render_math import render_steps
    from test_cases import test_cases_x3_rational, test_cases_wiki131278697

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
        "b + 3x^{2} +2b + 3b + x^{2}= 0",
        "(3 + \\frac{4}{17}) (-14\\frac{13}{15} - \\frac{2}{15}) - 2 \times 3 - 2 \\times \\frac{4}{17}",
        "-(3 + \\frac{4}{17}) \\times (14\\frac{13}{15}) - (3 + \\frac{4}{17}) \\times (2\\frac{2}{15})",

        # some animation testcases
        "1 + 0 + 0 + 0 + 0",
        '-3 \\frac{-2}{4}',
        '\\frac{2}{3} \div \\frac{4}{5}',
        '(\sqrt{2})^{2}',
        '0+1+2',
        '-\\frac{1}{-2} \div \\frac{-3}{4}',
        '\\frac{x}{3xy}',
        '-x x',
        '-\\frac{8}{-2}',
        "a + b = 3 - c",
        "x + b = 12",
        '\\frac{2}{x} + y = a + b',
        '\\frac{1}{y} \\frac{x}{1}',
        '-7(a-b)',
        '-(-2-3)^{2}',
        "\left| -(5+\\frac{1}{2})\\right| (\\frac{1}{3} - \\frac{1}{2}) \\frac{3}{11} \\div (1 - \\frac{1}{4})",
        "2 + 7 + 8",
        "3x + 3 = 2x - 1",
        '2(a + b) + 3',
        '2(a + b)',
        '(-7) + 10 + (-3) + 6 + (-6)',
        '-(3 - 2)x',
        "(-3 - \\frac{4}{17}) \\times (14\\frac{13}{15}) - (3\\frac{4}{17}) \\times (2\\frac{2}{15})",
    ]

    begin_from = 0

    n_steps = 0
    timer = Timer()

    #for i, test in enumerate(testcases):
    for i, test in enumerate(testcases[-1:]):
        if i < begin_from: continue

        test_narr = expression.tex2narr(test)

        with timer:
            steps, err = dfs(test_narr, all_axioms, debug=True, animation_mode=False, printTrim=False)
            if err:
                print('DFS error:', err)

        for narr, ani_narr, axiom, axiom_idx in steps:
            rich.print(f'[red]{axiom.name()}')
            tex = expression.narr2tex(narr)
            if ani_narr:
                ani_tex = expression.narr2tex(ani_narr)
                print('\t', ani_tex)
            print('\t', tex)

            #animation_json = mathjs.tex2json(tex)
            #print('\t', animation_json)

        render_steps(steps)

        n_steps += len(steps)
        print(f'steps: {len(steps)}')
        print(f'test case: {i} / {len(testcases)}')

        #input('Enter to continue...')

    timer.show_stats(n_steps=n_steps)


if __name__ == '__main__':
    if False:
        all_axioms = [
            Axiom(name='负号乘进因子', recursive_apply=True, strict_simplify=True, disable=False)
            .add_rule('-(x + *{1}) *{2} ', '(-x - *{1}) *{2}',
            animation='`-(x + *{1})`[replace]{-x - *{1}} *{2}')

            .add_test('-(3 - 2)x', '(-3 + 2) \\times x')
        ]

    else:
        from common_axioms import common_axioms
        all_axioms = common_axioms()

    args = sys.argv[1:]
    if len(args) > 0:
        tex = args[0]
        narr = expression.tex2narr(tex)
        steps, err = dfs(narr, all_axioms, debug=False, animation_mode=True)

        if err:
            print(err, file=sys.stderr)
            quit()

        ret_arr = []
        for i, (narr, ani_narr, axiom, axiom_idx) in enumerate(steps):
            trim_narr = expression.trim_animations_copy(narr)
            trim_tex = expression.narr2tex(trim_narr)

            animate_tex = expression.narr2tex(narr)
            animate_json = mathjs.tex2json(animate_tex)

            if ani_narr:
                ani_tex = expression.narr2tex(ani_narr)
                ani_json = mathjs.tex2json(ani_tex)
                ret_arr.append({
                    'tex': '\\text{transition step ...}',
                    'animate_tex': ani_tex,
                    'animate_json': ani_json,
                    'axiom': '移项',
                    'axiom_idx': -2
                })

            ret_arr.append({
                'tex': trim_tex,
                'animate_tex': animate_tex,
                'animate_json': animate_json,
                'axiom': axiom.name(),
                'axiom_idx': axiom_idx
            })

        import json
        print(json.dumps(ret_arr, ensure_ascii=True))

    else:
        #import cProfile
        #cProfile.run('test()')
        test(all_axioms)
