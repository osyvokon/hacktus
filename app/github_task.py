import datetime
from github import Github
from app import celery, connect_mongo


class GithubProvider:

    def __init__(self, github_token):
        self.github = Github(github_token)

    def run(self, dt):
        repos = self.github.get_user().get_repos()
        repos_count = 0
        commits_count = 0
        additions = 0
        deletions = 0
        stars = 0

        since = datetime.datetime(dt.year, dt.month, dt.day)
        until = since + datetime.timedelta(days=1)

        for repo in repos:
            repos_count += 1
            stars += repo.stargazers_count
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
            'stars': stars,
        }


@celery.task
def get_github_stats_for_day(github_token, dt, name):
    db = connect_mongo()
    stats = db.github.by_day.find_one({'user': name, 'dt': dt})
    today = datetime.date.today().toordinal()
    if stats: # and dt != today:
        return

    print("Getting GitHub stats for {}, {}".format(dt, name))
    stats = GithubProvider(github_token).run(dt)
    db.github.by_day.update({'user': name, 'dt': dt.toordinal()}, {'$set': {'stats': stats}}, upsert=True)
