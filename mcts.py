from state import value_v2 as state_value
import expression
from copy import deepcopy
from dfs import possible_next_steps
import json
import math
import random
import rich
import os
import numpy as np
from timer import Timer
from render_math import render_steps

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

manager = mp.Manager()

rollout_logfile = 'rollout.log'

import requests

def argmax(l):
    """
    给定数组，求最大元素的下标
    """
    return max((x, i) for i, x in enumerate(l))[1]


def children_weights(father, c_param=2.0, debug=False):
    """
    得到节点所有儿子的 UCT 权重
    """
    q, n, _, _, _, _, children = father
    weights = [
        c[0] + c_param * math.sqrt(math.log(n) / (c[1] + 1))
        for c in children
    ]
    return weights


def print_UCT(father, detailed=False):
    q, n, f_narr, _, _, _, children = father
    children_visits = [c[1] for c in children]
    children_narrs = [c[2] for c in children]
    zip_arr = zip(children, children_weights(father, c_param=.0), children_visits, children_narrs)

    if detailed:
        arr = [(c[4].name(), round(w, 3), f'{visits}/{n}', narr) for c, w, visits, narr in zip_arr]
    else:
        arr = [(c[4].name(), round(w, 3), f'{visits}/{n}') for c, w, visits, _ in zip_arr]

    arr.sort(key=lambda x: x[1], reverse=True)

    if detailed:
        print(expression.narr2tex(f_narr))
        for axiom_name, UCT, visits, narr in arr:
            rich.print('[green]UCT:[/]', end=" ")
            print(UCT, visits, axiom_name, expression.narr2tex(narr))
    else:
        print('[UCT]', arr)


def best_child_of(father, c_param=None, debug=False):
    """
    根据 UCT 选择最好的儿子节点
    """
    q, N, narr, _, _, _, children = father
    if c_param is None:
        weights = children_weights(father, debug=debug)
    else:
        weights = children_weights(father, c_param=c_param, debug=debug)
    argmax_idx = argmax(weights)

    if debug:
        print(f"\nfather", expression.narr2tex(narr))
        for i, ((q,n,narr,_,a,ai, _), UCT) in enumerate(zip(children, weights)):
            print()
            print( f"child [[{i}]] of axiom#{ai}", a.name())
            print(f"[UCT={UCT:.4f}, q/n={q:.2f}/{n}, N={N}, c_param={c_param}]",
                 expression.narr2tex(narr))
        print('\n[choice index]', f"[[{argmax_idx}]]")
        print()
    return children[argmax_idx], weights[argmax_idx], argmax_idx


def expand(father, step, prior=0):
    """
    新增儿子节点
    """
    q, n, _, _, _, _, children = father
    narr, axiom, axiom_idx = step

    # actual append

    to_be_appended = [prior, 0, narr, father, axiom, axiom_idx, []]

    if manager:
        to_be_appended[6] = manager.list([])
        to_be_appended = manager.list(to_be_appended)

    children.append(to_be_appended)
    father[6] = children

    return children[-1]


def fully_expand(father, steps, prior_arr=None):
    while True:
        q, n, _, _, _, _, children = father
        if len(children) < len(steps): # not fully expanded
            idx = len(children)
            step = steps[idx]
            prior = prior_arr[idx] if prior_arr is not None else 0
            expand(father, step, prior=prior)
        else:
            break


def move_policy(father, debug=False):
    """
    选择儿子就节点中下一个 roll-out 的起点
    """
    child, w, idx = best_child_of(father, debug=False)
    if debug:
        rich.print(f'[[best [yellow]child#{idx}[/]]]', end=" ")
        rich.print('[yellow]' + child[4].name())
    return child, idx


def nn_request(payload):
    #payload = {
    #    'req': 'value',
    #    'tex': "(-3 - \\frac{4}{17}) \\times (14 + \\frac{13}{15}) - (3 + \\frac{4}{17}) \\times (2 + \\frac{2}{15})"
    #}
    r = requests.post("http://localhost:8009", json=payload)
    j = r.json()
    #print(j['value'])
    return j


