import json
import pathlib

import requests
import yaml

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.yml"
QUESTIONS_FILE = BASE_DIR / "data/questions.json"


def add_quiz_questions_via_net():
    host = "http://127.0.0.1:8080"

    with open(CONFIG_FILE) as f:
        raw_yaml = yaml.safe_load(f)
        admin_config = raw_yaml["admin"]
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    session = requests.session()
    response = session.post(f"{host}/admin.login", data=admin_config)
    response.raise_for_status()
    print(response.json())

    for theme_title, questions_list in data.items():
        response = session.post(
            f"{host}/quiz.add_theme",
            data=dict(title=theme_title),
        )
        response.raise_for_status()
        print(response.json())
        theme_id = response.json()["data"]["id"]

        for question in questions_list:
            response = session.post(
                f"{host}/quiz.add_question",
                json=dict(theme_id=theme_id,
                          title=question["title"],
                          answers=question["answers"]),
                headers={"Content-Type": "application/json"},
            )
            if response.json().get("status") == "conflict":
                continue
            response.raise_for_status()


if __name__ == "__main__":
    add_quiz_questions_via_net()
