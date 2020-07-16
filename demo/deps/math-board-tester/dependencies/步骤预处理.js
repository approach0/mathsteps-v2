const { JSDOM } = require('jsdom');

const 支持多种运算板 = [
    {
        主要类型: 'ani-add',
        其它类型: [
            'ani-remove',
        ],
    },
    {
        主要类型: 'ani-move',
        其它类型: [
            'ani-add',
            'ani-remove',
            'ani-merge',
        ],
    },
    {
        主要类型: 'ani-replace',
        其它类型: [
            'ani-add',
            'ani-remove'
        ]
    },
    {
        主要类型: 'ani-merge',
        其它类型: [
            'ani-add',
            'ani-remove'
        ],
    },
    {
        主要类型: 'ani-remove-denominator',
        其它类型: [
            'ani-add',
            'ani-remove',
            'ani-replace',
        ],
    }
];

const MML包裹元素 = 'mml-wrapper';

class 步骤预处理 {
    // 移除空的与只有一个子节点并不带属性的mrow
    移除多余mrow(doc) {
        const mathWrappers = doc.querySelectorAll('math');
        mathWrappers.forEach(mathItem => {
            if (!mathItem.hasAttribute('xmlns')) {
                mathItem.setAttribute('xmlns', 'http://www.w3.org/1998/Math/MathML');
            }

            mathItem.querySelectorAll('mrow').forEach(mrow => {
                // 带属性的和子节点数量大于1的不能移除
                if (mrow.getAttributeNames().length > 0 || mrow.childNodes.length > 1) {
                    return;
                }
                if (mrow.childNodes.length === 0) {
                    // 空节点，移除
                    mrow.remove();
                } else {
                    // 只有一个子节点，替换
                    const child = mrow.childNodes[0];
                    mrow.replaceWith(child);
                }
            });
        });
    }

    // 对表达式进行包裹，添加外部math元素
    添加动画class(doc) {
        const mathWrappers = doc.querySelectorAll('math');

        mathWrappers.forEach(mathItem => {
            let metas = [];
            const aniItems = mathItem.querySelectorAll('[class^="ani-"],[class*=" ani-"]');
            aniItems.forEach(item => {
                item.classList.forEach(c => {
                    let aniClass = ''
                    switch (c) {
                        case 'ani-add':
                            aniClass = 'ani-add';
                            break;
                        case 'ani-remove':
                            aniClass = 'ani-remove';
                            break;
                        case 'ani-replace-before':
                        case 'ani-replace-after':
                            aniClass = 'ani-replace';
                            break;
                        case 'ani-move-before':
                        case 'ani-move-after':
                            aniClass = 'ani-move';
                            break;
                        case 'ani-merge-before':
                        case 'ani-merge-after':
                            aniClass = 'ani-merge';
                            break;
                        case 'ani-remove-denominator':
                            aniClass = 'ani-remove-denominator';
                            break;
                    }
                    if (aniClass && !metas.includes(aniClass)) {
                        metas.push(aniClass);
                    }
                })
            })
            if (metas.length > 1) {
                // 当有多种动画类型混合时，判断是否有支持的运算板
                let 有支持运算板 = false;
                for (const 运算板类 of 支持多种运算板) {
                    const 支持类型 = 运算板类;
                    if (metas.includes(支持类型.主要类型)) {
                        let 支持 = true;
                        for (const c of metas) {
                            if (c != 支持类型.主要类型 && !支持类型.其它类型.includes(c)) {
                                支持 = false;
                                break;
                            }
                        }
                        if (支持) {
                            mathItem.classList.add(支持类型.主要类型);
                            有支持运算板 = true;
                            break;
                        }
                    }
                }
                if (!有支持运算板) {
                    throw new Error(`不支持此运算类型组合：${metas.join(',')}`);
                }
            }
            else if (metas.length == 1) {
                mathItem.classList.add(metas[0]);
            }
        });
    }

    // 为表达式mml添加对应的class
    async 预处理步骤(步骤集) {
        const 预处理表达式 = [];
        // 进行封装
        步骤集.forEach(步骤 => {
            // 支持不同类型的步骤
            if (typeof 步骤 === 'string') {
                try {
                    步骤 = JSON.parse(步骤);
                } catch (err) {
                    // ignore error
                }
            }
            if (!步骤.变化 && !步骤.原式 && !步骤.新式) {
                if (!步骤.运算) {
                    预处理表达式.push(步骤);
                } else {
                    预处理表达式.push(步骤.运算);
                }
            } else {
                const 变化内容 = 步骤.变化 ? 步骤.变化 : 步骤.新式;
                const 处理表达式 = (表达式) => {
                    const doc = (new JSDOM(`<div id="${MML包裹元素}">${表达式}</div>`)).window.document;
                    this.移除多余mrow(doc);
                    this.添加动画class(doc);
                    return doc.querySelector(`#${MML包裹元素}`).innerHTML;
                };
                if (Array.isArray(变化内容)) {
                    预处理表达式.push(变化内容.map(变化 => {
                        return 处理表达式(变化);
                    }).join(''));
                } else {
                    预处理表达式.push(处理表达式(变化内容));
                }
            }
        });

        return 预处理表达式;
    }
}

module.exports = new 步骤预处理();