def policy_steps(narr, all_axioms, k=3, debug=False, nn_models=False, lock=None):
    """
    结合 policy 网络预测的 prior 生成 steps 以及其每一种可能的概率
    """
    if nn_models:
        # get NN predictions
        expr = expression.narr2tex(narr)

        if lock: lock.acquire()
        j = nn_request({'req': 'rule', 'tex': expr})
        rules, probs, = j['rules'], j['probs']
        if lock: lock.release()

        if debug:
            rich.print('[[restrict apply]]', end=" ")
            rich.print([all_axioms[r].name() for r in rules])

        steps = possible_next_steps(narr, all_axioms, state_value, restrict_rules=rules)
        if len(steps) == 0:
            steps = possible_next_steps(narr, all_axioms, state_value, restrict_rules=None)

        steps = [(n,a,ai) for n,_,a,ai in steps]

        # combine NN priors
        base_prob = min(probs) / 2.0
        step_probs = [base_prob if ai not in rules else probs[rules.index(ai)] for s, a, ai in steps]
        step_probs = np.array(step_probs)

        # normalize step probabilities
        sum_probs = step_probs.sum()
        if sum_probs != 0: step_probs = step_probs / sum_probs

        if debug:
            for prob, (s,a,ai) in zip(step_probs, steps):
                prob_percent = round(prob * 100, 2)
                rich.print(f'NN Policy: axiom#[red]{ai}[/red] {a.name()} prob=[blue]{prob_percent}%[/blue]')
                print(expression.narr2tex(s))
                print()

        return steps, step_probs
    else:
        # default steps without prior
        steps = possible_next_steps(narr, all_axioms, state_value)
        steps = [(n,a,ai) for n,_,a,ai in steps]
        return steps, [0 for _ in steps]


def reward_calc(values, debug=False, relative_value=True):
    father_val = values[0]
    argmax_idx = argmax(values)
    best_value = values[argmax_idx]

    if best_value > father_val:
        path_complexity = abs(sum(values[1: argmax_idx + 1]))
        complexity_reward = 10 / max(1, path_complexity)

        if relative_value:
            value_reward = ((best_value - father_val) ** 2) / (argmax_idx + 1)
        else:
            value_reward = 1000 / max(1, 1 - best_value)

        reward = value_reward + complexity_reward

        def normalize(x):
            return x / (1 + abs(x))
        norm_reward = normalize(reward / 100)

        if debug:
            reward_factors = {
                'father value': father_val,
                'best value': best_value,
                'at step': argmax_idx,
                'value reward': value_reward,
                'complexity reward': complexity_reward,
                'total reward': reward,
                'normalized reward': norm_reward,
                'values': values
            }
            print(json.dumps(reward_factors, indent=2))

        rewardless_len = len(values) - (argmax_idx + 1)
        return norm_reward, rewardless_len
    else:
        return 0, 0


def rollout(node, idx, all_axioms, n_times, visited,
            debug=False, nn_models=False, k=3, lock=None):
    """
    Monte-Carlo 树的 roll-out 操作
    """
    q, n, narr, father, axiom, axiom_idx, children = node

    cnt = 0

    values  = [state_value(father[2])]
    choices = [idx + 1]

    root_tex = expression.narr2tex(father[2])

    if debug:
        print('[roll-out origin]', end=' ')
        rich.print(f'[blue]{values[0]:.2f}[/]', end=' ')
        print(root_tex)

    while True:
        q, n, narr, father, axiom, axiom_idx, children = node
        expr = expression.narr2tex(narr)

        if nn_models:
            # use NN to estimate the number of left-over steps
            if lock: lock.acquire()
            j = nn_request({'req': 'value', 'tex': expr})
            expr_val = j['value']
            if lock: lock.release()
        else:
            # use rule-based value function to indicate complexity
            expr_val = state_value(narr)

        values.append(expr_val)

        if debug:
            axiom_name = axiom.name()
            print(f'[roll-out depth={cnt}]', end=' ')
            rich.print(f'[blue]{expr_val:.2f}[/]', end=' ')
            print(axiom_name, expr)

        if expr in visited:
            if debug: rich.print(f'[[roll-out]] [red]visited![/]')
            reward, rewardless_len = 0, 0
            break

        steps, step_probs = policy_steps(
            narr, all_axioms, k=k, debug=False, nn_models=nn_models, lock=lock
        )

        if len(steps) == 0:
            if debug: print('[roll-out reach leaf]')

            reward, rewardless_len = reward_calc(values, relative_value=(nn_models is None))
            break

        elif cnt >= n_times:
            if debug: print(f'[roll-out stop early (max times reached)]')

            reward, rewardless_len = reward_calc(values, relative_value=(nn_models is None))
            break

        # randomly select index
        rollout_idx = random.randint(0, len(steps) - 1)

        choices.append(rollout_idx + 1)

        # dive to deeper node specified by index
        if lock: lock.acquire()
        fully_expand(node, steps, prior_arr=step_probs)
        _, _, _, _, _, _, children = node
        next_node = children[rollout_idx]
        if lock: lock.release()

        node = next_node
        cnt += 1

    # write to roll-out log
    if lock: lock.acquire()
    with open(rollout_logfile, 'a') as fh:
        fh.write(json.dumps(choices))
        fh.write(json.dumps([f'{reward:.3f}']))
        fh.write(' ' + root_tex)
        fh.write('\n')
    if lock: lock.release()

    return node, reward, rewardless_len


