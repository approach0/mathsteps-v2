from lark import Lark, UnexpectedInput
from lark import Transformer
from copy import deepcopy
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
                    "op": "=",
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
                    "args": [x[0], x[1]],
                    "是除法": True
                }
            elif op == 'frac':
                obj = {
                    "mathjs": "OperatorNode",
                    "op": "/",
                    "fn": "divide",
                    "implicit": False,
                    "args": [x[0], x[1]],
                    "是分数": True
                }
            elif op == 'ifrac':
                obj = {
                    "mathjs": "ParenthesisNode",
                    "content": {
                        "mathjs": "OperatorNode",
                        "op": "+",
                        "fn": "add",
                        "args": [
                        x[0],
                        {
                            "mathjs": "ParenthesisNode",
                            "content": {
                            "mathjs": "OperatorNode",
                            "op": "/",
                            "fn": "divide",
                            "args": [x[1], x[2]],
                            "implicit": False
                            },
                            "是分数": True
                        }
                        ],
                        "implicit": False
                    },
                    "是分数": True
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
            ###
            # 动画节点
            ###
            elif op == 'ani-add':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-add',
                    '范围': '全'
                }
            elif op == 'ani-remove':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-remove',
                    '范围': '全'
                }
            elif op == 'ani-removeOnly':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-remove',
                    '范围': '单'
                }
            elif op == 'ani-removeDenom':
                obj = x[0]
                obj['变化'] = {
                    '类型': 'ani-remove-denominator',
                    '范围': '全'
                }
            elif op == 'ani-moveBefore':
                obj = x[0]
                grp = x[2]
                obj['变化'] = {
                    '类型': 'ani-move-before',
                    '范围': '全',
                    '组': f'ani-pair-no-{grp}'
                }
            elif op == 'ani-moveAfter':
                obj = x[0]
                grp = x[2]
                obj['变化'] = {
                    '类型': 'ani-move-after',
                    '范围': '全',
                    '组': f'ani-pair-no-{grp}'
                }
            elif op == 'ani-REPLACE':
                obj = x[0]
                subst = x[1]
                grp = 1
                obj['变化'] = {
                    '类型': 'ani-replace-before',
                    '范围': '全',
                    '替换为': subst,
                    '组': f'ani-pair-no-{grp}'
                }
                subst['变化'] = {
                    '类型': 'ani-replace-after',
                    '范围': '全',
                    '组': f'ani-pair-no-{grp}'
                }
            else:
                raise Exception('unexpected op: ' + op)


        return obj

    @staticmethod
    def son_after_animation(x, rank, assign=None):
        obj = x[rank]
        if '变化' in obj:
            ani_type = obj['变化']['类型']
            if ani_type == 'ani-replace-before':
                if assign: obj['变化']['替换为'] = assign
                return obj['变化']['替换为']
            else:
                if assign: x[rank] = assign
                return x[rank]
        return {}

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
            after_ani = self.son_after_animation(x, 1)
            if 'fn' in after_ani and after_ani['fn'] == 'unaryMinus':
                # fix cases like a + `-b`[add]
                unwrap = after_ani['args'][0]
                unwrap['变化'] = after_ani['变化']
                self.son_after_animation(x, 1, unwrap)
                y = self.gen_object(x, op='minus')
            else:
                y = self.gen_object(x, op='add')
            return y

    def minus(self, x):
        if x[0] == None:
            y = self.gen_object([x[1]], op='unary_minus')
            return y
        else:
            after_ani = self.son_after_animation(x, 1)
            if 'fn' in after_ani and after_ani['fn'] == 'unaryMinus':
                # fix cases like a + `-b`[add]
                unwrap = after_ani['args'][0]
                unwrap['变化'] = after_ani['变化']
                self.son_after_animation(x, 1, unwrap)
                y = self.gen_object(x, op='add')
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
        y = self.gen_object(x, op='frac')
        return y

    def ifrac(self, x):
        num = float(x[0])
        num_mathjs = self.number([x[0]])
        if not num.is_integer():
            return self.mul([num_mathjs, self.frac([x[1], x[2]])])
        else:
            y = self.gen_object([num_mathjs, x[1], x[2]], op='ifrac')
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
        name = 'ani-' + str(x[1])
        y = self.gen_object(x, op=name)
        return y

    def animation_group(self, x):
        name = 'ani-' + str(x[1])
        y = self.gen_object(x, op=name)
        return y

    def animation_replace(self, x):
        y = self.gen_object(x, op='ani-REPLACE')
        return y


def tex2mathjs(tex):
    return Tree2MathJS().transform(lark.parse(tex))


def mathjs2json(mathjs_obj, indent=None):
    return json.dumps(mathjs_obj, indent=indent, ensure_ascii=False)


def tex2json(tex, indent=None):
    mathjs_obj = tex2mathjs(tex)
    mathjs_fixhole(mathjs_obj)
    json = mathjs2json(mathjs_obj, indent=indent)
    return json


def mathjs_fixhole(obj, father_obj=None, rank=0):
    Type = obj['mathjs']

    if Type == 'SymbolNode':
        children = []
    elif Type == 'ConstantNode':
        children = []
    elif Type == 'ParenthesisNode':
        children = [obj['content']]
    else:
        children = [_ for _ in obj['args']]

    if '变化' in obj:
        # firstly, limit specified range for single leaf
        if len(children) == 0:
            obj['变化']['范围'] = '单'

        # secondly, add binary animation range tag if one child is animated
        ani_type = obj['变化']['类型']
        if obj['变化']['范围'] == '单' and ani_type == 'ani-remove' and len(children) > 0:
            # @chenhaojun enforces this case: 非叶子节点，“消去单，父不需要标”
            pass
        elif ani_type not in ['ani-replace-before', 'ani-replace-after', 'ani-remove-denominator']:
            father_obj['变化'] = deepcopy(obj['变化']) # copy meta-data
            father_obj['变化']['范围'] = '左' if rank == 0 else '右'

        # then, fix ``replace node''
        if '替换为' in obj['变化']:
            mathjs_fixhole(obj['变化']['替换为'])

    for i, child in enumerate(children):
        mathjs_fixhole(child, father_obj=obj, rank=i)


def mathjs_prettyprint(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    from common_axioms import common_axioms
    from dfs import dfs
    import expression

    test_expressions = [
        '-(a+b)',
        '`(-2)^{2}`[replace]{4} + 1',
        '`(a+b)`[remove]c',
        'a -`2`[moveAfter,3] = `2`[moveBefore,3] + `0`[add]',
        '\\frac{b}{a}',
        '`0ab`[replace]{0}',
        '\\frac{w`z`[moveAfter,1]}{x`y`[moveAfter,2]}',
        '`\\frac{1}{2} \div \\frac{3}{4}`[replace]{\\frac{1 \\times 4}{2 \\times 3}}',
        '`3`[remove] \\times \\frac{2}{`3`[removeDenom]}',
        '12 - `z`[add] = `z`[replace]{0}',
        'a + `-3`[add]',
        'a - `-4`[add]',
        '`0`[remove] - 7 + 10 - 3',
    ]

    for tex in test_expressions[-1:]:
        mathjs_obj = tex2mathjs(tex)
        #mathjs_prettyprint(mathjs_obj)
        mathjs_fixhole(mathjs_obj)
        #mathjs_prettyprint(mathjs_obj)

        json_str = mathjs2json(mathjs_obj, indent=2)
        print(json_str)
