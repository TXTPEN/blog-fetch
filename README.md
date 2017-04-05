# blog-fetch
given a blog url, fetch contact info (twitter, email, linkedin)

## install crontab

```bash
crontab -e
```


Add the following lines: 

```
*/10 * * * * /root/blogfetch/.venv/bin/python /root/blogfetch/util/hncrawl.py cron
*/10 * * * * /root/blogfetch/.venv/bin/python /root/blogfetch/feed.py
```

