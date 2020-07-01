def translate(name):
    translate_dict = {}
    translate_dict['add'] = '新增'
    translate_dict['remove'] = '消去'
    translate_dict['replaceBefore'] = '替换前'
    translate_dict['replaceAfter'] = '替换后'
    translate_dict['moveBefore'] = '移动前'
    translate_dict['moveAfter'] = '移动后'

    return translate_dict[name]
