import rich
import random
import expression
from lark import Token
from expression import NarrRoot
from expression import Tree2NestedArr
tr2narr = Tree2NestedArr()


def random_tok(only_number=False, small_number=False):
    """
    按照非均匀分布生成随机 token
    """

    if only_number:
        t = nonUniformChoice(
            ['INT', 'FLOAT'],
            [0.9, 0.1]
        )
    else:
        t = nonUniformChoice(
            ['VAR', 'INT', 'FLOAT'],
            [0.5, 0.5, 0.1]
        )

    if t == 'VAR':
        sym = random.choice(['x', 'y'])
        return tr2narr.var([Token('VAR', sym)])

    elif t == 'INT':
        if small_number:
            sym = 2
        else:
            sym = random.randint(0, 50)

        sign = nonUniformChoice(
            [+1, -1],
            [0.8, 0.2]
        )

        num_tok = tr2narr.number([Token('NUMBER', sign * sym)])
        return num_tok

    else:
        num = random.uniform(-5, 5)
        num = round(num, 3)
        num_tok = tr2narr.number([Token('NUMBER', num)])
        return num_tok


def nonUniformChoice(population, weights):
    """
    分均匀分布选择函数
    """
    return random.choices(
        population = population,
        weights = weights,
    )[0]


def random_operator(commutative=False):
    """
    按照非均匀分布生成随机操作符
    """
    possible_ops = [
        (0.2, 2, tr2narr.add),
        (0.2, 2, tr2narr.mul),

        (0.10, 2, tr2narr.frac),

        (0.25, 2, tr2narr.sup),
        (0.4, 2, tr2narr.minus),

        (0.05, 2, tr2narr.div),
        (0.05, 1, tr2narr.abs)
    ]

    if commutative:
        possible_ops = possible_ops[0:2]

    return nonUniformChoice(
        [t[1:] for t in possible_ops],
        [t[0] for t in possible_ops]
    )


def bounded_guassian_sample(sigma, maxval):
    """
    按照正态分布生成难度正数
    """
    sample = int(round(random.normalvariate(0, sigma), 0) + 1)
    if sample < 1:
        return 1
    else:
        return min(maxval, sample)


def random_exp(complexity=2):
    """
    按照复杂度指示生成随机数学表达式
    """
    err = False
    tex = ''
    t1 = tr2narr.null_reduce([])
    for _ in range(complexity):
        # null-reduce must be commutative
        commutative = (len(t1) == 0)

        n_oprands, build_op = random_operator(commutative=commutative)

        if n_oprands == 2:
            always_t12 = False

            if tr2narr.sup == build_op:
                t2 = random_tok(only_number=True, small_number=True)
                always_t12 = True

            elif 'simple' == nonUniformChoice(
                ['complex', 'simple'],
                [0.2, 0.8]
            ):
                t2 = random_tok()
            else:
                random_complexity = bounded_guassian_sample(3, 5)
                tex, err = random_exp(complexity=random_complexity)
                if err: break
                t2 = expression.tex2narr(tex)

            if always_t12 or random.choice(['12', '21']) == '12':
                t1 = build_op([t1, t2])
            else:
                t1 = build_op([t2, t1])
        else:
            t1 = build_op([t1])

        try:
            tex = expression.narr2tex(t1)
            expression.tex2narr(tex)
        except Exception as err_msg:
            err = True
            #rich.print('[red]invalid random expression')
            break

    return tex, err


def random_polynomial_term():
    err = False
    build_op = tr2narr.sup
    t1 = random_tok()

    if 'order2' == nonUniformChoice(
        ['order1', 'order2'],
        [0.5, 0.5]
    ):
        sign = nonUniformChoice(
            [+1, -1],
            [0.5, 0.5]
        )

        if sign < 0:
            t0 = tr2narr.null_reduce([])
            t1 = tr2narr.minus([t0, t1])

        t2 = random_tok(only_number=True, small_number=True)
        t1 = build_op([t1, t2])

    try:
        tex = expression.narr2tex(t1)
        expression.tex2narr(tex)
    except Exception as err_msg:
        err = True

    return tex, err


def random_terms():
    """
    将随机表达式按项组合，生成随机加和表达式
    """
    any_err = True
    build_op = tr2narr.add
    t1 = tr2narr.null_reduce([])

    # the number of terms is sampled from normal distribution
    n_terms = bounded_guassian_sample(3, 6)

    for _ in range(n_terms):
        if 'nested' == nonUniformChoice(
            ['nested', 'polynomial'],
            [0.2, 0.8]
        ):
            tex_t2, err = random_exp()
        else:
            tex_t2, err = random_polynomial_term()

        if err:
            continue
        else:
            any_err = False

        t2 = expression.tex2narr(tex_t2)
        if random.choice(['12', '21']) == '12':
            t1 = build_op([t1, t2])
        else:
            t1 = build_op([t2, t1])

    if len(t1) == 0:
        return '', True
    else:
        tex = expression.narr2tex(t1)
        return tex, any_err


def random_equations():
    """
    生成等号两边由随机表达式组成的等式
    """
    build_op = tr2narr.eq
    tex1, err1 = random_terms()
    tex2, err2 = random_terms()

    if err1 or err2:
        return '', True

    try:
        t1 = expression.tex2narr(tex1)
        t2 = expression.tex2narr(tex2)
        t1 = build_op([t1, t2])
        tex = expression.narr2tex(t1)
        expression.tex2narr(tex)
    except Exception as err_msg:
        return '', True

    return tex, False


if __name__ == '__main__':
    #for _ in range(16000):
    for _ in range(100):
        expr, err = random_terms()
        expr, err = random_polynomial_term()
        expr, err = random_equations()
        if err: continue
        print(expr, end='\n')
