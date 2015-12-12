import datetime
from app import celery, connect_mongo
from goodreads import client


class GoodreadsProvider:
    def __init__(self, token):
        print(token)
        self.client = client.GoodreadsClient(token)

    def run(self, dt):
        return self.client


def get_stats_for_day(token, dt):
    db = connect_mongo()
    coll = db.goodreads
    stats = coll.by_day.find_one({'dt': dt})
    today = datetime.date.today().toordinal()
    if stats and dt != today:
        return

    stats = GoodreadsProvider(token).run(dt)
    coll.by_day.update({'dt': dt.toordinal()},
                       {
                           '$set': {
                               'stats': stats
                           }
                       },
                       upsert=True)
