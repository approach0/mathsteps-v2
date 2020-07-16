const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const 步骤预处理 = require("./步骤预处理");

const ts = "ait-tutor-board-new";
const __marshal__ = "aog-ide@^3.0.0-core@src/models/eaog-tree-node.js#EaogTreeNode";


/**
 * 用于将ait-math的输出结果转为PG.
 */
class MathResultPgConverter {

    /**
     * 将ait-math返回的结果转为PG.
     */
    async convertToPg(questionMathML, steps) {
        steps = steps.map(s => {
            return {
                变化: s.mml,
                运算: s.text
            }
        });
        const preprocessedArray = await 步骤预处理.预处理步骤(steps);

        if (steps.length === 0) {
            return this._createSandNode();
        }

        // "显示内容"节点数组
        const contentNodeList = [];
        for (let i = 0; i < Math.min(preprocessedArray.length, steps.length); i++) {
            contentNodeList.push(this._createContentNode(i + 1, preprocessedArray[i], steps[i].运算));
        }

        // 创建"初始化节点"
        return this._createExplainPgStructure({ questionMathML, contentNodeList });
    }

    /**
     * 创建智能讲解PG.
     */
    _createExplainPgStructure({ questionMathML, contentNodeList }) {
        return this._createSandNode("Root", [
            this._createSandNode("题目", [
                {
                    __marshal__,
                    ts,
                    "type": "instruction",
                    "name": "显示题目",
                    "instruction": "显示题目",
                    "children": [],
                    "关联": {},
                    "内容": `<p>${questionMathML}</p>`
                }
            ]),
            this._createSandNode("智能提示", [
                this._createSandNode("元信息", []),
                this._createSandNode("解题思路", []),
            ]),
            this._createSandNode("智能讲解", [
                this._createSandNode("计算", contentNodeList)
            ]),
        ]);
    }

    /**
     * 创建内容节点.
     */
    _createContentNode(index, 内容, 说明, { nodeName, createAnimation = true } = {}) {
        return {
            __marshal__,
            ts,
            "type": "instruction",
            "name": nodeName || `${index}-${说明}`,
            "instruction": "显示内容",
            "children": [],
            "关联": {},
            "重点": [],
            "导航": [],
            说明,
            "内容": 内容,
        };
    }

    /**
     * 创建SAnd节点.
     */
    _createSandNode(name, children = []) {
        return {
            __marshal__,
            type: "sand",
            name,
            children,
            sequence: null,
            iterator: null
        };
    }

}

module.exports = new MathResultPgConverter();