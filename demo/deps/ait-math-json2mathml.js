const { 类脑 } = require('./公用基础')
const format = require('xml-formatter')

var args = process.argv.slice(2)

let input_json = args[0]

//let input_obj = {
//  "mathjs": "ParenthesisNode",
//  "content": {
//    "mathjs": "OperatorNode",
//    "op": "*",
//    "fn": "multiply",
//    "implicit": false,
//    "args": [
//      {
//        "mathjs": "OperatorNode",
//        "op": "*",
//        "fn": "multiply",
//        "implicit": false,
//        "args": [
//          {
//            "mathjs": "ConstantNode",
//            "value": 0
//          },
//          {
//            "mathjs": "SymbolNode",
//            "name": "a"
//          }
//        ]
//      },
//      {
//        "mathjs": "SymbolNode",
//        "name": "b"
//      }
//    ]
//  },
//  "变化": {
//    "类型": "ani-replace-before",
//    "范围": "全",
//    "替换为": {
//      "mathjs": "ConstantNode",
//      "value": 0,
//      "变化": {
//        "类型": "ani-replace-after",
//        "范围": "单",
//        "组": "ani-pair-no-1"
//      }
//    },
//    "组": "ani-pair-no-1"
//  }
//}
//
//input_json = JSON.stringify(input_obj)

const j = JSON.parse(input_json)
const m = 类脑.反序列化(j).toMathML()

console.log(m)
//console.log(format(m))
//console.log(JSON.stringify([m]))
