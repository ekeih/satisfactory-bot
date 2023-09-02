import logging
import random

from prometheus_client import Summary
from telegram import Update, constants
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, ApplicationBuilder, Application
from telegram.ext.filters import Chat

import satisfactory.game
import satisfactory.git
import satisfactory.youtube


class Bot:
    _app: Application
    github_client: satisfactory.git.Git or None = None
    youtube_client: satisfactory.youtube.Youtube or None = None
    chat_id = None

    def __init__(self, bot_token: str, chat_id: int, github_client: satisfactory.git.Git or None,
                 youtube_client: satisfactory.youtube.Youtube or None):
        self.chat_id = chat_id
        self.github_client = github_client
        self.youtube_client = youtube_client

        self._app = ApplicationBuilder().token(bot_token).build()

        self._app.add_handler(CommandHandler("start", self.start_handler, Chat(self.chat_id)))
        self._app.add_handler(CommandHandler("quote", self.quote_handler, Chat(self.chat_id)))
        if self.github_client is not None:
            self._app.add_handler(CommandHandler("images", self.check_images_handler, Chat(self.chat_id)))
        self._app.add_handler(CommandHandler("news", self.check_news_handler, Chat(self.chat_id)))

    def start(self) -> None:
        if self.github_client is not None:
            self._app.job_queue.run_repeating(self.check_images_timer, interval=60 * 10, first=5)
        self._app.job_queue.run_repeating(self.check_news_timer, interval=60 * 60, first=30)
        if self.youtube_client is not None:
            self._app.job_queue.run_repeating(self.check_videos, interval=60 * 60, first=15)
        self._app.job_queue.run_once(self.send_random_quote_timer, random.randrange(60 * 60 * 24, 60 * 60 * 24 * 7, 1))
        self._app.run_polling()

    @Summary("satisfactory_bot_start_handler", "Time spent running start_handler").time()
    async def start_handler(self, update: Update, context: CallbackContext):
        logging.info("/start called for chat %s", update.effective_chat.id)
        await self.send_random_quote(context)

    @Summary("satisfactory_bot_quote_handler", "Time spent running quote_handler").time()
    async def quote_handler(self, update: Update, context: CallbackContext):
        logging.info("/quote called for chat %s", update.effective_chat.id)
        await self.send_random_quote(context)

    @Summary("satisfactory_bot_check_images_handler", "Time spent running check_images_handler").time()
    async def check_images_handler(self, update: Update, context: CallbackContext):
        logging.info("/images called for chat %s", update.effective_chat.id)
        await self.check_images(context)

    @Summary("satisfactory_bot_check_news_handler", "Time spent running check_news_handler").time()
    async def check_news_handler(self, update: Update, context: CallbackContext):
        logging.info("/news called for chat %s", update.effective_chat.id)
        await self.check_news(context)

    @Summary("satisfactory_bot_check_images_timer", "Time spent running check_images_timer").time()
    async def check_images_timer(self, context: CallbackContext):
        await self.check_images(context)

    @Summary("satisfactory_bot_check_news_timer", "Time spent running the check_news_timer").time()
    async def check_news_timer(self, context: CallbackContext):
        await self.check_news(context)

    @Summary("satisfactory_bot_check_videos_timer", "Time spent running the check_videos_timer").time()
    async def check_videos_timer(self, context: CallbackContext):
        await self.check_videos(context)

    @Summary("satisfactory_bot_send_random_quote_timer", "Time spent running the send_random_quote_timer").time()
    async def send_random_quote_timer(self, context: CallbackContext):
        await self.send_random_quote(context)
        (self._app.job_queue.run_once(self.send_random_quote_timer,
                                      random.randrange(60 * 60 * 24, 60 * 60 * 24 * 7, 1)))

    @Summary("satisfactory_bot_check_images", "Time spent running check_images").time()
    async def check_images(self, context: CallbackContext) -> None:
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
                await context.bot.send_message(chat_id=self.chat_id, text="Tagged new release <code>%s</code>\n\n%s" % (
                version_tag, satisfactory.game.get_random_quote()), parse_mode=ParseMode.HTML)
        if new_versions_count == 0 and not context.job:
            # A user triggered the check manually, inform them that there was no new version found.
            await context.bot.send_message(chat_id=self.chat_id,
                                           text="No newer versions available, doing nothing.\n\n%s" % (
                                               satisfactory.game.get_random_quote()), parse_mode=ParseMode.HTML)

    @Summary("satisfactory_bot_check_news", "Time spent running check_news").time()
    async def check_news(self, context: CallbackContext) -> None:
        recent_news = satisfactory.game.get_patchnotes()
        for news in recent_news:
            if len(news) <= constants.MessageLimit.MAX_TEXT_LENGTH:
                await context.bot.send_message(chat_id=self.chat_id, text=news, parse_mode=ParseMode.HTML,
                                               disable_web_page_preview=True)
            else:
                parts = []
                while len(news) > 0:
                    if len(news) > constants.MessageLimit.MAX_TEXT_LENGTH:
                        part = news[: constants.MessageLimit.MAX_TEXT_LENGTH]
                        first_lnbr = part.rfind("\n")
                        if first_lnbr != -1:
                            parts.append(part[:first_lnbr])
                            news = news[first_lnbr:]
                        else:
                            parts.append(part)
                            news = news[constants.MessageLimit.MAX_TEXT_LENGTH:]
                    else:
                        parts.append(news)
                        break
                for part in parts:
                    await context.bot.send_message(chat_id=self.chat_id, text=part, parse_mode=ParseMode.HTML,
                                                   disable_web_page_preview=True)
        if len(recent_news) == 0 and not context.job:
            # A user triggered the check manually, inform them that there are no recent news available.
            await context.bot.send_message(chat_id=self.chat_id,
                                           text="No recent news found.\n\n%s" % (satisfactory.game.get_random_quote()),
                                           parse_mode=ParseMode.HTML)

    @Summary("satisfactory_bot_send_random_quote", "Time spent running send_random_quote").time()
    async def send_random_quote(self, context: CallbackContext) -> None:
        await context.bot.send_message(chat_id=self.chat_id, text=satisfactory.game.get_random_quote(),
                                       parse_mode=ParseMode.HTML)

    @Summary("satisfactory_bot_check_videos", "Time spent running check_videos").time()
    async def check_videos(self, context: CallbackContext) -> None:
        videos = self.youtube_client.get_new_videos()
        for video in videos:
            await context.bot.send_message(chat_id=self.chat_id, text=video, parse_mode=ParseMode.HTML)