def backprop(node, reward, rewardless_len):
    """
    反向传播：通过 reward 更新 roll-out 路径上所有节点的统计数据
    """
    cnt = 0
    while node is not None:
        q, n, narr, father, axiom, axiom_idx, children = node
        if cnt >= rewardless_len:
            node[0] = max(reward, node[0])
        node[1] += 1
        #print(f'[backprop q/n={node[0]:.3f}/{node[1]}]', expression.narr2tex(narr))
        node = father
        cnt += 1


def evaluate(
    node, all_axioms, steps, n_sample_times, sample_depth, visited,
    debug=False, nn_models=False, k=3, step_probs=None,
    worker=0, lock=None):
    """
    采样函数（顺序执行版）：进行 n_sample_times 次采样
    """
    for i in range(n_sample_times):
        if lock: lock.acquire()
        fully_expand(node, steps, prior_arr=step_probs)
        if lock: lock.release()

        child, idx = move_policy(node, debug=debug)

        if debug:
        #if True:
            rich.print(f"[red]worker#{worker} sample[/] {i+1}th/{n_sample_times}")
            print_UCT(node, detailed=True)
            #print('[step probs]', step_probs)
            #print('[expr]', expression.narr2tex(node[2]))
            #for s,a,ai in steps:
            #    print(f'axiom#{ai}', a, end='\n---\n')
            #    print(expression.narr2tex(s))
            #    print()

        bottom_node, reward, rewardless_len = rollout(
            child, idx, all_axioms, sample_depth, visited,
            debug=debug, nn_models=nn_models, k=k, lock=lock
        )

        if debug:
            print('\033[91m', end='')
            print(f'[reward] {reward:.2f}')
            print('\033[0m')

        if lock: lock.acquire()
        backprop(bottom_node, reward, rewardless_len)
        if lock: lock.release()


def evaluate_parallel(
    node, all_axioms, steps, n_sample_times, sample_depth, visited,
    debug=False, nn_models=False, k=3, step_probs=None,
    n_worker=11, n_samples_per_worker=2, use_thread=False):
    """
    采样函数（并行版本）：进行 n_sample_times 次采样
    """
    n_stages = n_sample_times // n_worker // n_samples_per_worker
    lock = manager.Lock() if manager else None

    for b in range(n_stages):
        #if debug:
        if True:
            name = 'multi-thread' if use_thread else 'multi-process'
            rich.print(f"[red]{name} stage[/] {b + 1}th/{n_stages} with " +
            f"{n_worker} workers, each {n_samples_per_worker}/{n_sample_times} samples")
            print_UCT(node, detailed=True)

        job = [None] * n_worker

        if use_thread:
            with ThreadPoolExecutor(max_workers=n_worker) as executor:
                for i in range(n_worker):
                    job[i] = executor.submit(evaluate,
                        node, all_axioms, steps, n_samples_per_worker, sample_depth, visited,
                        debug=False, nn_models=nn_models, k=k, step_probs=step_probs,
                        worker=i, lock=lock
                    )
        else:
            with ProcessPoolExecutor(max_workers=n_worker) as executor:
                for i in range(n_worker):
                    job[i] = executor.submit(evaluate,
                        node, all_axioms, steps, n_samples_per_worker, sample_depth, visited,
                        debug=False, nn_models=nn_models, k=k, step_probs=step_probs,
                        worker=i, lock=lock
                    )

