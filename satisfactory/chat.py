import logging
from datetime import datetime

from telegram import ParseMode, Update, constants
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
        dispatcher.add_handler(CommandHandler("images", self.check_images_handler))
        dispatcher.add_handler(CommandHandler("news", self.check_news_handler))

    def start(self) -> None:
        self.updater.job_queue.run_repeating(self.check_images_timer, interval=60 * 10, first=5)
        self.updater.job_queue.run_repeating(self.check_news_timer, interval=60 * 60, first=30)
        self.updater.start_polling()
        self.updater.idle()

    def start_handler(self, update: Update, context: CallbackContext):
        logging.info("/start called for chat %s", update.effective_chat.id)
        context.bot.send_message(chat_id=update.effective_chat.id, text=satisfactory.game.get_random_quote())

    def check_images_handler(self, update: Update, context: CallbackContext):
        logging.info("/images called for chat %s", update.effective_chat.id)
        self.check_images(context)

    def check_news_handler(self, update: Update, context: CallbackContext):
        logging.info("/news called for chat %s", update.effective_chat.id)
        self.check_news(context)

    def check_images_timer(self, context: CallbackContext):
        self.check_images(context)

    def check_news_timer(self, context: CallbackContext):
        self.check_news(context)

    def check_images(self, context: CallbackContext) -> None:
        versions = satisfactory.game.get_versions()
        existing_git_tags = self.github_client.get_tags()
        for version, values in versions.items():
            version_tag = "server-%s/%s-%s" % (version, values["timeupdated"].strftime("%Y.%m.%d"), values["buildid"])
            for tag in existing_git_tags:
                if tag.name == version_tag:
                    logging.info("Git tag %s for %s already exists, doing nothing", version_tag, version)
                else:
                    logging.info("Tagging new %s version: %s", version, version_tag)
                    self.github_client.create_tag(version_tag)
                    context.bot.send_message(chat_id=self.chat_id, text="Tagged new release <code>%s</code>\n\n%s" % (version_tag, satisfactory.game.get_random_quote()), parse_mode=ParseMode.HTML)

    def check_news(self, context: CallbackContext) -> None:
        for news in satisfactory.game.get_patchnotes():
            if len(news) <= constants.MAX_MESSAGE_LENGTH:
                context.bot.send_message(chat_id=self.chat_id, text=news, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                parts = []
                while len(news) > 0:
                    if len(news) > constants.MAX_MESSAGE_LENGTH:
                        part = news[: constants.MAX_MESSAGE_LENGTH]
                        first_lnbr = part.rfind("\n")
                        if first_lnbr != -1:
                            parts.append(part[:first_lnbr])
                            news = news[first_lnbr:]
                        else:
                            parts.append(part)
                            news = news[constants.MAX_MESSAGE_LENGTH :]
                    else:
                        parts.append(news)
                        break
                for part in parts:
                    context.bot.send_message(chat_id=self.chat_id, text=part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
