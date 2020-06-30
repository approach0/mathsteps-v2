from lark import Lark, UnexpectedInput
from lark import Transformer
import rich
import json

lark = Lark.open('grammar.lark', rel_to=__file__, parser='lalr', debug=False)

class Tree2MathJS(Transformer):

    @staticmethod
    def gen_object(x, op=None):
        if isinstance(x, float):
            return {
                "mathjs": "ConstantNode",
                "value": x
            }
        elif isinstance(x, str):
            return {
                "mathjs": "SymbolNode",
                "name": x
            }
        else:
            if op == 'add':
                return {
                    "mathjs": "OperatorNode",
                    "op": "+",
                    "fn": "add",
                    "args": [x[0], x[1]]
                }
            elif op == 'unary_add':
                return {
                    "mathjs": "OperatorNode",
                    "fn": "unaryPlus",
                    "op": "+",
                    "args": [x[0]]
                }
            elif op == 'minus':
                return {
                    "mathjs": "OperatorNode",
                    "op": "-",
                    "fn": "subtract",
                    "args": [x[0], x[1]]
                }
            elif op == 'unary_minus':
                return {
                    "mathjs": "OperatorNode",
                    "fn": "unaryMinus",
                    "op": "-",
                    "args": [x[0]]
                }
            elif op == 'eq':
                return {
                    "mathjs": "OperatorNode",
                    "op": "==",
                    "fn": "equal",
                    "args": [x[0], x[1]]
                }
            elif op == 'mul':
                return {
                    "mathjs": "OperatorNode",
                    "op": "*",
                    "fn": "multiply",
                    "args": [x[0], x[1]]
                }
            elif op == 'div':
                return {
                    "mathjs": "OperatorNode",
                    "op": "/",
                    "fn": "divide",
                    "args": [x[0], x[1]]
                }
            elif op == 'sup':
                return {
                    "mathjs": "OperatorNode",
                    "op": "^",
                    "fn": "pow",
                    "args": [x[0], x[1]]
                }
            else:
                return None

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

    def sup(self, x):
        y = self.gen_object(x, op='sup')
        return y


def tex2mathjs(tex):
    return Tree2MathJS().transform(lark.parse(tex))


def mathjs2json(mathjs_obj, indent=None):
    return json.dumps(mathjs_obj, indent=indent)


if __name__ == '__main__':
    #tex = '1 + 2 + a'
    #tex = '-1+2 = x'
    #tex = '3x + 1x + 2 \\times 3'
    #tex = '1 \div 2x + \\frac{1}{x}'
    tex = 'a^{2}'

    mathjs_obj = tex2mathjs(tex)
    json_str = mathjs2json(mathjs_obj, indent=2)
    print(json_str)
