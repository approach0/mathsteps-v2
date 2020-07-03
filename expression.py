from lark import Lark, UnexpectedInput
from lark import Transformer
import rich


lark = Lark.open('grammar.lark', rel_to=__file__, parser='lalr', debug=False)
debug = False


class NarrRoot():

    def __init__(self, sign, Type, animation=None):
        self.sign = sign
        self.Type = Type
        self.animation = animation
        self.animatGrp = None

    def get(self):
        return self.sign, self.Type

    def set(self, sign, Type):
        self.sign = sign
        self.Type = Type

    def __repr__(self):
        if self.animation is None:
            return f'<{self.sign}, {self.Type}>'
        elif self.animatGrp is None:
            return f'<{self.sign}, {self.Type}, {self.animation}>'
        else:
            return f'<{self.sign}, {self.Type}, {self.animation}{self.animatGrp}>'

    def __getitem__(self, idx):
        if idx == 0:
            return self.sign
        elif idx == 1:
            return self.Type
        elif idx == 2:
            return self.animation
        else:
            raise ValueError('NarrRoot get index out of bound.')

    def __setitem__(self, idx, value):
        if idx == 0:
            self.sign = value
        elif idx == 1:
            self.Type = value
        elif idx == 2:
            self.animation = value
        else:
            raise ValueError('NarrRoot set index out of bound.')

    def __eq__(self, other):
        return self.sign == other.sign and self.Type == other.Type

    def copy(self):
        sign, Type = self.get()
        return NarrRoot(sign, Type)


class Tree2NestedArr(Transformer):

    @staticmethod
    def children(x):
        """
        得到节点的子节点
        """
        if isinstance(x, list):
            return x[1:]
        else:
            return x.children

    @staticmethod
    def unwrap_null_reduce(x):
        if len(x[0]) == 0:
            return [x[1]]
        elif len(x[1]) == 0:
            return [x[0]]
        else:
            return x

    @staticmethod
    def passchildren(x, op_type):
        x = Tree2NestedArr().unwrap_null_reduce(x)
        x = [[(child[0])] + [_ for _ in Tree2NestedArr().children(child)] for child in x]

        return passchildren(NarrRoot(+1, op_type), x)[0]

    @staticmethod
    def negate(x):
        """
        符号变负号
        """
        sign, Type = x[0].get()
        sign = sign * (-1)
        x[0].set(sign, Type)
        return x

    def null_reduce(self, x):
        """
        处理 null reduce
        """
        return []

    def add(self, x):
        """
        转换 a + b （满足交换律）
        """
        if len(x[0]) == 0:
            return x[1]
        else:
            return self.passchildren(x, 'add')

    def eq(self, x):
        """
        转换 a = b
        """
        return [NarrRoot(+1, 'eq'), x[0], x[1]]

    def minus(self, x):
        """
        转换 a - b （满足交换律）
        """
        x[1] = self.negate(x[1])
        if len(x[0]) == 0:
            return x[1]
        else:
            return self.passchildren(x, 'add')

    def mul(self, x):
        """
        转换 a * b （满足交换律）
        """
        x = self.passchildren(x, 'mul')
        return x

    def div(self, x):
        """
        转换 a ÷ b
        """
        return [NarrRoot(+1, 'div'), x[0], x[1]]

    def frac(self, x):
        """
        转换 分数
        """
        return [NarrRoot(+1, 'frac'), x[0], x[1]]

    def ifrac(self, x):
        """
        转换 带分数 (improper fraction)
        """
        if x[0] == '&':
            num_narr = [NarrRoot(1, 'VAR'), 'v']
        else:
            num = float(x[0])
            num_narr = self.number([x[0]])
            if not num.is_integer():
                return self.mul([num_narr, self.frac([x[1], x[2]])])

        return [NarrRoot(+1, 'ifrac'), num_narr, x[1], x[2]]

    def sqrt(self, x):
        """
        转换 分数
        """
        return [NarrRoot(+1, 'sqrt'), x[0]]

    def sup(self, x):
        """
        转换 指数
        """
        return [NarrRoot(+1, 'sup'), x[0], x[1]]

    def number(self, n):
        """
        转换 常数
        """
        return [NarrRoot(+1, n[0].type), float(n[0])]

    def var(self, x):
        """
        转换 变量、符号
        """
        return [NarrRoot(+1, x[0].type), str(x[0])]

    def abs(self, x):
        """
        转换 绝对值
        """
        return [NarrRoot(+1, 'abs'), x[0]]

    def grp(self, x):
        """
        转换 括号
        """
        return x[0]

    def wildcards(self, x):
        """
        转换 括号
        """
        number = str(x[1])
        return [NarrRoot(+1, 'WILDCARDS'), number]

    def animation(self, x):
        name = str(x[1])
        x[0][0].animation = name
        return x[0]

    def animation_group(self, x):
        name = str(x[1])
        group = int(x[2])
        x[0][0].animation = name
        x[0][0].animatGrp = group
        return x[0]

    def animation_replace(self, x):
        return [NarrRoot(+1, 'REPLACE'), x[0], x[1]]


