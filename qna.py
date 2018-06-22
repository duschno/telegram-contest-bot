questions = {
    1: 'The capital of Norway?',
    2: '2 + 2 = ?',
    3: 'Abbreviation of the Institute of Computational Mathematics at KFU?'
}
answers = {
    1: ['oslo'],
    2: ['4'],
    3: ['ivmiit',
        'vmk',
        'ivmiit-vmk',
        'cm&it',
        'cmait',
        'icmait']
}


def check(s):
    try:
        s = s.strip(' .,!;\n\t').lower()
        key, answer = s.split(maxsplit=1)
        key = int(key)
        if answers.get(key) is None:
            return key, None, 'Question doesn\'t exist.'
        if answer not in answers.get(key):
            return key, False, 'Answer received.'
        if answer in answers.get(key):
            return key, True, 'Answer received.'
    except Exception as e:
        print(e)
        return None, None, 'Exception :('
