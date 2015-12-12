import datetime
from github import Github


class GithubProvider:

    def __init__(self, github_token):
        print(github_token)
        self.github = Github(github_token)

    def run(self, dt):
        repos = self.github.get_user().get_repos()
        repos_count = 0
        commits_count = 0
        additions = 0
        deletions = 0

        since = datetime.datetime(dt.year, dt.month, dt.day)
        until = since + datetime.timedelta(days=1)

        for repo in repos:
            repos_count += 1
            commits = repo.get_commits(since=since, until=until)
            for commit in commits:
                commits_count += 1
                stats = commit.stats
                additions += stats.additions
                deletions += stats.deletions

        return {
            'repos_count': repos_count,
            'commits_count': commits_count,
            'additions': additions,
            'deletions': deletions,
        }
