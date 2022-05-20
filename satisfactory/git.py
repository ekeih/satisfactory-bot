from typing import List

from github import Github, Tag


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
