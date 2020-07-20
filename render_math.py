import subprocess
import expression


def output_html(output_file, display_str):
    print('render math and save to html ...')
    subprocess.run(["node", 'render-math.js', output_file, display_str])


def display_str__steps(expressions):
    """
    把表达式数组转换成渲染过的步骤（输出 html）
    """
    expressions = expressions[:]
    expressions[0] = '\\begin{align} &' + expressions[0]
    expressions[-1] += '\\end{align}'
    if '=' not in expressions[0]:
        return '\\\\=&'.join(expressions)
    else:
        return '\\\\ \\Rightarrow &'.join(expressions)


def display_str__axioms(axioms):
    expressions = [a.latex().replace('\n', '\\\\ & ') for a in axioms]
    expressions[-1] += '\\end{align} '
    display_str = '\\begin{align} & ' + '\\\\ & \\\\ & '.join(expressions)
    return display_str


def display_str__eq_array(eq_array):
    eq_array = [e.replace('=', '&=', 1) for e in eq_array]
    step_str = '\\\\'.join(eq_array)
    return '\left\{\\begin{array}{rl}' + step_str + '\end{array}\\right.\\\\'


def render_equations(expressions, output='./render-tex.html'):
    """
    渲染解题步骤
    """
    display_str = display_str__steps(expressions)
    output_html(output, display_str)


def render_axioms(axioms, output='./render-tex.html'):
    """
    把定理渲染成 LaTeX（输出 html）
    """
    display_str = display_str__axioms(axioms)
    output_html(output, display_str)


def render_steps(steps, output='./render-tex.html', show_index=False):
    display_str = '\\begin{align}'
    for i, step in enumerate(steps):
        if len(step) == 4:
            narr, _, axiom, axiom_idx = step
        else:
            narr, axiom, axiom_idx = step

        tex = expression.narr2tex(narr)
        if show_index: display_str += '' if i == 0 else ('\\text{step %d}' % i)
        display_str += '&' if i == 0 else '=&'
        display_str += tex
        if axiom_idx >= 0:
            desc = axiom.name() + f' (规则 {axiom_idx})'
            desc = ' '.join(list(desc))
            display_str += ('\\qquad \\text{%s}' % desc)
        display_str += '\\\\'

    display_str += '\\end{align}'
    output_html(output, display_str)


def render_attention(tex, tokens, alpha, axiom, output='./render-tex.html'):
    """
    输出 Attention 的可视化 HTML 展示页面
    """
    #print(tex)
    #print(tokens)
    #print(alpha)

    display_str = display_str__steps([tex])
    display_str += display_str__axioms([axiom])
    display_str = display_str.replace('\\end{align}\\begin{align}',
        '\\\\ & \\\\ & \\\\')
    output_html(output, display_str)


    css = '''
    <style>
    #frame {
        text-align: center;
        width: fit-content;
        margin-top: 15px;
    }
    .display-table {
        display: table;
        margin-top: 50px;
    }
    .display-table > div {
        display: table-row;
    }
    .display-table > div > div {
        display: table-cell;
        text-align: center;
        position: relative;
        border-right: solid 1px #c5c5c5;
        padding-top: 10px;
        width: 50px;
        height: 30px;
    }
    div.hl {
        position: absolute;
        top: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
    }
    pre {
        text-align: center;
        position: absolute;
        top: 0;
        color: white;
        font-weight: 800;
        z-index: 2;
        width: 100%;
        height: 100%;
        mix-blend-mode: hard-light;
    }
    </style>
    '''

    table = '''
    <div class="display-table">
    REPLACE_ME
    </div>
    '''

    items = ''

    from colorsys import hls_to_rgb
    import math

    # colorized probability row
    items += '\t<div>\n'
    for tok, a in zip(tokens, alpha):
        saturation = a
        r,g,b = hls_to_rgb(1, 0.5, saturation)
        r = math.floor(r * 255)
        g = math.floor(g * 255)
        b = math.floor(b * 255)
        items += f'\t\t<div><div class="hl" style="background-color:rgb({r},{g},{b});">'\
              + f'</div><pre>{tok}</pre></div>\n'
    items += '\t</div>\n'

    # probability row
    items += '\t<div>\n'
    for a in alpha:
        prob = float(a) * 100.0
        prob = round(prob, 1)
        items += f'\t\t<div>{prob}%</div>\n'
    items += '\t</div>\n'

    table = table.replace('REPLACE_ME', items)

    html = ''
    with open(output, 'r') as fh:
        html = fh.read()
        html = html.replace('<style></style>', css)
        html = html.replace('<addons/>', table)
        #print(html)

    with open(output, 'w') as fh:
        fh.write(html)


if __name__ == '__main__':
    render_equations(['1+1', '2'])
