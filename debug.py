import expression
import rich
import state
from axiom import Axiom
from mcts import reward_calc
from dfs import possible_next_steps
from render_math import render_steps
from test_cases import test_cases_x3_rational, test_cases_wiki131278697

from nn.train import BoW, RNN_model, tex2tokens, batch_tensors
import nn.predict as nn

def print_steps(steps):
    for i, (narr, ani_narr, axiom, axiomIdx) in enumerate(steps):
        tex = expression.narr2tex(narr)
        value = state_value(narr)
        rich.print(f'[red]{i + 1}[/red] [blue]{value:.2f}[/]', end=" ")
        print(axiom.name())
        if ani_narr:
            ani_tex = expression.narr2tex(ani_narr)
            print('\t', ani_tex)
        print('\t', tex)


def nn_value(narr):
    tex = expression.narr2tex(narr)
    expr_val, _ = nn.predict_value(tex, nn_models)
    return expr_val


if __name__ == '__main__':

    if False:
        all_axioms = [
            Axiom(name='乘积写成乘方的形式', allow_complication=True)
            .add_rule('#(#X)(#X)', '#0 X^{2}',
            animation='`#1(#2 X)(#3 X)`[replace]{#0 X^{2}}')
        ]

    else:
        from common_axioms import common_axioms
        all_axioms = common_axioms(full=True)

    testcase = (
        "(-3 - \\frac{4}{17}) \\times (14 + \\frac{13}{15}) - (3 + \\frac{4}{17}) \\times (2 + \\frac{2}{15})"
    )

    debug_NN = True

    if debug_NN:
        global nn_models
        nn_models = nn.NN_models('model-policy-nn.pretrain.pt', 'model-value-nn.pretrain.pt', 'bow.pkl')

    state_value = nn_value if debug_NN else state.value_v2

    try:
        narr = expression.tex2narr(testcase)
        val0 = state_value(narr)
        steps = [(narr, None, Axiom(name='原式'), -1)]
        choices = [0]
        values = [val0]
        while len(steps) > 0:
            narr = steps[-1][0]
            value = state_value(narr)
            values.append(value)

            # only used in animation_mode
            expression.trim_animations(narr)

            if debug_NN:
                rules, probs, _ = nn.predict_policy(testcase, nn_models, k=4)
                rules = rules.tolist()

                axiom_name_probs = [(all_axioms[r].name(), probs[i]) for i, r in enumerate(rules) if r >= 0]
                rich.print('[cyan]model prediction:[/]', axiom_name_probs)

                next_steps = possible_next_steps(narr, all_axioms, state_value, debug=True, restrict_rules=rules)
            else:
                next_steps = possible_next_steps(narr, all_axioms, state_value, debug=True)


            if len(next_steps) == 0:
                break

            # print choices
            rich.print(f'[bold red]current[/] [blue]{value:.2f}[/]:', end=" ")
            print(expression.narr2tex(narr))
            #expression.narr_prettyprint(narr)

            reward, _ = reward_calc(values)
            print('\033[91m', end='')
            print(f'origin value: {val0:.2f}, cur value: {value:.2f}, reward = {reward:.2f}')
            print('\033[0m')

            while True:
                print_steps(next_steps)
                render_steps(steps[-1:] + next_steps, show_index=True, output='./debug.html')
                j = input('Enter choice (0 to print past steps): ')
                if int(j) == 0:
                    rich.print('Choices:', choices)
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
