import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import urlparse
from blogfetch import DB
from multiprocessing.dummy import Pool as ThreadPool

Base = declarative_base()
engine = create_engine('postgresql://postgres@localhost/hacker_news', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

current_path = os.path.dirname(os.path.abspath(__file__))

class Submission(Base):
    __table__ = sa.Table('hn_submissions', Base.metadata, autoload=True, autoload_with=engine)
    def __repr__(self):
        return "<class Submission id=" + str(self.objectid) +" >"

with open(current_path + '/last_id', 'r') as f:
    last_id = f.read()
with open(current_path + '/diff.txt', 'r') as f:
    do_not_post = f.read().split('\n')
with open(current_path + '/sent.txt', 'r') as f:
    already_sent = f.read().split('\n')

bfetch = DB()

def fetch(i):
    domain = urlparse.urlparse(i.url).hostname
    print i.url
    if domain not in do_not_post and domain not in already_sent:
        bfetch.add(i.url)
        with open(current_path + "/sent.txt", "a") as f:
            f.write("\n"+domain)
    with open(current_path + '/last_id', 'w') as f:
        f.write(str(i.objectid))

# for i in session.query(Submission).filter(Submission.objectid > last_id, Submission.url != None).all():
#     thr = threading.Thread(target=fetch, args=(i,))
#     thr.join()


if __name__ == '__main__':
    urls = []
    for i in session.query(Submission).filter(Submission.objectid < last_id, Submission.url != None).all():
        urls.append(i)
    pool = ThreadPool(1)
    pool.map(fetch, urls)
    pool.close()
    pool.join()
