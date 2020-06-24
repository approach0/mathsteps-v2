def test_case_from_log(path):
    """
    从外部读入随机表达式测试用例 (newline 分割的 log 格式)
    """
    arr = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip()
            arr.append(line)
    return arr


def test_cases_x3_rational():
    """
    extracted from:
    https://gitlab.dm-ai.cn/research-algorithm/Task-planner-group/X3-support/X3-solve-rational-problem/blob/b59222ae7e27b1371de646679be082be29469d5f/retriever.py
    """
    questions = []
    answers = []

    questions.append(
        "-3\\frac{1}{2}+\left|-3+(-2)\\times3^{3}\\right|"
    )
    answers.append([
        '\\frac{111}{2}'
    ])

    questions.append(
        "(-32\\frac{1}{4})-(5\\frac{1}{4}-(+3\\frac{1}{7})+(-5\\frac{1}{4})+(-2\\frac{6}{7}))"
    )
    answers.append([
        '\\frac{-41}{7}', '\\frac{41}{-7}'
    ])

    questions.append(
        "(-3\\frac{1}{3})\div2\\frac{1}{3}\\times\\frac{7}{10}"
    )
    answers.append([
        '\\frac{-15}{7}', '\\frac{15}{-7}', '-\\frac{15}{7}'
    ])

    questions.append(
        "(-3)^{2}-1\\frac{1}{2}\\times\\frac{2}{9}-6\div(-\\frac{2}{3})^{2}-(-2)^{2}"
    )
    answers.append([
        '\\frac{-155}{18}', '\\frac{155}{-18}'
    ])

    questions.append(
        "(-3)^{2}-(1\\frac{1}{2})^{3}\\times\\frac{2}{9}-6\div\left|-\\frac{2}{3}\\right|"
    )
    answers.append([
        '-\\frac{1}{36}', '\\frac{-1}{36}', '\\frac{1}{-36}'
    ])

    questions.append(
        "(+5\\frac{2}{3})+(-2\\frac{1}{2})"
    )
    answers.append([
        '\\frac{7}{3}'
    ])

    questions.append(
        "(-2\\frac{1}{3})+(-\\frac{2}{3})"
    )
    answers.append([
        '\\frac{-4}{3}', '\\frac{4}{-3}', '-\\frac{4}{3}'
    ])

    questions.append(
        "(-1\\frac{1}{4})+0.25"
    )
    answers.append([
        '0'
    ])

    questions.append(
        "\\frac{2}{3}+(-\\frac{1}{2})"
    )
    answers.append([
        '\\frac{1}{6}'
    ])

    questions.append(
        "(-3.2)+(-3.2)"
    )
    answers.append([
        '-6.4'
    ])

    questions.append(
        "(-\\frac{1}{2})\div(-\\frac{1}{3})"
    )
    answers.append([
        '\\frac{3}{2}'
    ])

    questions.append(
        "(-48)\div8-(-25)\\times(-6)"
    )
    answers.append([
        '-156'
    ])

    questions.append(
        "-2-2\div\\frac{1}{3}\\times3+12"
    )
    answers.append([
        '8'
    ])

    questions.append(
        "(-18)\div2\\frac{1}{4}\\times(1-\\frac{3}{4})"
    )
    answers.append([
        '-144'
    ])

    questions.append(
        "(\\frac{2}{9}-\\frac{1}{4}+\\frac{1}{18})\div(-\\frac{1}{36})"
    )
    answers.append([
        '-1'
    ])

    questions.append(
        "(-1)^{10}\\times2^{2}+(-4)^{2}\div(-2)"
    )
    answers.append([
        '-4'
    ])

    questions.append(
        "-1^{6}-\\frac{1}{3}\\times[-2^{2}-9\div(-3)]"
    )
    answers.append([
        '\\frac{-2}{3}', '\\frac{2}{-3}'
    ])

    questions.append(
        "\left|-10^{2}\\right|+[(-4)^{2}-(3+3^{2})\\times2]"
    )
    answers.append([
        '92'
    ])

    questions.append(
        "-1^{4}-(1-0.5)\div\\frac{1}{3}\\times[2-(-2)^{2}]"
    )
    answers.append([
        '-0.25'
    ])

    questions.append(
        "3+5\\times6-6\div3"
    )
    answers.append([
        '31'
    ])

    questions.append(
        "2+3-(4+5)"
    )
    answers.append([
        '-4'
    ])

    questions.append(
        "\left|2+3\\right|^{2}"
    )
    answers.append([
        '25'
    ])

    questions.append(
        "(2+3)^{2}"
    )
    answers.append([
        '25'
    ])

    questions.append(
        "\\frac{1}{5}\\times6\\times5"
    )
    answers.append([
        '6'
    ])

    questions.append(
        "0.3+0.5+0.7"
    )
    answers.append([
        '1.5'
    ])

    questions.append(
        "1"
    )
    answers.append([
        '1'
    ])

    questions.append(
        "[1+(2+3)^{2}]^{2}"
    )
    answers.append([
        '676'
    ])

    questions.append(
        "-1.5+\\frac{7}{4}"
    )
    answers.append([
        '0.25', '\\frac{1}{4}'
    ])

    questions.append(
        "2\\times(1-2+3\\times4\\div5)"
    )
    answers.append([
        '\\frac{14}{5}'
    ])

    questions.append(
        "1+2-3\\times4\div5-6+7+8\\times9\div10\div11"
    )
    answers.append([
        '\\frac{124}{55}'
    ])

    questions.append(
        "\left|-5+\left|2-3\\right|\\right|"
    )
    answers.append([
        '4'
    ])

    questions.append(
        "-2^{4}"
    )
    answers.append([
        '-16'
    ])

    questions.append(
        "-(1+2)\\times(1+2)"
    )
    answers.append([
        '-9'
    ])

    questions.append(
        "5.5\\times\\frac{1}{5}+(-1.1)"
    )
    answers.append([
        '0'
    ])

    questions.append(
        "1-2+3-4-4+2-1+4-3"
    )
    answers.append([
        '-4'
    ])

    questions.append(
        "0.3+0.5+0.7"
    )
    answers.append([
        '1.5'
    ])

    questions.append(
        "\\frac{3}{4}+3.3+0.25+0.7"
    )
    answers.append([
        '5'
    ])

    questions.append(
        "\\frac{1}{4}-\\frac{2}{3}+\\frac{3}{4}-\\frac{1}{3}"
    )
    answers.append([
        '0'
    ])

    questions.append(
        "\\frac{1}{5}-\\frac{2}{3}+\\frac{3}{4}-\\frac{7}{10}"
    )
    answers.append([
        '\\frac{-5}{12}', '\\frac{5}{-12}'
    ])

    questions.append(
        "1+\\frac{1}{5}-\\frac{3}{2}-7+\\frac{8}{10}+\\frac{1}{2}"
    )
    answers.append([
        '-6'
    ])

    questions.append(
        "1\\frac{0.5}{0.75}"
    )
    answers.append([
        '0.667'
    ])

    questions.append(
        "\\frac{1}{2}\\times\\frac{3}{4}\\times\\frac{2}{3}"
    )
    answers.append([
        '\\frac{1}{4}'
    ])

    questions.append(
        "0.25\\times\\frac{1}{8}\\times4"
    )
    answers.append([
        '\\frac{1}{8}', '0.124'
    ])

    questions.append(
        "\\frac{1}{4}\\times\\frac{1}{3}\div\\frac{3}{4}"
    )
    answers.append([
        '\\frac{1}{9}'
    ])

    questions.append(
        "1-3\\frac{4}{5}+\\frac{1}{8}-\\frac{1}{3}-(2-\\frac{6}{20})\\times2-2"
    )
    answers.append([
        '\\frac{-841}{120}', '\\frac{841}{-120}'
    ])

    questions.append(
        "\left|-2-\\frac{1}{3}\\right|+\\frac{1}{2}"
    )
    answers.append([
        '\\frac{17}{6}'
    ])

    questions.append(
        "[(2.33-1)-3.2-1]-9.9"
    )
    answers.append([
        '-12.77'
    ])

    questions.append(
        "2\div4"
    )
    answers.append([
        '\\frac{1}{2}'
    ])

    questions.append(
        "4\div2"
    )
    answers.append([
        '2'
    ])

    questions.append(
        "1-(\\frac{4}{5}-1.1)\\times(2+1.1)"
    )
    answers.append([
        '1.93'
    ])

    questions.append(
        "[(2.33-1)-3.2-0.2\\times33]-9.9"
    )
    answers.append([
        '-18.37'
    ])

    questions.append(
        "1-0.9"
    )
    answers.append([
        '0.1'
    ])

    questions.append(
        "\left|-21.76\\right|-7.26+(-3)"
    )
    answers.append([
        '11.5'
    ])

    questions.append(
        "2.7+(-8.5)-(+3.4)-(-1.2)"
    )
    answers.append([
        '-8'
    ])

    questions.append(
        "(-1\\frac{7}{8})\\times0"
    )
    answers.append([
        '0'
    ])

    questions.append(
        "(-3)^{3}\div2\\frac{1}{4}\\times(\\frac{2}{3})^{2}+4-2^{2}\\times\\frac{1}{3}"
    )
    answers.append([
        '\\frac{-713}{6}', '\\frac{713}{-6}'
    ])

    questions.append(
        "-(2+3)^{2}"
    )
    answers.append([
        '-25'
    ])

    questions.append(
        "-(2.2)^{2}"
    )
    answers.append([
        '-4.84'
    ])

    questions.append(
        "-(-2^{2})"
    )
    answers.append([
        '4'
    ])

    questions.append(
        "(-3)^{3}"
    )
    answers.append([
        '-27'
    ])

    questions.append(
        "\\frac{2}{4}"
    )
    answers.append([
        '\\frac{1}{2}'
    ])

    questions.append(
        "2.22\\times\\frac{0.2}{0.003}"
    )
    answers.append([
        '148.001'
    ])

    questions.append(
        "1+1-[-1-(-1)+(2-1)]"
    )
    answers.append([
        '1'
    ])

    questions.append(
        "2.76-10.26"
    )
    answers.append([
        '-7.5'
    ])

    questions.append(
        "3^{4}+(2^{2})^{3}"
    )
    answers.append([
        '145'
    ])

    questions.append(
        "\left|-5+\left|2-3\\right|\\right|"
    )
    answers.append([
        '4'
    ])

    questions.append(
        "\\frac{1}{8}+\\frac{1}{3}-0.25\\times0.125\\times2^{2}"
    )
    answers.append([
        '0.333', '\\frac{1}{3}', '0.334'
    ])

    questions.append(
        "\\frac{1}{8}+\\frac{1}{3}-0.25\div8\\times2^{2}"
    )
    answers.append([
        '0.45'
    ])

    questions.append(
        "2+2-2+2-2+2-2+2"
    )
    answers.append([
        '4'
    ])

    questions.append(
        "\left|-6\\right|"
    )
    answers.append([
        '6'
    ])

    questions.append(
        "36.54+22-82+63.46"
    )
    answers.append([
        '40'
    ])

    questions.append(
        "5+(-4)+6+4+3+(-3)+(-2)"
    )
    answers.append([
        '9'
    ])

    questions.append(
        "21\\frac{2}{3}+(+3\\frac{1}{4})-(-\\frac{2}{3})-(+\\frac{1}{4})"
    )
    answers.append([
        '\\frac{91}{6}'
    ])

    questions.append(
        "\\frac{1}{3}+\\frac{1}{6}+\\frac{1}{3}"
    )
    answers.append([
        '\\frac{5}{6}'
    ])

    questions.append(
        "\\frac{1}{3}+\\frac{3}{4}-\\frac{1}{4}"
    )
    answers.append([
        '\\frac{5}{6}'
    ])

    questions.append(
        "\\frac{1}{3}\\times\\frac{3}{4}\\times\\frac{4}{5}"
    )
    answers.append([
        '\\frac{1}{5}'
    ])

    questions.append(
        "\\frac{1}{3}\\div\\frac{4}{3}\\div\\frac{5}{4}"
    )
    answers.append([
        '\\frac{1}{5}'
    ])

    questions.append(
        "-2+3+1+(-3)+2+(-4)"
    )
    answers.append([
        '-3'
    ])

    questions.append(
        "(-12.5)\\times(+31)\\times(-\\frac{4}{5})\\times(0.1)"
    )
    answers.append([
        '31'
    ])

    questions.append(
        "42\\times(-\\frac{2}{3})+(-\\frac{3}{4})\\div(-0.25)"
    )
    answers.append([
        '-25'
    ])

    questions.append(
        "2-3-4+5+6-7-8+9"
    )
    answers.append([
        '0'
    ])

    questions.append(
        "1+2+3+4+5+6+7+8+9"
    )
    answers.append([
        '45'
    ])

    questions.append(
        "0.25\\times0.125\\times2^{2}"
    )
    answers.append([
        '0.125'
    ])

    questions.append(
        "\\frac{1}{8}-\\frac{1}{3}-\\frac{1}{16}"
    )
    answers.append([
        '\\frac{-13}{48}', '\\frac{13}{-48}'
    ])

    questions.append(
        "1+2-2"
    )
    answers.append([
        '1'
    ])

    questions.append(
        '3+2+8+7'
    )
    answers.append([
        '20'
    ])

    questions.append(
        "-5\\frac{5}{24}-2\\frac{5}{9}-(10\\frac{11}{18}+12\\frac{5}{6})"
    )
    answers.append([
        '\\frac{-1315}{72}', '\\frac{1315}{-72}'
    ])

    return questions, answers