#def policy_fine_tuning(nn_models, expr, policy, debug=False, all_axioms=[]):
#    """
#    对 policy network 进行 on-the-fly 参数更新。
#    """
#    #if debug:
#    if True:
#        rich.print('[bold green]fine tune policy[/]', end=' ')
#        print(expr, '==>', f'policy#{policy}')
#        if policy > 0: print(all_axioms[policy - 1])
#        print()
#    # preparing
#    tokens = tex2tokens(expr)
#    bow = nn_models.bow
#    device = nn_models.device
#    x_batch, p_batch, _ = batch_tensors([(tokens, policy, 0)], bow, device)
#    # feed forward
#    policy_logits, _ = nn_models.policy_network(x_batch)
#    logprob = F.log_softmax(policy_logits, dim=1) # [B, max_rule]
#    policy_loss = nn_models.policy_loss_fun(logprob, p_batch)
#    # fine-tuning network
#    nn_models.policy_opt.zero_grad()
#    policy_loss.backward()
#    nn_models.policy_opt.step()
#
#
#def value_fine_tuning(nn_models, expr, value, debug=False):
#    """
#    对 value network 进行 on-the-fly 参数更新。
#    """
#    #if debug:
#    if True:
#        rich.print('[bold green]fine tune value[/]', expr, '==>', value)
#    # preparing
#    tokens = tex2tokens(expr)
#    bow = nn_models.bow
#    device = nn_models.device
#    x_batch, _, v_batch = batch_tensors([(tokens, 0, value)], bow, device)
#    # feed forward
#    value_predicts, _ = nn_models.value_network(x_batch)
#    value_predicts = value_predicts.squeeze(1) # [B]
#    value_loss = nn_models.value_loss_fun(value_predicts, v_batch)
#    # fine-tuning network
#    nn_models.value_opt.zero_grad()
#    value_loss.backward()
#    nn_models.value_opt.step()


def back_off_step(steps, debug=False):
    """
    裁剪 MCTS 最后几步的探索步骤，确保得到的 value 比较小
    """
    max_val = max([state_value(narr) for narr, a, ai in steps])

    while len(steps) > 1:
        cur_step = steps[-1]
        narr, _, _ = cur_step
        val = state_value(narr)

        if val >= max_val:
            break
        else:
            if debug:
                expr = expression.narr2tex(narr)
                val = state_value(narr)
                rich.print(f'[magenta]back-off[/] [blue]val={val:.3f}[/]', end=' ')
                print(expr)
            steps.pop()

    return steps


def mcts(narr0, all_axioms, sample_depth=4, n_sample_times=200, n_maxsteps=100, k=3,
         debug=False, nn_models=False, training=False, force_single_thread=False):
    #       q  n   narr  father  axiom   axiomIdx  children
    root = [0, 1, narr0, None,  None,      -1,       []    ]
    moves = [root]

    render_steps([(narr0, None, -1)])

    global manager
    if not force_single_thread:
        # prepare proxy structure for parallel processes
        root[6] = manager.list([])
        root = manager.list(root)
        moves = [root]
    else:
        manager = None

    node = root
    visited = set([expression.narr2tex(narr0)])
    final_steps = []

    while True:
        q, n, narr, father, axiom, axiom_idx, children = node

        # debug print
        if True:
        #if debug:
            print('\033[94m', end='')
            expr_val = state_value(narr)
            print(f'[current] step={len(moves)}, val={expr_val:.1f}:',
                expression.narr2tex(narr), end='')
            print('\033[0m', end='\n')
            expression.narr_prettyprint(narr)

        steps, step_probs = policy_steps(
            narr, all_axioms, k=k, debug=debug, nn_models=nn_models
        )

        if debug:
            rich.print(f'[magenta]Candidate steps: {len(steps)}[/]')
            for i, (n, a, ai) in enumerate(steps):
                val = state_value(n)
                rich.print(f'[red]#{i+1}[/]', a.name(), ':', end=' ')
                rich.print(f'val={val:.2f}', end=' ')
                print(expression.narr2tex(n), end='\n\n')

            if False:
                from axiom import Axiom
                render_steps([(narr, Axiom(), -1)] + steps, show_index=True)
                choices = input('Limit choices: ')
                choices = [i for i in map(lambda x: int(x), choices.split(','))]
                rich.print(choices)
                steps = [steps[i-1] for i in choices]

        if len(steps) == 0:
            if debug: print('[no more candidate steps]')
            if nn_models and training:
                policy = 0
                #policy_fine_tuning(nn_models, expr, policy, debug=debug, all_axioms=all_axioms)
            break

        if manager and not force_single_thread:
            evaluate_parallel(
                node, all_axioms, steps, n_sample_times, sample_depth, visited,
                debug=debug, nn_models=nn_models, k=k, step_probs=step_probs
            )
        else:
            evaluate(
                node, all_axioms, steps, n_sample_times, sample_depth, visited,
                debug=debug, nn_models=nn_models, k=k, step_probs=step_probs
            )

        # selection
        move_choice, w, _ = best_child_of(node, c_param=.0, debug=debug)
        move_to_expr = expression.narr2tex(move_choice[2])
        if w == 0 or move_to_expr in visited:
            print(f'[abort] best w={w:.2f}, visited: {move_to_expr in visited}')
            break
        else:
            if nn_models and training:
                policy = move_choice[5] + 1
                #policy_fine_tuning(nn_models, expr, policy, debug=debug, all_axioms=all_axioms)

            moves.append(move_choice)
            node = move_choice

            # construct steps to be returned
            final_steps = [(e, a, ai) for q, n, e, f, a, ai, c in moves]
            render_steps(final_steps)

            visited.add(move_to_expr)
            #if debug: print('[visited]', visited)

            if len(moves) >= n_maxsteps:
                if debug: print('[exceed max steps]')
                break

    if len(final_steps) > 0:
        final_steps = back_off_step(final_steps, debug=True)

    if nn_models and training:
        # fine-tune value network
        for i, (e, _, _) in enumerate(final_steps):
            value = -(len(final_steps) - i - 1)
            #value_fine_tuning(nn_models, e, value, debug=debug)
    return final_steps


