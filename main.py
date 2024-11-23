import logging
from datetime import UTC, datetime
from typing import Dict, List

import click
import vdf
from github import Github, Tag
from steam.client import SteamClient
from steam.core.msg import MsgProto
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.utils.proto import proto_to_dict

logging.basicConfig(level=logging.INFO)
CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "auto_envvar_prefix": "SATISFACTORY_BOT",
}
APPID = 1690800  # Steam ID of Satisfactory

class Git:
    repository = None

    def __init__(self, token: str, repository: str):
        github_client = Github(token)
        self.repository = github_client.get_repo(repository)

    def get_tags(self) -> List[Tag.Tag]:
        tags = [tag for tag in self.repository.get_tags()]
        return tags

    def create_tag(self, tag: str) -> None:
        latest_commit = self.repository.get_commits()[0].sha
        t = self.repository.create_git_tag(tag=tag, message="Released by satisfactory-bot", object=latest_commit, type="commit")
        self.repository.create_git_ref("refs/tags/%s" % (t.tag), t.sha)


def get_versions() -> Dict:
    result = {}
    client = SteamClient()

    if client.connect(retry=5):
        logging.debug("Steam client connected successfully")
    else:
        raise Exception("Steam client was unable to connect")

    login = client.anonymous_login()
    if login == EResult.OK:
        logging.debug("Steam client logged in successfully")
    else:
        raise Exception("Steam client was unable to login")

    resp = proto_to_dict(client.send_job_and_wait(MsgProto(EMsg.ClientPICSProductInfoRequest), {"apps": [{"appid": APPID}]}, timeout=10))
    appinfo = vdf.loads(resp["apps"][0].pop("buffer")[:-1].decode("utf-8", "replace"))["appinfo"]

    for branch, value in appinfo["depots"]["branches"].items():
        if not value.get("pwdrequired"):
            result[branch] = {"timeupdated": datetime.fromtimestamp(int(value["timeupdated"]), UTC), "buildid": value["buildid"]}

    client.logout()
    client.disconnect()

    return result


def check_images(github_client: Git) -> None:
    versions = get_versions()
    existing_git_tags = [tag.name for tag in github_client.get_tags()]
    for version, values in versions.items():
        version_tag = "server-%s/%s-%s" % (version, values["timeupdated"].strftime("%Y.%m.%d"), values["buildid"])
        if version_tag in existing_git_tags:
            logging.info("Git tag %s for %s already exists, doing nothing", version_tag, version)
        else:
            logging.info("Tagging new %s version: %s", version, version_tag)
            github_client.create_tag(version_tag)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("-g", "--github-token", "github_token", required=True, default=None, type=str, help="GitHub token to access GitHub")
@click.option("-r", "--repository", "repository", required=True, default="ekeih/satisfactory-bot", type=str, help="GitHub repository")
def main(github_token: str, repository: str) -> None:
    check_images(Git(github_token, repository))


if __name__ == "__main__":
    main()
