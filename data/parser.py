import json
import pathlib

import requests
from bs4 import BeautifulSoup

URL = "https://psycatgames.com/ru/magazine/party-games/trivia-questions/"
FILE_NAME = pathlib.Path(__file__).resolve().parent / "questions.json"


def parse_quiz_site():
    """
    Сайт имеет нестандартную структуру, почти нет вложенных полей.
    """
    response = requests.get(URL)
    response.encoding = "utf-8"  # default is "ISO-8859-1"

    soup = BeautifulSoup(response.text, "html.parser")
    data = {}

    start_from = soup.select("h2[id]")[1]  # до этого - хлам
    for theme in start_from.find_next_siblings("h2"):
        theme_title = theme.text
        theme_title = theme_title[:theme_title.index("вопросы для Викторины")].strip()

        data[theme_title] = []
        row = theme.next_sibling
        while row and "<h2 id" not in row.__repr__():
            if "<h3 id" in row.__repr__():
                question_title = row.text
                question_title = question_title[question_title.index(".") + 1:].strip()
            elif "<ul" in row.__repr__():
                answers = [i.text.strip() for i in row.select("ul > li")]
            elif "trivia-answer" in row.__repr__():
                correct_answer = row.select_one("h4[id]").text.strip()
                answer_description = row.select_one("p").text.strip()

                if correct_answer in answers:  # бывает, что правильный ответ не совпадает с вариантами ответов
                    question_answers = []
                    for answer in answers:
                        answer = answer.split("\n")[0].strip()  # удаляем возможный хлам
                        if answer == correct_answer:
                            question_answers.append(dict(title=answer, is_correct=True, description=answer_description))
                        else:
                            question_answers.append(dict(title=answer, is_correct=False))
                    data[theme_title].append(dict(title=question_title,
                                                  answers=question_answers))

                del question_title, answers  # чтобы убедиться, что нет ошибок

            row = row.next_sibling

    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
