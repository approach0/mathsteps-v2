import state
import expression
from common_axioms import common_axioms
from copy import deepcopy
from dfs import possible_next_steps
import math
import random
import rich
import os
import numpy as np
from timer import Timer

#from nn_policy.train import BoW, RNN_model, tex2tokens, batch_tensors
#from nn_policy.predict import NN_models
#from nn_policy import predict as nn

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
manager = multiprocessing.Manager()

import torch.nn.functional as F


def argmax(l):
    """
    给定数组，求最大元素的下标
    """
    return max((x, i) for i, x in enumerate(l))[1]


def children_weights(father, c_param=1.4, debug=False):
    """
    得到节点所有儿子的 UCT 权重
    """
    q, n, _, _, _, _, children = father

    if debug:
        print('[Q weights]', [c[0] for c in children])

    weights = [
        c[0] / c[1] + c_param * math.sqrt(2 * math.log(n) / c[1])
        if c[1] != 0 else 0
        for c in children
    ]
    return weights


def best_child_of(father, c_param=1.4, debug=False):
    """
    根据 UCT 选择最好的儿子节点
    """
    q, n, _, _, _, _, children = father
    weights = children_weights(father, debug=debug)
    argmax_idx = argmax(weights)

    if debug:
        print(f"father: [n={n}]")
        for i, ((q,n,narr,_,a,ai, _), w) in enumerate(zip(children, weights)):
            print()
            print( f"child [[{i}]] of axiom#{ai}")
            print(a)
            print(f"[w={w:.4f}, q={q:.2f}, n={n}]", expression.narr2tex(narr))
        print('\n[choice index]', f"[[{argmax_idx}]]")
        print()
    return children[argmax_idx], weights[argmax_idx]


def expand(father, step, prior=0):
    """
    新增儿子节点
    """
    q, n, _, _, _, _, children = father
    narr, axiom, axiom_idx = step

    # actual append
    to_be_appended = [prior, 100, narr, father, axiom, axiom_idx, []]
    if manager: to_be_appended = manager.list(to_be_appended)
    children.append(to_be_appended)
    father[6] = children

    return children[-1]


def move_policy(father, steps, debug=False, prior_arr=None):
    """
    选择儿子就节点中下一个 roll-out 的起点
    未展开充分前进行展开操作，展开充分后通过 UCT 公式选择。
    """
    q, n, _, _, _, _, children = father
    if len(children) < len(steps): # not fully expanded
        idx = len(children)
        step = steps[idx]
        prior = prior_arr[idx] * 100.0 if prior_arr is not None else 0
        if debug: print('[expand] ', '(prior=%.5f)' % prior, '\n', step[1])
        return expand(father, step, prior=prior)
    else:
        child, w = best_child_of(father, debug=False)
        if debug: print(f'[best child] w={w:.5f}\n', child[4])
        return child


def policy_steps(narr, all_axioms, k=3, debug=False, nn_models=None, trust_nn=False):
    """
    结合 policy 网络预测的 prior 生成 steps 以及其每一种可能的概率
    """
    if nn_models:
        # get NN predictions
        expr = expression.narr2tex(narr)
        rules, probs, _ = nn.predict_policy(expr, nn_models, k=k)

        if trust_nn:
            steps = possible_next_steps(narr, all_axioms, restrict_rules=rules)
        else:
            steps = possible_next_steps(narr, all_axioms, restrict_rules=None)

        # combine NN priors
        rules = rules.tolist()
        base_prob = min(probs) / 2.0
        step_probs = [base_prob if ai not in rules else probs[rules.index(ai)] for s, a, ai in steps]
        step_probs = np.array(step_probs)

        # normalize step probabilities
        sum_probs = step_probs.sum()
        if sum_probs != 0: step_probs = step_probs / sum_probs

        if debug:
            for prob, (s,a,ai) in zip(step_probs, steps):
                prob_percent = round(prob * 100, 2)
                rich.print(f'axiom#[red]{ai}[/red] prob=[blue]{prob_percent}%[/blue]\n')
                print(a, end='\n---\n')
                print(expression.narr2tex(s))
                print()

        return steps, step_probs
    else:
        # default steps without prior
        steps = possible_next_steps(narr, all_axioms)

        return steps, [0 for _ in steps]


