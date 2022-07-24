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

# List of loading screen tips
# https://www.reddit.com/r/SatisfactoryGame/comments/dns87g/does_anyone_know_where_i_can_find_a_full_list_of/
# https://docs.google.com/spreadsheets/d/1Wohw5iTpt07OLRXgAOanIeIpr5Y-75nieJ1b4KiLYrE/edit#gid=0

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
    "FICSIT TIP NO. 1: Don't die.",
    "FICSIT TIP NO. 2: Back to work, and Stay Effective.",
    "FICSIT TIP NO. 3: Are you feeling stuck? Are you lost? Is the entire world against you? Inform ADA so we can replace your brain's reward center!",
    "FICSIT TIP NO. 4: Bored of the standard orange and grey factories? Try out our FICSIT-approved color gun! ... Oh wait, it's not even in the game anymore.",
    "FICSIT TIP NO. 5: Getting killed a lot? Try bringing a weapon next time, or medkits, or, you know, stop doing whatever you're doing.",
    "FICSIT TIP NO. 6: Be nice to Steve, he's under a lot of pressure.",
    "FICSIT TIP NO. 7: We own you.",
    "FICSIT TIP NO. 8: Don't worry, be happy.",
    "FICSIT TIP NO. 9: ADA is always watching.",
    "FICSIT TIP NO. 10: Who am I to tell you what to do?",
    "FICSIT TIP NO. 11: Am I real?",
    "FICSIT TIP NO. 12: One of these is not like the others.",
    "FICSIT TIP NO. 13: Your fun is wrong.",
    "FICSIT TIP NO. 14: Life needs things to live.",
    "FICSIT TIP NO. 15: Is it Thursday yet?",
    "FICSIT TIP NO. 16: Are you real?",
    "FICSIT TIP NO. 17: [REDACTED]",
    "FICSIT TIP NO. 18: Keep an eye on that power capacity.",
    "FICSIT TIP NO. 19: Faster belts don't necessarily mean faster production.",
    "FICSIT TIP NO. 20: Whoever reads this is a poo-poo head.",
    "FICSIT TIP NO. 21: You are appreciated.",
    "FICSIT TIP NO. 22: Look behind you.",
    "FICSIT TIP NO. 23: So, uh, wanna go out sometime?",
    "FICSIT TIP NO. 24: Wait is this supposed to be useful or something?",
    "FICSIT TIP NO. 25: <3",
    "FICSIT TIP NO. 26: Level Up? Ha, Kidding. We don't even have levels.",
    "FICSIT TIP NO. 27: Can't stop wont stop!",
    "FICSIT TIP NO. 28: Now we have to load the game for you, all over again.",
    "FICSIT TIP NO. 29: If you're afraid of spiders, we got your back. Enable Arachnophobia mode in the options menu. Get it? Arach-NO-phobia?",
    "FICSIT TIP NO. 30: Sometimes all you need is a potato.",
    "FICSIT TIP NO. 31: I had a lot of fun writing these.",
    "FICSIT TIP NO. 32: BRB",
    "FICSIT TIP NO. 33: Congratulations! You made it to the loading screen.",
    "FICSIT TIP NO. 34: Dear diary,",
    "FICSIT TIP NO. 35: Happy Birthday",
    "FICSIT TIP NO. 36: I'd love to stay and chat, but...",
    "FICSIT TIP NO. 37: The key is a lie.",
    "FICSIT TIP NO. 38: GG EZ",
    "FICSIT TIP NO. 39: Catch phrase!",
    "FICSIT TIP NO. 40: Rude",
    "FICSIT TIP NO. 41: Come here often?",
    "FICSIT TIP NO. 42: Hello? Anyone there?",
    "FICSIT TIP NO. 43: Life + Universe + Everything",
    "FICSIT TIP NO. 44: Abort.",
    "FICSIT TIP NO. 45: Hey, nice to see you again.",
    "FICSIT TIP NO. 46: *insert lore here*",
    "FICSIT TIP NO. 47: Hope you brought a towel.",
    "FICSIT TIP NO. 48: This is my favourite tip in the game."
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
