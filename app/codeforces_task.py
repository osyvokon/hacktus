from app import celery, connect_mongo
import datetime
import requests

class CodeforcesProvider:
    def __init__(self, username):
        self.username = username
        self.db = connect_mongo()
        self.collection = self.db.codeforces.submissions
        self.stats = self.db.codeforces.by_day
        self.last_record = self.refresh_last_record()

    def refresh_last_record(self):
        cr = self.collection.find({'user': self.username}).sort([('ts', -1)]).limit(1)
        last_rec = None
        if cr.count() > 0:
            for doc in cr:
                last_rec = doc
        return last_rec

    def get_last_ts(self):
        if self.last_record is None:
            self.last_record = self.refresh_last_record()
        if self.last_record is not None:
            return self.last_record['ts']
        return None

    def refresh_submissions(self):
        url = "http://codeforces.com/api/user.status?handle={}&from=1&count=500".format(self.username)
        data = requests.get(url).json()
        saved = 0
        last_ts = self.get_last_ts()

        if data['result'] is not None:
            for res in data['result']:
                timestamp = res['creationTimeSeconds']
                ts = datetime.date.fromtimestamp(timestamp).toordinal()
                if last_ts is None or last_ts < ts:
                    sub = {
                        '_id': res['id'],
                        'ts': ts,
                        'timestamp': timestamp,
                        'verdict': res['verdict'],
                        'success': res['verdict'] == 'OK',
                        'user': self.username
                    }
                    self.collection.update(sub, sub, upsert=True)
                    saved += 1
        print('saved new submissions: {}'.format(saved))

    def get_submissions(self, dt):
        since = datetime.datetime(dt.year, dt.month, dt.day)
        until = since + datetime.timedelta(days=1)
        cr = self.collection.find({'$and': [
            {'ts': {'$gte': since.toordinal()}},
            {'ts': {'$lte': until.toordinal()}},
            {'user': self.username}
        ]}).sort([('ts', -1)])
        result = []
        for doc in cr:
            result.append(doc)
        return result


@celery.task
def get_stats_for_day(name, dt):
    pr = CodeforcesProvider(name)
    result = {
        'submissions': 0,
        'passed': 0,
        'failed': 0
    }
    print( "get_stats_for_day celery run")
    if pr.last_record is None:
        print ("refresh_submissions")
        pr.refresh_submissions()

    subs = pr.get_submissions(dt)
    if subs is not None and len(subs) > 0:
        for sub in subs:
            if sub.success:
                result['passed'] += 1
            else:
                result['failed'] += 1
            result['submissions'] += 1
    pr.stats.update({'user': name, 'dt': dt.toordinal()}, {'$set': {'stats': result}}, upsert=True)
    return result
