import logging

from prometheus_client import Summary
from telegram import ParseMode, Update, constants
from telegram.ext import CallbackContext, CommandHandler, Updater
from telegram.ext.filters import Filters

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
        dispatcher.add_handler(CommandHandler("start", self.start_handler, Filters.chat(self.chat_id)))
        dispatcher.add_handler(CommandHandler("images", self.check_images_handler, Filters.chat(self.chat_id)))
        dispatcher.add_handler(CommandHandler("news", self.check_news_handler, Filters.chat(self.chat_id)))

    def start(self) -> None:
        self.updater.job_queue.run_repeating(self.check_images_timer, interval=60 * 10, first=5)
        self.updater.job_queue.run_repeating(self.check_news_timer, interval=60 * 60, first=30)
        self.updater.start_polling()
        self.updater.idle()

    @Summary("satisfactory_bot_start_handler", "Time spent running start_handler").time()
    def start_handler(self, update: Update, context: CallbackContext):
        logging.info("/start called for chat %s", update.effective_chat.id)
        context.bot.send_message(chat_id=update.effective_chat.id, text=satisfactory.game.get_random_quote())

    @Summary("satisfactory_bot_check_images_handler", "Time spent running check_images_handler").time()
    def check_images_handler(self, update: Update, context: CallbackContext):
        logging.info("/images called for chat %s", update.effective_chat.id)
        self.check_images(context)

    @Summary("satisfactory_bot_check_news_handler", "Time spent running check_news_handler").time()
    def check_news_handler(self, update: Update, context: CallbackContext):
        logging.info("/news called for chat %s", update.effective_chat.id)
        self.check_news(context)

    @Summary("satisfactory_bot_check_images_timer", "Time spent running check_images_timer").time()
    def check_images_timer(self, context: CallbackContext):
        self.check_images(context)

    @Summary("satisfactory_bot_check_news_timer", "Time spent running the check_news_timer").time()
    def check_news_timer(self, context: CallbackContext):
        self.check_news(context)

    @Summary("satisfactory_bot_check_images", "Time spent running check_images").time()
    def check_images(self, context: CallbackContext) -> None:
        versions = satisfactory.game.get_versions()
        existing_git_tags = [tag.name for tag in self.github_client.get_tags()]
        new_versions_count = 0
        for version, values in versions.items():
            version_tag = "server-%s/%s-%s" % (version, values["timeupdated"].strftime("%Y.%m.%d"), values["buildid"])
            if version_tag in existing_git_tags:
                logging.info("Git tag %s for %s already exists, doing nothing", version_tag, version)
            else:
                logging.info("Tagging new %s version: %s", version, version_tag)
                new_versions_count += 1
                self.github_client.create_tag(version_tag)
                context.bot.send_message(chat_id=self.chat_id, text="Tagged new release <code>%s</code>\n\n%s" % (version_tag, satisfactory.game.get_random_quote()), parse_mode=ParseMode.HTML)
        if new_versions_count == 0 and not context.job:
            # A user triggered the check manually, inform them that there was no new version found.
            context.bot.send_message(chat_id=self.chat_id, text="No newer versions available, doing nothing.\n\n%s" % (satisfactory.game.get_random_quote()), parse_mode=ParseMode.HTML)

    @Summary("satisfactory_bot_check_news", "Time spent running check_news").time()
    def check_news(self, context: CallbackContext) -> None:
        recent_news = satisfactory.game.get_patchnotes()
        for news in recent_news:
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
        if len(recent_news) == 0 and not context.job:
            # A user triggered the check manually, inform them that there are no recent news available.
            context.bot.send_message(chat_id=self.chat_id, text="No recent news found.\n\n%s" % (satisfactory.game.get_random_quote()), parse_mode=ParseMode.HTML)