def test_cases_wiki131278697():
    """
    测试用例（从 https://wiki.dm-ai.cn/pages/viewpage.action?pageId=131278697 上找的）
    """
    questions = []
    answers = []

    questions.append(
        "12 - (-18) + (-7) - 20"
    )
    answers.append([])

    questions.append(
        "4.7 - (-8.9) - 7.5 + (-6)"
    )
    answers.append([])

    questions.append(
        "0 - \\frac{1}{2} + \\frac{3}{4} + (-\\frac{5}{6}) + \\frac{2}{3}"
    )
    answers.append([])

    questions.append(
        "6 \cdot (-2) + 27 \div (-9)"
    )
    answers.append([])

    questions.append(
        "\left| -(5+\\frac{1}{2})\\right| (\\frac{1}{3} - \\frac{1}{2}) \\frac{3}{11} \\div (1 - \\frac{1}{4})"
    )
    answers.append([])

    questions.append(
        "(-2)^{3} \\times (\\frac{1}{2} - \\frac{3}{8}) - \\left| -2 \\right|"
    )
    answers.append([])

    questions.append(
        "-\\frac{2}{5} [-2^{2} \cdot (- \\frac{3}{2})^{3} - 6]"
    )
    answers.append([])

    questions.append(
        "(\\frac{5}{6} + \\frac{3}{8}) \\times 24"
    )
    answers.append([])

    questions.append(
        "(\\frac{1}{8} + \\frac{2}{3} - \\frac{3}{4}) 24"
    )
    answers.append([])

    questions.append(
        "(-\\frac{1}{2} + \\frac{2}{3} - \\frac{1}{4}) \\left| -24 \\right|"
    )
    answers.append([])

    questions.append(
        "(\\frac{1}{4} - \\frac{1}{36} + \\frac{1}{9}) \div (- \\frac{1}{36})"
    )
    answers.append([])

    questions.append(
        "(-(9 + \\frac{23}{24})) \cdot 18"
    )
    answers.append([])

    questions.append(
        "25 \cdot 48 + 103 \cdot 25 - 25 \cdot 51"
    )
    answers.append([])

    questions.append(
        "-13 \\times \\frac{2}{3} - 0.34 \\frac{2}{7} + \\frac{1}{3}(-13) - \\frac{5}{7} 0.34"
    )
    answers.append([])

    questions.append(
        "- (3\\frac{4}{17}) (2\\frac{2}{15}) - (7\\frac{4}{17}) (14 \\frac{13}{15}) - 4 (-14 \\frac{13}{15})"
    )
    answers.append([])

    questions.append(
        "(-7) + 10 + (-3) + 6 + (-6)"
    )
    answers.append([])

    questions.append(
        "43 + (-77) + 27 + (-43)"
    )
    answers.append([])

    questions.append(
        "-200.9 + 28 + 0.9 + (-8)"
    )
    answers.append([])

    questions.append(
        "-78 - (-4) + 200 + (+96) + (-22)"
    )
    answers.append([])

    questions.append(
        "-(5 + 3\div4) + (2 + 3\div7) - (1 + 1\div4) + 4\div7"
    )
    answers.append([])

    questions.append(
        "(-0.1) - (-4.6) - (+8.9) + (+5.4)"
    )
    answers.append([])

    questions.append(
        "(-1.75) + (2 + 3\div4) - (3+ 4\div5) + (1 + 4 \div 5)"
    )
    answers.append([])

    questions.append(
        "(-12) 2.45 \cdot 0 \cdot 9 \cdot 100"
    )
    answers.append([])

    questions.append(
        "\\frac{2018}{3} (-15) \div \\frac{1}{4} \\times 0"
    )
    answers.append([])

    questions.append(
        "(2011 + 2012) \\cdot 0 \div 2013"
    )
    answers.append([])

    #questions.append(
    #    "3x + 3 = 2x - 1"
    #)
    #answers.append([])

    #questions.append(
    #    "2(2x + 3) + 3(2x + 3) = 15"
    #)
    #answers.append([])

    #questions.append(
    #    "\\frac{2x + 1}{3} - \\frac{5x - 1}{6} = 1"
    #)
    #answers.append([])

    #questions.append(
    #    "1 - \\frac{3}{2}x = 3x + 5 \div 2"
    #)
    #answers.append([])

    #questions.append(
    #    "\\frac{5x + 4}{3} + \\frac{x - 1}{4} = 2 - \\frac{5x - 5}{12}"
    #)
    #answers.append([])

    #questions.append(
    #    "\\frac{5y - 1}{4} - \\frac{2y + 6}{3} = 1"
    #)
    #answers.append([])

    #questions.append(
    #    "\\frac{2a - 0.3}{0.5} - \\frac{a + 0.4}{0.3} = 1"
    #)
    #answers.append([])

    #questions.append(
    #    "\\frac{0.1(2x - 4) - 1}{0.2} = \\frac{0.2(4 - 2x) - 0.1}{0.3} - 1"
    #)
    #answers.append([])

    #questions.append(
    #    "2x + 3[x - 2(x - 1) + 4] = 8"
    #)
    #answers.append([])

    #questions.append(
    #    "2 [\\frac{8}{3}x - (2x - \\frac{1}{2})] = \\frac{3}{4}x"
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        'y = 2x',
    #        '3x + 5y = 26',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        'a + 5b = 6',
    #        '3a - 6b = 4',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '5x + 2y = 9',
    #        '10x + y = 12',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '3x + 2y + 3 = 0',
    #        '\\frac{5x + y}{2} = 2x + y',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '2x - y = -2',
    #        'x + y = 5',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '2x - y = 3',
    #        '3x - y = 8',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '2x - y = 5',
    #        '7x - 3y = 20',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '2x - 3y = 4',
    #        '3x - 2y = 6',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        '\\frac{2s}{3} + \\frac{3t}{4} = \\frac{1}{2}',
    #        '\\frac{4s}{5} + \\frac{5t}{6} = \\frac{7}{15}',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        'x + 2y + z = 0',
    #        '2x -y -z = 1',
    #        '3x -y -z = 2',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    [
    #        'a - 2b + 4c = 12',
    #        '3a + 2b = 1',
    #        '4a - c = 7',
    #    ]
    #)
    #answers.append([])

    #questions.append(
    #    '(5a^{2} + 2a - 1) - 4[3 - 2(4a + a^{2})]'
    #)
    #answers.append([])

    #questions.append(
    #    '3x^{2} - [7x - (4x - 3) - 2x^{2}]'
    #)
    #answers.append([])

    #questions.append(
    #    '3(a^{2} - 2ab) - 2(-3ab + b^{2})'
    #)
    #answers.append([])

    #questions.append(
    #    '4(2x^{2} - 3x + 1) - 2(4x^{2} - 2x + 3)'
    #)
    #answers.append([])

    #questions.append(
    #    '5a^{2}b - [2ab^{2} - 2(ab - \\frac{5}{2} a^{2} b) + ab] + 5ab^{2}' # not being able to handle now!
    #)
    #answers.append([])

    #questions.append(
    #    '2 \cdot (a - c) \cdot b'
    #)
    #answers.append([])

    return questions, answers