def rollout(node, all_axioms, n_times, visited, debug=False, nn_models=None, k=3, lock=None):
    """
    Monte-Carlo 树的 roll-out 操作
    nn_models 未指定时，完全随机进行深度为 n_times 的 roll-out.
    nn_models 指定时，通过神经网络指定 roll-out 选择节点的概率。
    """
    cnt = 0
    reward = 0
    max_step_reward = 100
    max_complexity_reward = 10
    complexity_reward = 0
    origin_val = state.value(node[2])
    while True:
        q, n, narr, father, axiom, axiom_idx, children = node
        expr = expression.narr2tex(narr)

        if expr in visited:
            if debug: print('\033[91m', 'visited!', '\033[0m', expr)
            if nn_models:
                reward = -max_step_reward
            break

        # when no NN presents, we can only define value by complexity difference
        expr_val = state.value(narr)
        if nn_models is None:
            if expr_val > origin_val:
                if debug: print(f'[roll-out found early reward]', expr)
                reward = expr_val - origin_val
                break
        else:
            complexity_reward += -expr_val

        steps, step_probs = policy_steps(
            narr, all_axioms, k=k, debug=False, nn_models=nn_models, trust_nn=True
        )

        if len(steps) == 0:
            if debug: print('[roll-out reach leaf]')

            if nn_models:
                step_reward = max_step_reward
                reward = step_reward + max_complexity_reward / max(1, complexity_reward)
                if debug: print(f'[step reward] {max_step_reward}')
            break

        elif cnt >= n_times:
            if debug: print(f'[roll-out stop early]')

            if nn_models:
                # use NN to estimate the number of left-over steps
                if lock: lock.acquire()
                pred_val, _ = nn.predict_value(expr, nn_models)
                if lock: lock.release()

                if debug: print(f'[predict value]', pred_val)

                step_reward = max_step_reward / max(1, 1 - pred_val)
                reward = step_reward + max_complexity_reward / max(1, complexity_reward)
                if debug: print(f'[step reward] {step_reward}')
            break

        # randomly select index
        if nn_models:
            rollout_idx = random.choices(
                population = [_ for _ in range(len(steps))],
                weights = step_probs,
            )[0]
        else:
            rollout_idx = random.randint(0, len(steps) - 1)

        if lock: lock.acquire()
        if rollout_idx < len(children):
            if debug: print(f'[roll-out depth={cnt}, idx={rollout_idx} (exist)]:', expr)
            next_node = children[rollout_idx]
        else:
            if debug: print(f'[roll-out depth={cnt}, idx={rollout_idx} (expand)]:', expr)
            next_node = expand(node, steps[rollout_idx])
        if lock: lock.release()

        node = next_node
        cnt += 1

        if debug:
            print(end='\n')

    if debug:
        if reward > 0: print('\033[91m', end='')
        print(f'[reward ] val={reward:.2f}')
        print('\033[0m')
    return node, reward


def backprop(node, reward):
    """
    反向传播：通过 reward 更新 roll-out 路径上所有节点的统计数据
    """
    while node is not None:
        q, n, narr, father, axiom, axiom_idx, children = node
        node[0] += reward
        node[1] += 1
        node = father


def evaluate(
    node, all_axioms, steps, n_sample_times, sample_depth, visited,
    debug=False, nn_models=None, k=0, step_probs=None, worker=0, lock=None):
    """
    采样函数（顺序执行版）：进行 n_sample_times 次采样
    """
    for i, _ in enumerate(range(n_sample_times)):
        if lock: lock.acquire()
        child = move_policy(node, steps, debug=debug, prior_arr=step_probs)
        if lock: lock.release()

        if True:
            rich.print(f"[red]worker#{worker} sample[/] {i}th/{n_sample_times}")
            #print('[step probs]', step_probs)
            print('[UCT]', [round(w, 5) for w in children_weights(node)])
            #for s,a,ai in steps:
            #    print(f'axiom#{ai}', a, end='\n---\n')
            #    print(expression.narr2tex(s))
            #    print()

        bottom_node, reward = rollout(
            child, all_axioms, sample_depth, visited, debug=debug,
            nn_models=nn_models, k=k, lock=lock
        )

        if lock: lock.acquire()
        backprop(bottom_node, reward)
        if lock: lock.release()


def evaluate_parallel(
    node, all_axioms, steps, n_sample_times, sample_depth, visited, k=0,
    n_worker=10, batch_sz=2, debug=False, nn_models=None, use_thread=False):
    """
    采样函数（并行版本）：进行 n_sample_times 次采样
    """
    n_stages = n_sample_times // n_worker // batch_sz
    lock = manager.Lock() if manager else None

    for b in range(n_stages):
        #if debug:
        if True:
            name = 'multi-thread' if use_thread else 'multi-process'
            rich.print(f"[red]{name} stage[/] {b + 1}th/{n_stages} with " +
            f"{n_worker} workers, each {batch_sz}/{n_sample_times} samples")

        if use_thread:
            with ThreadPoolExecutor(max_workers=n_worker) as executor:
                for i in range(batch_sz):
                    executor.submit(evaluate,
                        node, all_axioms, steps, batch_sz, sample_depth, visited,
                        debug=False, nn_models=nn_models, k=k, worker=i, lock=lock
                    )
        else:
            with ProcessPoolExecutor(max_workers=n_worker) as executor:
                for i in range(n_worker):
                    executor.submit(evaluate,
                        node, all_axioms, steps, batch_sz, sample_depth, visited,
                        debug=False, nn_models=nn_models, k=k, worker=i, lock=lock
                    )
    #quit()


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
    max_val = max([val for val, narr, a, ai in steps])

    while len(steps) > 1:
        cur_step = steps[-1]
        val, narr, _, _ = cur_step

        if val >= max_val:
            break
        else:
            if debug:
                expr = expression.narr2tex(narr)
                rich.print(f'[magenta]back-off[/magenta] {expr}')
            steps.pop()

    return steps