def test():
    from test_cases import test_cases_x3_rational, test_cases_wiki131278697, test_case_from_log

    from common_axioms import common_axioms
    axioms = common_axioms(full=True)

    testcases = []

    tmp, _ = test_cases_x3_rational()
    testcases += tmp

    #testcases += [
    #    '\\frac{12a}{3a + a + 20a} - \\frac{1}{4}',
    #    '1 + \\frac{7}{3}',
    #    '4 -3 \\frac{1}{2}',
    #    '\\frac{(-3)^{3}}{2 \cdot \\frac{1}{4} \cdot (-\\frac{2}{3})^{2}} + 4 -4 \cdot \\frac{1}{3}',
    #    '\\frac{11}{2} (- \\frac{1}{6}) \\frac{3}{11} \\frac{4}{3}',
    #    '(-3\\frac{1}{3})\div2\\frac{1}{3}\\times\\frac{7}{10}',
    #    'a - x^{2} + x^{2} \\times 0.609 + 1 = 0',
    #    '1.609 \\times x^{2} + x^{2} + x^{2} \\times 2 \\times x = 0',
    #    '-x \\times 0.391 - 629 - x^{2} \\times 2 + y^{2} + x \\times \\frac{50}{x + y} = 0',

    #    # some tests for extracting common factors
    #    "25 \cdot 48 + 103 \cdot 25 - 25 \cdot 51",
    #    "-13 \\times \\frac{2}{3} - 0.34 \\frac{2}{7} + \\frac{1}{3}(-13) - \\frac{5}{7} 0.34",

    #    "-x 0.391 - 629 - 2 x^{2} + y^{2} + \\frac{50x}{x+y} = 0",
    #    "- (3\\frac{4}{17}) (2\\frac{2}{15}) - (7\\frac{4}{17}) (14 \\frac{13}{15}) - 4 (-14 \\frac{13}{15})",
    #    "(-3 - \\frac{4}{17}) \\times (14 + \\frac{13}{15}) - (3 + \\frac{4}{17}) \\times (2 + \\frac{2}{15})",
    #    #"-200.9 + 28 + 0.9 + (-8)",
    #    #"3+5\\times6-6\div3",
    #    #"\\frac{(-3)^{3}}{2 \\times \\frac{1}{4} (-\\frac{2}{3})^{2}} +4 -4 \\times\\frac{1}{3}",
    #    #"6 \div 3"
    #]

    nn_models = True
    debug = True
    force_single_thread = False

    n_steps = 0
    timer = Timer()
    open(rollout_logfile, 'w')
    #for i, expr in enumerate(testcases[-1:]):
    for i, expr in enumerate(testcases[:]):
        narr = expression.tex2narr(expr)

        n_sample_times = 22 if nn_models or force_single_thread else 440

        with timer:
            steps = mcts(narr, axioms,
                debug=debug, n_sample_times=n_sample_times,
                nn_models=nn_models, force_single_thread=force_single_thread)

        for j, (narr, axiom, axiom_idx) in enumerate(steps):
            val = state_value(narr)
            expr = expression.narr2tex(narr)
            axiom_name = axiom.name() if axiom is not None else '原式'
            rich.print(f'step{j} {axiom_name} [blue]val={val:.2f}[/]', expr)

        render_steps(steps)
        n_steps += len(steps)
        print(f'steps: {len(steps)}')
        print(f'Test case: {i} / {len(testcases) - 1}')

        #print('Enter to continue')
        #input()

    timer.show_stats(n_steps=n_steps)


if __name__ == '__main__':
    test()
