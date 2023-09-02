import logging
from importlib import metadata

import click
from prometheus_client import Gauge, start_http_server

import satisfactory.chat
import satisfactory.git
import satisfactory.youtube

logging.basicConfig(level=logging.INFO)
CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "auto_envvar_prefix": "SATISFACTORY_BOT",
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("-b", "--bot-token", "bot_token", required=True, default=None, type=str, help="Telegram Bot Token")
@click.option("-g", "--github-token", "github_token", required=True, default=None, type=str, help="GitHub token to access GitHub")
@click.option("-y", "--youtube-token", "youtube_token", required=True, default=None, type=str, help="Google API token to access YouTube")
@click.option("-c", "--chat-id", "chat_id", required=True, default=None, type=int, help="Chat ID to send messages to")
@click.option("-r", "--repository", "repository", required=True, default="ekeih/satisfactory-bot", type=str, help="GitHub repository")
@click.option("-a", "--metrics-address", required=True, default="0.0.0.0", type=str, help="IP address to serve metrics on")
@click.option("-p", "--metrics-port", required=True, default=8000, type=int, help="Port to serve metrics on")
@click.option("-v", "--version", is_flag=True, type=bool, help="Show version and exit")
def cli(bot_token: str, github_token: str, youtube_token: str, chat_id: int, repository: str, metrics_address: str, metrics_port: int, version: bool) -> None:
    installed_version=metadata.version('satisfactory_bot')
    if version:
        print(installed_version)
    else:
        logging.info("Running version %s", installed_version)
        start_http_server(port=metrics_port, addr=metrics_address)
        Gauge("satisfactory_bot_info", "Static info of satisfactory-bot", ["version"]).labels(installed_version).set(1)

        github_client = None
        if github_token is not None:
            github_client = satisfactory.git.Git(github_token, repository)

        youtube_client = None
        if youtube_token is not None:
            youtube_client = satisfactory.youtube.Youtube(youtube_token)

        bot = satisfactory.chat.Bot(bot_token=bot_token, chat_id=chat_id, github_client=github_client, youtube_client=youtube_client)
        bot.start()


if __name__ == "__main__":
    cli()
