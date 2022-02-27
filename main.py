import pathlib

from aiohttp.web import run_app

from app.web.app import setup_app

if __name__ == "__main__":
    config_file = pathlib.Path(__file__).resolve().parent / "config.yaml"
    run_app(setup_app(config_file))