def tex_parse(tex):
    """
    TeX 解析，调用 Lark
    """
    return lark.parse(tex)


def tree2narr(tree):
    """
    Lark 树转换成 narr (nested array)
    """
    return Tree2NestedArr().transform(tree)


def tex2narr(tex):
    """
    TeX 换成 narr (nested array)
    """
    return tree2narr(tex_parse(tex))


def terminal_tokens():
    return ['NUMBER', 'VAR', 'WILDCARDS']


def commutative_operators():
    return ['add', 'mul']


def binary_operators():
    return ['div', 'frac', 'sup', 'eq', 'REPLACE']


def no_permute_tokens():
    return ['ifrac']


def need_inner_fence(narr):
    """
    表达式 narr 在符号和本身之间，须不须要包裹括号
    """
    sign, Type = narr[0].get()

    if debug: print('inner fence?', narr)

    if sign < 0 and len(narr) > 2: # non-unary
        if Type in ['mul', 'frac', 'sup', 'ifrac']:
            return False
        else:
            return True
    else:
        return False


def need_outter_fence(root, child_narr, rank=0):
    """
    子表达式 child_narr 在挂到 root 下时，须不须要包裹括号
    """
    child_root = child_narr[0]

    #debug = True
    if debug: print('outter fence?', root, '@@@', child_narr)

    if root is None:
        return False
    elif root[1] in ['frac', 'ifrac', 'abs', 'sqrt', 'add', 'eq']:
        return False
    elif root[1] == 'sup' and child_root[1] == 'sqrt':
        return True
    elif child_root[0] == +1:
        if len(child_narr) <= 2: # unary
            return False
        elif root[1] == 'sup' and child_root[1] in ['frac', 'afrac', 'sup']:
            return True
        elif child_root[1] in ['frac', 'sup']:
            return False
        return True

    #elif child_root[0] == -1:
    #    if root[1] == 'mul' and root[0] > 0 and rank == 1:
    #        return False

    return True


