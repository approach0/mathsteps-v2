import os
import rich
import expression
from timer import Timer
from render_math import render_steps
from state import value_v2 as state_value
from common_axioms import common_axioms

from mcts import mcts
from dfs import dfs
from test_cases import test_cases_x3_rational, test_cases_wiki131278697, test_case_from_log


def generate_corpus(test_case_id, data, steps, DIV=20):
    # make directory
    folder = './output/' + str(test_case_id % DIV)
    os.makedirs(folder, exist_ok=True)

    # save html preview file
    render_steps(steps, output=f'{folder}/{i}.html')

    # corpus text file
    with open(f'{folder}/{i}.txt', 'w') as fh:
        for last_e, a, this_e in data:
            fields = [last_e, str(a), this_e]
            fh.write(' $ '.join(fields) + '\n')


if __name__ == '__main__':
    basic_axioms = common_axioms(full=False)
    all_axioms = common_axioms(full=True)

    # test cases to generate steps
    testcases = []

    testcases += [
        #'\\frac{12a}{3a + a + 20a} - \\frac{1}{4}',

        "\\frac{-1}{\\frac{2}{3} \cdot \\frac{7}{10}}",
        '1 + \\frac{7}{3}',
        '4 -3 \\frac{1}{2}',
        '\\frac{(-3)^{3}}{2 \cdot \\frac{1}{4} \cdot (-\\frac{2}{3})^{2}} + 4 -4 \cdot \\frac{1}{3}',
        '\\frac{11}{2} (- \\frac{1}{6}) \\frac{3}{11} \\frac{4}{3}',
        "25 \cdot 48 + 103 \cdot 25 - 25 \cdot 51",
        "-13 \\times \\frac{2}{3} - 0.34 \\frac{2}{7} + \\frac{1}{3}(-13) - \\frac{5}{7} 0.34",
        '(-3\\frac{1}{3})\div2\\frac{1}{3}\\times\\frac{7}{10}',
        "(-18) \div ((2\\frac{1}{4}) \\times (1 - \\frac{3}{4}))",
        "(-3 - \\frac{4}{17}) (14\\frac{13}{15}) - (3\\frac{4}{17}) (2 + \\frac{2}{15})",
        "(3 + \\frac{4}{17}) (-14\\frac{13}{15} - \\frac{2}{15}) - 2 \\times 3 - 2 \\times \\frac{4}{17}",
        "-(3 + \\frac{4}{17}) \\times (14\\frac{13}{15}) - (3 + \\frac{4}{17}) \\times (2\\frac{2}{15})",
        "\\frac{-1}{\\frac{2}{3} \cdot \\frac{7}{10}}",
        "1 + 0 + 0 + 0 + 0",
        '-3 \\frac{-2}{4}',
        '\\frac{2}{3} \div \\frac{4}{5}',
        '(\sqrt{2})^{2}',
        '0+1+2',
        '-\\frac{1}{-2} \div \\frac{-3}{4}',
        '-\\frac{8}{-2}',
        '-(-2-3)^{2}',
        "\left| -(5+\\frac{1}{2})\\right| (\\frac{1}{3} - \\frac{1}{2}) \\frac{3}{11} \\div (1 - \\frac{1}{4})",
        "2 + 7 + 8",
        "(-3 - \\frac{4}{17}) \\times (14\\frac{13}{15}) - (3\\frac{4}{17}) \\times (2\\frac{2}{15})",
        "\\frac{1}{2} \\times 10.2 - (\\frac{5}{4} + 1 - 9 \\frac{1}{7})^{2}",

        "-200.9 + 28 + 0.9 + (-8)",
        "3+5\\times 6-6\div3",
        "6 \div 3",
    ]

    #tmp, _ = test_cases_wiki131278697()
    #testcases += tmp

    tmp, _ = test_cases_x3_rational()
    testcases += tmp

    testcases += test_case_from_log('./rational_8000.txt')
    testcases += test_case_from_log('./full_random_1000.txt')

    #n_sample_times = 220
    n_sample_times = 440
    start = 0
    always_use_MCTS = False

    open('fallback.log', 'w')

    for i, expr in enumerate(testcases[:]):
        if i < start: continue

        try:
            narr = expression.tex2narr(expr)

            err = None
            if not always_use_MCTS:
                # use DFS or mcts (as fallback) to generate steps
                steps, err = dfs(narr, basic_axioms, debug=True, maxsteps=150)
                steps = [(n, a, ai) for n, an, a, ai in steps]

            if err or always_use_MCTS:
                with open('fallback.log', 'a') as fh:
                    fh.write(f'#{i}: ' + expr + '\n')

                steps = mcts(narr, all_axioms, debug=False, n_sample_times=n_sample_times,
                    nn_models=None, force_single_thread=False)

            # make data pair
            data = []
            for j in range(1, len(steps)):
                last_narr, _, _ = steps[j - 1]
                narr, axiom, axiom_idx = steps[j]

                last_expr = expression.narr2tex(last_narr)
                expr = expression.narr2tex(narr)

                axiom_name = axiom.name()
                rich.print(f'step{j} axiom#{axiom_idx} {axiom_name}', expr)

                data.append((last_expr, axiom_idx + 1, expr))
            data.append((expr, 0, expr))

            # write data pair
            print(f'Test case: {i} / {len(testcases) - 1}')
            generate_corpus(i, data, steps, DIV=20)

            #input('pause')

        except KeyboardInterrupt:
            print('Abort')
            quit()
        except Exception as err:
            print(err)
            continue
