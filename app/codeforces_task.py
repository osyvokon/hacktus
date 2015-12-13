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
        self.url = "http://codeforces.com/api/user.status?handle={}&from=1&count={}"
        self.refresh_submissions()

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

    def has_new_submissions(self):
        url = self.url.format(self.username, 1)
        data = requests.get(url).json()
        last_ts = self.get_last_ts()
        result = False

        if data['result'] is not None:
            for res in data['result']:
                timestamp = res['creationTimeSeconds']
                ts = datetime.date.fromtimestamp(timestamp).toordinal()
                if last_ts is None or last_ts < ts:
                    result = True
        print("Codeforces - checking for new submissions: {}".format(self.username))
        return result

    def refresh_submissions(self):
        if not self.has_new_submissions():
            return
        print("Codeforces - refreshing submissions for: {}".format(self.username))
        url = self.url.format(self.username, 500)
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
        print('Codeforces - saved submissions: {}'.format(saved))

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

    def get_submissions_between(self, start_date, end_date):
        since = datetime.datetime(start_date.year, start_date.month, start_date.day)
        until = datetime.datetime(end_date.year, end_date.month, end_date.day) + datetime.timedelta(days=1)
        cr = self.collection.find({'$and': [
            {'ts': {'$gte': since.toordinal()}},
            {'ts': {'$lt': until.toordinal()}},
            {'user': self.username}
        ]}).sort([('ts', -1)])
        result = []
        for doc in cr:
            result.append(doc)
        return result

    def subs_to_stats(self, subs):
        result = {
            'submissions': 0,
            'passed': 0,
            'failed': 0
        }
        if subs is not None and len(subs) > 0:
            for sub in subs:
                if 'success' in sub and sub['success']:
                    result['passed'] += 1
                else:
                    result['failed'] += 1
                result['submissions'] += 1
        return result

    def get_stats_for_day(self, name, dt):
        return self.subs_to_stats(self.get_submissions(dt))

    def get_stats_for_week(self, name):
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)
        return self.subs_to_stats(self.get_submissions_between(start_date, end_date))

    def get_stats_for_month(self, name):
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)
        return self.subs_to_stats(self.get_submissions_between(start_date, end_date))