def narr2tex(narr, parentRoot=None, tag=True, rank=0):
    """
    narr (nested array) 换成 TeX
    """
    root = narr[0]
    sign, token = root.get()
    sign = '' if sign > 0 else '-'

    if token in terminal_tokens():
        val = narr[1]
        if token == 'WILDCARDS':
            expr = '*{' + str(val) + '}'
        elif token == 'NUMBER':
            if val.is_integer():
                expr = str(int(val))
            else:
                expr = str(val)
        else:
            expr = str(val)

    elif token in commutative_operators():
        expr = ''
        sep_op = ' + ' if token == 'add' else ' \\times '
        operands = narr[1:]
        for i, child in enumerate(operands):
            to_append = narr2tex(child, parentRoot=root, tag=tag, rank=i+1)

            if i == 0:
                expr += to_append
            elif to_append[0] == '-':
                expr += ' - ' + to_append[1:]
            else:
                expr += sep_op + to_append

    elif token in binary_operators():
        expr1 = narr2tex(narr[1], parentRoot=root, tag=tag, rank=1)
        expr2 = narr2tex(narr[2], parentRoot=root, tag=tag, rank=2)

        expr = None
        if token == 'div':
            expr = expr1 + ' \\div ' + expr2
        elif token == 'frac':
            expr = '\\frac{' + expr1 + '}{' + expr2 + '}'
        elif token == 'sup':
            expr = expr1 + '^{' + expr2 + '}'
        elif token == 'eq':
            expr = expr1 + ' = ' + expr2
        elif token == 'REPLACE':
            expr = '`' + expr1 + '`[replace]{' + expr2 + '}'
        else:
            raise Exception('unexpected token: ' + token)

    elif token == 'ifrac':
        expr1 = narr2tex(narr[1], parentRoot=root, tag=tag, rank=1)
        expr2 = narr2tex(narr[2], parentRoot=root, tag=tag, rank=2)
        expr3 = narr2tex(narr[3], parentRoot=root, tag=tag, rank=3)
        expr = expr1 + '\\frac{' + expr2 + '}{' + expr3 + '}'

    else:
        expr = narr2tex(narr[1], parentRoot=root, tag=tag, rank=1)

        if token == 'abs':
            expr = '\\left|' + expr + '\\right|'
        elif token == 'sqrt':
            expr = '\sqrt{' + expr + '}'
        else:
            raise Exception('unexpected token: ' + token)

    if need_inner_fence(narr):
        expr = '(' + expr + ')'
    expr = sign + expr
    if need_outter_fence(parentRoot, narr, rank=rank):
        expr = '(' + expr + ')'
    if tag and root.animation:
        if root.animatGrp is None:
            expr = '`' + expr + '`[' + root.animation + ']'
        else:
            expr = '`' + expr + '`[' + root.animation + ',' + str(root.animatGrp) + ']'
    return expr


def narr_prettyprint(narr, level=0):
    """
    narr 的美化版打印
    """
    root = narr[0]
    children = narr[1:]
    sign, token = root.get()

    if token in ['NUMBER', 'VAR', 'WILDCARDS']:
        print('    ' * level, narr)
        return

    print('    ' * level, root)
    for c in children:
        narr_prettyprint(c, level + 1)


def get_wildcards_index(narr):
    root_sign, root_type = narr[0].get()
    if root_type not in terminal_tokens():
        children_tokens = [c[0][1] for c in narr[1:]]
    else:
        children_tokens = [narr[0][1]]
    try:
        wildcards_index = children_tokens.index('WILDCARDS')
    except ValueError:
        wildcards_index = None
    return wildcards_index


def passchildren(root, children):
    sign, op_type = root.get()
    new_narr = [root.copy()]
    any_change = False
    for child in children:
        child_sign, child_type = child[0].get()
        if child_type == op_type:
            if child_type == 'add':
                # distribute sign
                for grand_child in child[1:]:
                    grand_sign, grand_type = grand_child[0].get()
                    grand_child[0].set(grand_sign * child_sign, grand_type)
                    new_narr.append(grand_child)

            elif child_type == 'mul':
                # reduce sign
                new_narr[0].set(sign * child_sign, op_type)
                new_narr += child[1:]

            else:
                raise Exception('unexpected type: ' + Type)

            # this part will only cause change if child sign is negative
            if child_sign < 0:
                any_change = True
        else:
            if op_type == 'mul' and child_sign < 0:
                child[0].set(+1, child_type)
                new_narr[0].set(sign * -1, op_type)
                any_change = True

            new_narr.append(child)

    return new_narr, any_change


def canonicalize(narr):
    sign, Type = narr[0].get()
    if Type == 'add':
        # -(a + ...) becomes -a - ...
        return passchildren(NarrRoot(+1, Type), [narr])
    else:
        return passchildren(NarrRoot(sign, Type), narr[1:])


