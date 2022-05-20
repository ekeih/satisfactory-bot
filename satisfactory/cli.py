from gevent import monkey

# Necessary to make the steam api client work in a different thread.
monkey.patch_all()

import logging

import click

import satisfactory.chat
import satisfactory.git

logging.basicConfig(level=logging.INFO)
CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "auto_envvar_prefix": "SATISFACTORY_BOT",
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("-b", "--bot-token", "bot_token", required=True, default=None, type=str, help="Telegram Bot Token")
@click.option("-g", "--github-token", "github_token", required=True, default=None, type=str, help="GitHub token to access GitHub")
@click.option("-c", "--chat-id", "chat_id", required=True, default=None, type=int, help="Chat ID to send messages to")
@click.option("-r", "--repository", "repository", required=True, default="ekeih/satisfactory-bot", type=str, help="GitHub repository")
def cli(bot_token: str, github_token: str, chat_id: int, repository: str) -> None:
    github_client = satisfactory.git.Git(github_token, repository)
    bot = satisfactory.chat.Bot(bot_token=bot_token, chat_id=chat_id, github_client=github_client)
    bot.start()


if __name__ == "__main__":
    cli()