def mcts(narr0, all_axioms, sample_depth=8, n_sample_times=200, n_maxsteps=150, k=3,
         debug=False, nn_models=None, training=False, force_single_thread=False):
    #       q  n   narr  father  axiom   axiomIdx  children
    root = [0, 1, narr0, None,  None,      -1,       []    ]
    moves = [root]
    global manager

    if nn_models is None and not force_single_thread:
        # prepare proxy structure for parallel processes
        root = manager.list(root)
        moves = manager.list([root])
    else:
        manager = None

    visited = set([expression.narr2tex(narr0)])

    while True:
        node = moves[-1]
        q, n, narr, father, axiom, axiom_idx, children = node

        # debug print
        if True:
        #if debug:
            print('\033[94m', end='')
            expr_val = state.value(narr)
            print(f'[current] step={len(moves)}, val={expr_val:.1f}:',
                expression.narr2tex(narr), end='')
            print('\033[0m', end='\n')

        steps, step_probs = policy_steps(
            narr, all_axioms, k=k, debug=debug, nn_models=nn_models, trust_nn=False
        )

        if debug:
            rich.print(f'[magenta]candidate steps={len(steps)}[/]')
            for n, a, ai in steps:
                print(a.name(), ':')
                print(expression.narr2tex(n), end='\n\n')

        if len(steps) == 0:
            if nn_models and training:
                policy = 0
                #policy_fine_tuning(nn_models, expr, policy, debug=debug, all_axioms=all_axioms)
            break

        if manager:
            evaluate_parallel(
                node, all_axioms, steps, n_sample_times, sample_depth, visited,
                debug=debug, nn_models=nn_models, k=k
            )
        else:
            evaluate(
                node, all_axioms, steps, n_sample_times, sample_depth, visited,
                debug=debug, nn_models=nn_models, k=k, step_probs=step_probs
            )

        # selection
        move_choice, w = best_child_of(node, c_param=.0, debug=debug)
        move_to_expr = move_choice[2]
        if w == 0 or move_to_expr in visited:
            print(f'[abort] best w={w:.2f}, visited: {move_to_expr in visited}')
            break
        else:
            if nn_models and training:
                policy = move_choice[5] + 1
                #policy_fine_tuning(nn_models, expr, policy, debug=debug, all_axioms=all_axioms)

            if manager:
                move_choice = manager.list(move_choice)
            moves.append(move_choice)

            visited.add(move_to_expr)
            #if debug: print('[visited]', visited)

            if len(moves) > n_maxsteps:
                break

    # construct steps to be returned
    steps = [(state.value(e), e, a, ai) for q, n, e, f, a, ai, c in moves]
    steps = back_off_step(steps, debug=True)

    if nn_models and training:
        # fine-tune value network
        for i, (_, e, _, _) in enumerate(steps):
            value = -(len(steps) - i - 1)
            #value_fine_tuning(nn_models, e, value, debug=debug)
    return steps


if __name__ == '__main__':
    from render_math import render_steps
    axioms = common_axioms()

    test_exprs = ['( \\frac{5}{6} + \\frac{3}{8} ) 24']
    test_exprs = ['-629 + (0.609 + \\frac{50}{x + y} -1) \cdot x -x^{2} \cdot 2 + y^{2} = 0']

    nn_models = None
    timer = Timer()

    debug = True

    for i, expr in enumerate(test_exprs):
        narr = expression.tex2narr(expr)

        n_sample_times = 10 if nn_models else 200
        with timer:
            steps = mcts(narr, axioms,
                debug=debug, n_sample_times=n_sample_times,
                nn_models=nn_models, force_single_thread=False)

        total_steps += len(steps)

        render_steps(steps)
        print(f'Test case: {i} / {len(test_exprs) - 1}')

        answer = steps[-1][1]
        truths = answers[i]
        if answer in truths:
            rich.print('[bold green]pass[/bold green]')
        else:
            print('[truths]', truths)
            rich.print('[bold red]failed[/]')

            #print('Enter to continue')
            #input()
