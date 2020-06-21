import math

def right_padding_zeros(num):
    """
    得到 整数类型 数字的右边零的个数，否则返回 0
    """
    cnt = 0
    num = abs(num)
    Int = int(num)
    if Int != num:
        return cnt
    elif Int == 0:
        return 1

    while Int > 0:
        digit = Int % 10
        if digit != 0:
            break
        else:
            cnt += 1
        Int = Int // 10
    return cnt

def token_stats(narr, stats={}, right_side_of_eq=False, inside_of_sqrt=False):
    """
    得到 表达式内符号的频率统计
    """
    root = narr[0]
    children = narr[1:]
    sign, token = root

    def incr(d, k, v=1):
        if right_side_of_eq and k in [
            'VAR', 'NUMBER_decimal', 'NUMBER_integer', 'NUMBER_one'
        ]:
            if 'right_side_of_eq' in d:
                d['right_side_of_eq'] += v
            else:
                d['right_side_of_eq'] = v
        else:
            if k in d:
                d[k] += v
            else:
                d[k] = v

    # count negativity
    if sign < 0:
        incr(stats, 'neg')

    # count leaves
    if token in ['NUMBER', 'VAR']:
        if token == 'NUMBER':
            num = children[0]
            # test right-padding zeros
            n_zeros = right_padding_zeros(num)
            incr(stats, 'NUMBER_pad_zeros', n_zeros)
            # test ones
            if num == 1:
                incr(stats, 'NUMBER_one')
            elif num == 0:
                incr(stats, 'NUMBER_zero')
            elif num.is_integer():
                incr(stats, 'NUMBER_integer')
            else:
                incr(stats, 'NUMBER_decimal')

            # add number complexity
            if inside_of_sqrt:
                incr(stats, 'NUMBER_in_sqrt', abs(int(num)))
            else:
                incr(stats, 'NUMBER_sum', abs(int(num)))

        else: # count variables
            incr(stats, token)

        return stats

    else: # count operators
        incr(stats, token)

    for i, c in enumerate(children):
        # count subtree terms
        if inside_of_sqrt:
            incr(stats, 'n_terms_in_sqrt')
        else:
            incr(stats, 'n_terms')

        if i == 1 and token == 'eq':
            token_stats(c, stats, right_side_of_eq=True)
        elif token == 'sqrt':
            token_stats(c, stats, inside_of_sqrt=True)
        else:
            token_stats(c, stats, right_side_of_eq)
    return stats


def value(narr, debug=False):
    """
    计算 表达式的价值（等于各个符号频率的自定义加权和）
    """
    if isinstance(narr, str):
        return value(expression.tex2narr(narr))

    value_dict = {
        'VAR': 10,
        'NUMBER_integer': 0.5,
        'NUMBER_decimal': 2,
        'NUMBER_pad_zeros': - 0.2,
        'NUMBER_one':  - 0.1,
        'NUMBER_zero': 0.1,
        'NUMBER_in_sqrt': 0.5,
        'eq': 0,
        'neg': 0.5,
        'add': 2,
        'mul': 1,
        'div': 10,
        'frac': 8,
        'ifrac': 20,
        'sup': 4,
        'abs': 1,
        'sqrt': 1,
        'n_terms': 0.6,
        'n_terms_in_sqrt': 25,
        'right_side_of_eq': 15,
    }
    stats = token_stats(narr, {})

    if debug: print(stats)

    accum = 0
    # symbol type values
    for key in stats:
        if key in value_dict:
            accum += stats[key] * value_dict[key] 
    # number sum values
    if 'NUMBER_sum' in stats:
        accum += math.log(1 + stats['NUMBER_sum']) / 2
    if 'NUMBER_in_sqrt' in stats:
        accum += 1.5 * math.log(1 + stats['NUMBER_in_sqrt'])
    return -accum


def test(tex):
    """
    包装测试函数
    """
    import expression
    narr = expression.tex2narr(tex)
    print(tex)
    print(value(narr, debug=True))
    print()


if __name__ == '__main__':
    #print(right_padding_zeros(-100))
    #print(right_padding_zeros(0))

    #test('10 \cdot x + 15 = 15')
    #test('10 \cdot x + 15 -15 = 0')

    test('100 \\times 25')
    test('2500')
