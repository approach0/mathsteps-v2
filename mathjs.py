from lark import Lark, UnexpectedInput
from lark import Transformer
import rich
import json

lark = Lark.open('grammar.lark', rel_to=__file__, parser='lalr', debug=False)

class Tree2MathJS(Transformer):

    @staticmethod
    def gen_object(x, op=None, animation_name=None):
        if isinstance(x, float):
            obj = {
                "mathjs": "ConstantNode",
                "value": x
            }
        elif isinstance(x, str):
            obj = {
                "mathjs": "SymbolNode",
                "name": x
            }
        else:
            if op == 'add':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "+",
                    "fn": "add",
                    "implicit": False,
                    "args": [x[0], x[1]]
                }
            elif op == 'unary_add':
                obj = {
                    "mathjs": "OperatorNode",
                    "fn": "unaryPlus",
                    "op": "+",
                    "implicit": False,
                    "args": [x[0]]
                }
            elif op == 'minus':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "-",
                    "fn": "subtract",
                    "implicit": False,
                    "args": [x[0], x[1]]
                }
            elif op == 'unary_minus':
                obj = {
                    "mathjs": "OperatorNode",
                    "fn": "unaryMinus",
                    "op": "-",
                    "implicit": False,
                    "args": [x[0]]
                }
            elif op == 'eq':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "==",
                    "fn": "equal",
                    "implicit": False,
                    "args": [x[0], x[1]]
                }
            elif op == 'mul':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "*",
                    "fn": "multiply",
                    "implicit": False,
                    "args": [x[0], x[1]]
                }
            elif op == 'div':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "/",
                    "fn": "divide",
                    "implicit": False,
                    "args": [x[0], x[1]]
                }
            elif op == 'ifrac':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "ifrac",
                    "fn": "ifrac",
                    "implicit": False,
                    "args": [x[0], x[1], x[2]]
                }
            elif op == 'sup':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "^",
                    "fn": "pow",
                    "implicit": False,
                    "args": [x[0], x[1]]
                }
            elif op == 'sqrt':
                obj = {
                    "mathjs": "FunctionNode",
                    "fn": {
                        "mathjs": "SymbolNode",
                        "name": "sqrt"
                    },
                    "args": [x[0]]
                }
            elif op == 'abs':
                obj = {
                    "mathjs": "FunctionNode",
                    "fn": {
                        "mathjs": "SymbolNode",
                        "name": "abs"
                    },
                    "args": [x[0]]
               }
            elif op == 'grp':
                obj = {
                  "mathjs": "ParenthesisNode",
                  "content": x[0]
                }
            elif op == 'add':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-add',
                    '范围': '全'
                }
            elif op == 'remove':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-remove',
                    '范围': '全'
                }
            elif op == 'moveBefore':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-move-before',
                    '范围': '全',
                    '组': 'ani-pair-no-1'
                }
            elif op == 'moveAfter':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-move-after',
                    '范围': '全',
                    '组': 'ani-pair-no-1'
                }
            elif op == 'REPLACE':
                obj = x[0]
                subst = x[1]
                obj['变化'] = {
                    '类型': 'ani-replaceBefore',
                    '范围': '全',
                    '组': 'ani-pair-no-1',
                    '替换为': subst
                }
                subst['变化'] = {
                    '类型': 'ani-replaceAfter',
                    '范围': '全',
                    '组': 'ani-pair-no-1'
                }
            else:
                raise Exception('unexpected op: ' + op)


        return obj

    def null_reduce(self, x):
        return None

    def number(self, x):
        return self.gen_object(float(x[0]))

    def var(self, x):
        return self.gen_object(str(x[0]), op=x[0].type)

    def add(self, x):
        if x[0] == None:
            y = self.gen_object([x[1]], op='unary_add')
            return y
        else:
            y = self.gen_object(x, op='add')
            return y

    def minus(self, x):
        if x[0] == None:
            y = self.gen_object([x[1]], op='unary_minus')
            return y
        else:
            y = self.gen_object(x, op='minus')
            return y

    def eq(self, x):
        y = self.gen_object(x, op='eq')
        return y

    def mul(self, x):
        y = self.gen_object(x, op='mul')
        return y

    def div(self, x):
        y = self.gen_object(x, op='div')
        return y

    def frac(self, x):
        y = self.gen_object(x, op='div')
        return y

    def ifrac(self, x):
        y = self.gen_object(x, op='ifrac')
        return y

    def sqrt(self, x):
        y = self.gen_object(x, op='sqrt')
        return y

    def sup(self, x):
        y = self.gen_object(x, op='sup')
        return y

    def abs(self, x):
        y = self.gen_object(x, op='abs')
        return y

    def grp(self, x):
        y = self.gen_object(x, op='grp')
        return y

    def animation(self, x):
        name = str(x[1])
        y = self.gen_object(x, op=name)
        return y

    def animation_replace(self, x):
        y = self.gen_object(x, op='REPLACE')
        return y


def tex2mathjs(tex):
    return Tree2MathJS().transform(lark.parse(tex))


def mathjs2json(mathjs_obj, indent=None):
    return json.dumps(mathjs_obj, indent=indent, ensure_ascii=False)


def tex2json(tex, indent=None):
    mathjs = tex2mathjs(tex)
    json = mathjs2json(mathjs, indent=indent)
    return json


if __name__ == '__main__':
    from common_axioms import common_axioms
    from dfs import dfs
    import expression

    test_expressions = [
        '-(a+b)',
        '`(a+b)`[remove]c',
        '`(-2)^{2}`[replace]{4} + 1'
    ]

    for tex in test_expressions[-1:]:
        mathjs_obj = tex2mathjs(tex)
        json_str = mathjs2json(mathjs_obj, indent=2)
        print(json_str)
