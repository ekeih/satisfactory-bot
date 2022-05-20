import logging

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

import satisfactory.game
import satisfactory.git


class Bot:
    updater = None
    github_client = None
    chat_id = None

    def __init__(self, bot_token: str, chat_id: int, github_client: satisfactory.git.Git):
        self.chat_id = chat_id
        self.updater = Updater(token=bot_token, use_context=True)
        self.github_client = github_client
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", self.start_handler))
        dispatcher.add_handler(CommandHandler("check", self.check_for_updates))

    def start(self) -> None:
        self.updater.job_queue.run_repeating(self.reconcile_timer, interval=60 * 10, first=1)
        self.updater.start_polling()
        self.updater.idle()

    def reconcile(self) -> None:
        experimental_version = satisfactory.game.get_experimental_version()
        git_tags = self.github_client.get_tags()
        experimental_tag = [tag for tag in git_tags if tag.name == experimental_version]
        if experimental_tag:
            logging.info("Git Tag %s already exists, doing nothing", experimental_version)
        else:
            logging.info("Tagging new version: %s", experimental_version)
            self.github_client.create_tag(experimental_version)

    def reconcile_timer(self, _: CallbackContext):
        logging.info("Check for new versions")
        self.reconcile()

    def start_handler(self, update: Update, context: CallbackContext):
        logging.info("/start called for chat %s" % (update.effective_chat.id))
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Breaking news from Earth: widespread chaos and mayhem. World president urges all citizens to do their part and harvest alien artifacts."
        )

    def check_for_updates(self, update: Update, context: CallbackContext):
        self.reconcile()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Let me check...")
