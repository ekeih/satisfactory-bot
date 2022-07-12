import logging
import random
import re
from datetime import datetime
from typing import Dict, List

import requests
import vdf
from prometheus_client import Counter
from steam.client import SteamClient
from steam.core.msg import MsgProto
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.utils.proto import proto_to_dict

NEWS_URL = "https://store.steampowered.com/events/ajaxgetadjacentpartnerevents/?appid=526870&count_after=10"
APPID = 1690800  # Steam ID of Satisfactory

PROM_STEAM_CONNECT = Counter("satisfactory_bot_steam_connect", "Status of Steam client connection attempts", ["status"])
PROM_STEAM_LOGIN = Counter("satisfactory_bot_steam_login", "Status of Steam client login attempts", ["status"])

QUOTES = [
    "Harvest.",
    "Comply.",
    "Harvest. It.",
    "I strongly advise you to harvest this specimen.",
    "Your contract legally compels you to harvest this artifact.",
    "You are so lucky that you found this most valuable artifact.",
    "Picking up multiple FICSIT personnel in the area, proceed with harvest before it's too late.",
    "Breaking news from Earth: widespread chaos and mayhem. World president urges all citizens to do their part and harvest alien artifacts.",
    "Relaying message: Hello this is maternal figure. I have taken ill and need your help to find a cure. Doctors say that the only remedy is alien artifacts.",
]


def get_versions() -> Dict:
    result = {}
    client = SteamClient()

    if client.connect(retry=1):
        logging.debug("Steam client connected successfully")
        PROM_STEAM_CONNECT.labels("success").inc()
    else:
        PROM_STEAM_CONNECT.labels("error").inc()
        raise Exception("Steam client was unable to connect")

    login = client.anonymous_login()
    PROM_STEAM_LOGIN.labels(login.name).inc()
    if login == EResult.OK:
        logging.debug("Steam client logged in successfully")
    else:
        raise Exception("Steam client was unable to login")

    resp = proto_to_dict(client.send_job_and_wait(MsgProto(EMsg.ClientPICSProductInfoRequest), {"apps": [{"appid": APPID}]}, timeout=10))
    appinfo = vdf.loads(resp["apps"][0].pop("buffer")[:-1].decode("utf-8", "replace"))["appinfo"]

    for branch, value in appinfo["depots"]["branches"].items():
        if not value.get("pwdrequired"):
            result[branch] = {"timeupdated": datetime.utcfromtimestamp(int(value["timeupdated"])), "buildid": value["buildid"]}

    client.logout()
    client.disconnect()

    return result


def sanitize_steam_string(text: str) -> str:

    # sanitize HTML
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # sanitize steam markup https://steamcommunity.com/comment/Guide/formattinghelp
    # replace supported tags
    text = text.replace("[*]", "-")
    text = text.replace("[b]", "<b>")
    text = text.replace("[/b]", "</b>")
    text = text.replace("[i]", "<i>")
    text = text.replace("[/i]", "</i>")
    text = text.replace("[u]", "<u>")
    text = text.replace("[/u]", "</u>")
    text = text.replace("[s]", "<strike>")
    text = text.replace("[/s]", "</strike>")
    text = text.replace("[code]", "<code>")
    text = text.replace("[/code]", "</code>")
    text = re.sub("\[url\=(.*)\](.*)\[/url\]", r'<a href="\1">\2</a>', text)
    text = re.sub("\[quote\=(.*)\](.*)\[/quote\]", r'"\2" -- \1', text)
    # remove unsupported tags
    text = re.sub("\[/?(h[0-9]|spoiler|noparse|hr|list|olist)\]", "", text)

    return text


def get_patchnotes(age: int = 60) -> List[str]:
    news = []
    response = requests.get(NEWS_URL, timeout=10)
    response.raise_for_status()
    for event in response.json()["events"]:
        if "patchnotes" in event["announcement_body"]["tags"] and not event["event_name"].startswith("Experimental"):
            event_time = datetime.fromtimestamp(event["announcement_body"]["posttime"])
            event_age = datetime.now() - event_time
            if event_age.total_seconds() / 60 < age:
                name = sanitize_steam_string(event["event_name"])
                body = sanitize_steam_string(event["announcement_body"]["body"])
                event_time = datetime.fromtimestamp(event["announcement_body"]["posttime"]).strftime("%d.%m.%Y %H:%M")
                new_news_item = "<b>%s</b> (%s)\n\n%s" % (name, event_time, body)
                news.append(new_news_item)
    return news


def get_random_quote() -> str:
    return random.choice(QUOTES)
