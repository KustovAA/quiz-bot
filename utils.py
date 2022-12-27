import re

import requests


def get_quiz_from_file(filepath: str):
    if filepath.startswith('http'):
        response = requests.get(filepath)
        file_contents = response.content.decode(encoding='KOI8-R')
    else:
        with open(filepath, 'r', encoding='KOI8-R') as file:
            file_contents = file.read()

    chunks = file_contents.split('\n\n')

    questions = []
    answers = []

    for chunk in chunks:
        if 'Вопрос' in chunk:
            questions.append(chunk)
        elif 'Ответ' in chunk:
            answers.append(chunk)

    quiz = dict()

    for index, question in enumerate(questions):
        key = re.sub(r'\n?Вопрос \d+:\n', '', question)
        value = re.sub(r'\n?Ответ:\n', '', answers[index])
        quiz[key] = value

    return quiz
