from lark import Lark, UnexpectedInput
from lark import Transformer
import rich

lark = Lark.open('grammar.lark', rel_to=__file__, parser='lalr', debug=True)

class Tree2NestedArr(Transformer):
    """
    中间表示的转换类。把 Lark 的表示树转换成我们所期望的表示。
    """

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
    def passchildren(x, ifis, reduce_sign=False):
        """
        如果子二叉树的 token 是 ifis 的话，将子二叉树合并到当前节点（扁平化）
        """
        x = Tree2NestedArr().unwrap_null_reduce(x)
        # handle two commutative tree of the same type
        sign = 1
        ret = []
        for i in range(len(x)):
            child_root = x[i][0]
            child_sign, child_type = child_root
            if reduce_sign: sign *= child_sign
            if child_type == ifis:
                ret += Tree2NestedArr().children(x[i])
            else:
                ret.append(x[i])

        return [(sign, ifis)] + ret

    @staticmethod
    def negate(x):
        """
        符号变负号
        """
        sign, Type = x[0]
        sign = sign * (-1)
        x[0] = sign, Type
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
        return self.passchildren(x, 'add')

    def eq(self, x):
        """
        转换 a = b
        """
        return [(+1, 'eq'), x[0], x[1]]

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
        x = self.passchildren(x, 'mul', reduce_sign=True)
        return x

    def div(self, x):
        """
        转换 a ÷ b
        """
        return [(+1, 'div'), x[0], x[1]]

    def frac(self, x):
        """
        转换 分数
        """
        return [(+1, 'frac'), x[0], x[1]]

    def sqrt(self, x):
        """
        转换 分数
        """
        return [(+1, 'sqrt'), x[0]]

    def sup(self, x):
        """
        转换 指数
        """
        return [(+1, 'sup'), x[0], x[1]]

    def number(self, n):
        """
        转换 常数
        """
        return [(+1, n[0].type), float(n[0])]

    def var(self, x):
        """
        转换 变量、符号
        """
        return [(+1, x[0].type), str(x[0])]

    def abs(self, x):
        """
        转换 绝对值
        """
        return [(+1, 'abs'), x[0]]

    def par_grp(self, x):
        """
        转换 圆括号
        """
        return x[0]

    def sq_grp(self, x):
        """
        转换 方括号
        """
        return x[0]


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


def sign_wrap(root, expr):
    sign, Type = root
    if sign > 0:
        return expr
    elif Type in ['add']:
        return '-(' + expr + ')'
    else:
        return '-' + expr


def narr2tex(arr):
    """
    narr (nested array) 换成 TeX
    """
    root = arr[0]
    sign, token = root

    # HANDLE: number, var
    if token in ['NUMBER', 'VAR', 'WILDCARDS']:
        val = arr[1]
        # omit decimal point
        val = int(val) if token == 'NUMBER' and val.is_integer() else val
        sign = '' if sign > 0 else '-'
        return sign + str(val)

    # HANDLE: add, mul
    if token in ['add', 'mul']:
        expr = ''
        sep_op = ' + ' if token == 'add' else ' \\cdot '
        operands = arr[1:]
        for i, child in enumerate(operands):
            to_append = narr2tex(child)
            child_sign, child_type = child[0]

            if token == 'mul' and child_type == 'add':
                to_append = '(' + to_append + ')'

            if i == 0:
                expr += to_append
            elif to_append[0] == '-':
                expr += to_append
            else:
                expr += sep_op + to_append

        return sign_wrap(root, expr)

    # HANDLE: div, frac, sup
    elif token in ['div', 'frac', 'sup', 'eq']:
        expr1 = narr2tex(arr[1])
        expr2 = narr2tex(arr[2])

        if token == 'div':
            return sign_wrap(root, expr1 + ' \\div ' + expr2)
        elif token == 'frac':
            return sign_wrap(root, '\\frac{' + expr1 + '}{' + expr2 + '}')
        elif token == 'sup':
            return sign_wrap(root, expr1 + '^{' + expr2 + '}')
        elif token == 'eq':
            return expr1 + ' = ' + expr2
        else:
            raise Exception('unexpected token: ' + token)
    # HANDLE: abs, sq_grp, par_grp, sqrt
    else:
        expr = narr2tex(arr[1])

        if token == 'abs':
            return sign_wrap(root, '\\left|' + expr + '\\right|')
        elif token == 'sq_grp':
            return sign_wrap(root, '[' + expr + ']')
        elif token == 'par_grp':
            return sign_wrap(root, '(' + expr + ')')
        elif token == 'sqrt':
            return sign_wrap(root, '\sqrt{' + expr + '}')
        else:
            raise Exception('unexpected token: ' + token)


def narr_prettyprint(arr, level=0):
    """
    narr 的美化版打印
    """
    root = arr[0]
    children = arr[1:]

    sign, token = arr[0]
    if token in ['NUMBER', 'VAR', 'WILDCARDS']:
        print('    ' * level, arr)
        return

    print('    ' * level, root)
    for c in children:
        narr_prettyprint(c, level + 1)



if __name__ == '__main__':
    test_expressions = ['2 -(-3)']
    test_expressions = ['-2b + 1']
    test_expressions = ['(-2 \cdot b) c']
    test_expressions = ['-(- 1 + (-2 \cdot b) \cdot a - 3)']
    test_expressions = ['a(-2 \cdot b) c']

    for expr in test_expressions:
        print(expr, end="\n\n")
        tree = None
        try:
            tree = tex_parse(expr)
            #print(tree.pretty())
        except UnexpectedInput as error:
            print(error)
            continue

        narr = tree2narr(tree)
        #print('[narr]', narr)

        tex = narr2tex(narr)
        rich.print('[red]TeX:[/]', end=' ')
        print(tex)

        narr_prettyprint(narr)
