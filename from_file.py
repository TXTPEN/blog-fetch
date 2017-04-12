import os
import urlparse
from blogfetch import DB
from multiprocessing.dummy import Pool as ThreadPool

bfetch = DB()

def fetch(i):
    domain = urlparse.urlparse(i['url']).hostname
    print i['url']
    bfetch.add(i['url'], i['name'])

# for i in session.query(Submission).filter(Submission.objectid > last_id, Submission.url != None).all():
#     thr = threading.Thread(target=fetch, args=(i,))
#     thr.join()


if __name__ == '__main__':
    urls = []
    with open('contact.txt') as f:
        contact = f.read().split('\n')
    for c in contact:
        c = c.split(' ')
        url = c[-1]
        name = c[0]
        urls.append({'name':name,'url':url})

    pool = ThreadPool(1)
    pool.map(fetch, urls)
    pool.close()
    pool.join()
