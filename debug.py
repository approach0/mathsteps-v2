import expression
import rich
import state
from dfs import possible_next_steps
from axiom import Axiom
from common_axioms import common_axioms


def print_steps(steps):
    for i, (narr, axiom, axiomIdx) in enumerate(steps):
        tex = expression.narr2tex(narr)
        value = state_value(narr)
        rich.print(f'[red]{i + 1}[/red] [blue]{value:.2f}[/]', end=" ")
        print(axiom.name(), tex)


if __name__ == '__main__':
    from render_math import render_steps
    from test_cases import test_cases_x3_rational, test_cases_wiki131278697

    all_axioms = common_axioms(full=True)
    state_value = state.value_v2

    testcase = (
        "- (3\\frac{4}{17}) (2\\frac{2}{15}) - (7\\frac{4}{17}) (14 \\frac{13}{15}) - 4 (-14 \\frac{13}{15})"
    )

    try:
        narr = expression.tex2narr(testcase)
        steps = [(narr, Axiom(name='原式'), -1)]
        choices = [0]
        while len(steps) > 0:
            narr = steps[-1][0]
            value = state_value(narr)
            next_steps = possible_next_steps(narr, all_axioms, state_value, debug=False)

            if len(next_steps) == 0:
                break

            # print choices
            rich.print(f'[bold red]current[/] [blue]{value:.2f}[/]:', end=" ")
            print(expression.narr2tex(narr))
            expression.narr_prettyprint(narr)

            print_steps(next_steps)

            while True:
                render_steps(steps[-1:] + next_steps, show_index=True, output='./debug.html')
                j = input('Enter choice (0 to print past steps): ')
                if int(j) == 0:
                    print_steps(steps)
                    render_steps(steps, output='./debug.html')
                    input('Enter to continue ...')
                    continue
                elif int(j) < 0:
                    steps = steps[0: int(j)]
                    choices = choices[0: int(j)]
                    break

                choice_step = next_steps[int(j) - 1]
                steps.append(choice_step)
                choices.append(int(j))
                break

    except KeyboardInterrupt:
        print()

    rich.print('Choices:', choices)
    print_steps(steps)
    render_steps(steps, output='./debug.html')
