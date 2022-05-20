from typing import Dict

import vdf
from steam.client import SteamClient
from steam.core.msg import MsgProto
from steam.enums.emsg import EMsg
from steam.utils.proto import proto_to_dict

APPID = 1690800  # Steam ID of Satisfactory


def get_versions() -> Dict:
    result = {}
    client = SteamClient()
    client.anonymous_login()
    resp = proto_to_dict(client.send_job_and_wait(MsgProto(EMsg.ClientPICSProductInfoRequest), {"apps": [{"appid": APPID}]}, timeout=10))
    appinfo = vdf.loads(resp["apps"][0].pop("buffer")[:-1].decode("utf-8", "replace"))["appinfo"]

    for branch, value in appinfo["depots"]["branches"].items():
        if not value.get("pwdrequired"):
            result[branch] = value

    return result


def get_experimental_version() -> str:
    return get_versions()["experimental"]["buildid"]


def get_early_access_version() -> str:
    return get_versions()["public"]["buildid"]
