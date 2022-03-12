import pathlib
import time

from aiohttp.web import run_app

from app.web.app import setup_app

if __name__ == "__main__":
    time.sleep(5.0)  # while init db

    config_file = pathlib.Path(__file__).resolve().parent / "config.yml"
    run_app(setup_app(config_file))
