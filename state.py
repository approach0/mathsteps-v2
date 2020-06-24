import math
import expression

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

def token_stats(narr, stats={}, right_side_of_eq=False, inside_of_sqrt=False, level=0):
    """
    得到 表达式内符号的频率统计
    """
    root = narr[0]
    children = narr[1:]
    sign, token = root

    #print(f'L{level}', expression.narr2tex(narr))

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
            if level > 2:
                if 'n_deepest_var_level' not in stats:
                    stats['n_deepest_var_level'] = level
                elif stats['n_deepest_var_level'] < level:
                    stats['n_deepest_var_level'] = level

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
            token_stats(c, stats, right_side_of_eq=True, level=level)
        elif token == 'sqrt':
            token_stats(c, stats, inside_of_sqrt=True, level=level)
        else:
            token_stats(c, stats, right_side_of_eq, level=level+1)
    return stats


def value_v1(narr, debug=False):
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
        'n_deepest_var_level': 100,
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


def collect_stats(narr, stats, level, grandRoot):
    root = narr[0]
    children = narr[1:]
    sign, token = root

    if sign < 0:
        stats['neg'] += 1

    if token in expression.terminal_tokens():
        if stats['max_level'] < level:
            stats['max_level'] = level

        if token == 'NUMBER':
            num = children[0]

            stats['NUMBER_sum'] += abs(num)
            if grandRoot and grandRoot[1] == 'sqrt':
                stats['NUMBER_in_sqrt'] += abs(num)

            if num.is_integer():
                if abs(num) == 1 or abs(num) == 0:
                    stats['NUMBER_one_zero'] += 1
                else:
                    stats['NUMBER_other_ints'] += 1

                n_zeros = right_padding_zeros(num)
                stats['NUMBER_pad_zeros'] += n_zeros
            else:
                stats['NUMBER_decimal'] += 1
        else:
            stats['VAR_cnt'] += 1

        return

    for i, c in enumerate(children):
        if token in ['frac', 'ifrac']:
            collect_stats(c, stats, level + 3, root)
        else:
            collect_stats(c, stats, level + 1, root)


def value_v2(narr, level=0, debug=False):
    stats = {
        'neg': 0,
        'max_level': 0,
        'NUMBER_sum': 0,
        'NUMBER_in_sqrt': 0,
        'NUMBER_one_zero': 0,
        'NUMBER_other_ints': 0,
        'NUMBER_pad_zeros': 0,
        'NUMBER_decimal': 0,
        'VAR_cnt': 0
    }

    collect_stats(narr, stats, 0, None)

    tex = expression.narr2tex(narr)
    parentheses_cnt = tex.count('(')

    complexity = [
        stats['max_level'],
        #1.0 * parentheses_cnt,
        1.0 * math.log(1 + math.log(1 + stats['NUMBER_sum'])),
        5.0 * math.log(1 + stats['NUMBER_in_sqrt']),
        1.0 * math.log(1
            + 0.2 * stats['NUMBER_one_zero']
            + 1.0 * stats['NUMBER_other_ints']
            + 1.0 * stats['neg']
            + 3.0 + stats['NUMBER_decimal']
            - 0.1 * stats['NUMBER_pad_zeros'],
        ),
        1.5 * math.log(1
            + 3.0 * stats['VAR_cnt']
        )
    ]

    if debug:
        print('parentheses_cnt:', parentheses_cnt)
        print(stats)
        print(complexity)

    return -sum(complexity)


def test(tex, state_value):
    """
    包装测试函数
    """
    import expression
    narr = expression.tex2narr(tex)
    print('[expression]', tex)
    print(state_value(narr, debug=True))
    print()


if __name__ == '__main__':
    #print(right_padding_zeros(-100))
    #print(right_padding_zeros(0))

    #test('0 + 0 + 0', value_v2)
    #test('0', value_v2)

    #test('10 \cdot x + 15 = 15', value_v2)
    #test('10 \cdot x + 15 -15 = 0', value_v2)

    #test('100 \\times 25', value_v2)
    #test('2500', value_v2)

    #test('2(x+y)+1+2', value_v2)
    #test('2x+2y+3+4', value_v2)

    #test('-3', value_v2)
    #test('3', value_v2)

    #test('10 + 2', value_v2)
    #test('7 + 5', value_v2)

    #test('0 + 3', value_v2)
    #test('6 - 3', value_v2)

    #test('3 \\sqrt{3}', value_v2)
    #test('\\sqrt{27}', value_v2)

    #test('81 \\sqrt{9}', value_v2)
    #test('\\sqrt{59049}', value_v2)

    #test('-x \\times 0.391 - 629 - x^{2} \\times 2 + y^{2} + x \\times \\frac{50}{x + y} = 0', value_v2)
    #test('x \\times 50 + (x + y) \\times (-629 - x^{2} \\times 2 + y^{2}) + x^{2} \\times 0.391 + x \\times 0.391 \\times y = 0', value_v2)
    #test('x \\times 50 + x^{2} \\times 0.391 + x \\times 0.391 \\times y + 2 \\times x^{2} \\times x + 2 \\times x^{2} \\times y - 629 \\times x - 629 \\times y + y^{2} \\times x + y^{2} \\times y = 0', value_v2)

    #test('\\frac{1}{2}', value_v2)
    #test('4 - 3 \\frac{1}{2}', value_v2)

    test('-x \\times 0.391 - 629 - x^{2} \\times 2 + y^{2} + \\frac{50 \\times x}{x + y} = 0', value_v2)
    test('50 \\times x + (x + y) \\times (-x \\times 0.391 - 629 - x^{2} \\times 2 + y^{2}) = (x + y) \\times 0', value_v2)
    test('50 \\times x + (x + y) \\times x \\times 0.391 + (-629 - x^{2} \\times 2 + y^{2}) \\times x - y \\times 629 + y \\times x^{2} \\times 2 + y \\times y^{2} = 0', value_v2)