def replace_or_pass_children(narr, i, substitute):
    """
    表达式 narr 的第 i 个子节点，用 substitute 替换。
    如果表达式有相同的 root 操作符，且满足交换律，则把两个表达式合并。
    """
    root = narr[0]
    sign, Type = root.get()
    if Type == substitute[0][1] and Type in ['add', 'mul']:
        new_narr, _ = passchildren(NarrRoot(sign, Type), [substitute])
        narr[0] = new_narr[0]
        del narr[1 + i]
        narr[:] = narr[0: 1 + i] + new_narr[1:] + narr[i + 1:]
    else:
        narr[1 + i] = substitute
    return narr


def trim_animations(narr, top_root=True):
    root = narr[0]
    sign, token = root.get()

    if top_root and token == 'REPLACE':
        pseudo_narr = [NarrRoot(sign, 'add'), narr]
        trim_animations(pseudo_narr)
        narr[:] = pseudo_narr
        return

    root.animation = None
    root.animatGrp = None

    if token in terminal_tokens():
        return

    children = narr[1:]
    for i, child in enumerate(children):
        child_root = child[0]
        child_sign, child_token = child_root.get()

        if child_token == 'REPLACE':
            substitute = child[2]
            substitute[0].sign *= child_sign
            replace_or_pass_children(narr, i, substitute)
            child = substitute
        elif child_root.animation in ['remove',  'moveBefore']:
            narr[1 + i] = None
            continue

        trim_animations(child, top_root=False)

    # prune None children and if necessary, pass the children of single
    # commutative operands to its grand father.
    narr[:] = [x for x in narr if x is not None]
    if len(narr[1:]) == 0:
        raise ValueError('trim_animations result in a childless node')
    elif token in commutative_operators() and len(narr[1:]) == 1:
        narr[:] = narr[1]


if __name__ == '__main__':
    debug = True
    lark = Lark.open('grammar.lark', rel_to=__file__, parser='lalr', debug=debug)

    test_expressions = [
        '-(a+b)',
        '2 -(-3)',
        '2 -(-3b)',
        '-2b + 1',
        '(-2 \cdot b) c',
        '-(- 1 + (-2 \cdot b) \cdot a - 3)',
        'a(-2 \cdot b) c',
        '-c(a \div b)',
        '-c(-ad \div b)',
        '-c\\frac{a}{b}',
        '-c(-\\frac{a}{b})',
        'a-(-b + 3a)',
        '-x^{2}',
        '-3x^{2}',
        'x-\\left| -ab \\right|',
        '+(i+j)x',
        '1 +a *{1}',
        '2 \cdot (-3 \\frac{1}{2})',
        '+1 = -3',
        '\\frac{-2}{3}',
        '-(-a)(-b)',
        '& \\frac{y}{x}',
        'a-b-c+d-f',
        '-a(-2)(-3)4',
        '3.2 \\frac{1}{2}',
        '-(-a)b',
        '(-a)b',
        '`3`[replace]{1+2} + 3',
        '`(a+b)`[remove]c',
        '`3`[remove,2]',
        '-(`(3\\frac{-2}{4})`[replace]{(3 + 2)})',
        '`(-2)^{2}`[replace]{4} + 1',
        '(\sqrt{2})^{2}',
        'a -`2`[moveAfter,2] = `2`[moveBefore,2] + `0`[add]'
    ]

    for expr in test_expressions[-1:]:
    #for expr in test_expressions[:]:
        rich.print('[bold yellow]original:[/]', end=' ')
        print(expr, end="\n\n")
        tree = None
        try:
            tree = tex_parse(expr)
            print(tree.pretty())
        except UnexpectedInput as error:
            print(error)
            continue

        narr = tree2narr(tree)

        rich.print('[[origin narr]]', narr)
        #trim_animations(narr)
        #rich.print('[[trim narr]]', narr)

        tex = narr2tex(narr)
        rich.print('[bold yellow]TeX:[/]', end=' ')
        print(tex)

        narr_prettyprint(narr)
        print()
