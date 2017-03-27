import threading, urllib, urlparse
from HTMLParser import HTMLParser
import re

pool = set()
allowed = ['github.com', 'linkedin.com', 'stackoverflow.com', 'github.io', 'plus.google.com']

class LinkHTMLParser(HTMLParser):
      A_TAG = "a"
      HREF_ATTRIBUTE = "href"

      def __init__(self):
      	  self.links = []
	  HTMLParser.__init__(self)

      def handle_starttag(self, tag, attrs):
      	  """Add all 'href' links within 'a' tags to self.links"""
      	  if cmp(tag, self.A_TAG) == 0:
	     for (key, value) in attrs:
       	     	 if cmp(key, self.HREF_ATTRIBUTE) == 0:
		    self.links.append(value)

      def handle_endtag(self, tag):
      	  pass

def emailParse(markup):
    match_obj = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', markup)
    if match_obj:
        return list(set(match_obj))

def linkedinParse(markup):
    match_obj = re.findall(r'(linkedin.com.+)"', markup)
    if match_obj:
        return list(set(match_obj))

def tweetParse(markup):
    match_obj = re.findall(r"http(?:s)?:\/\/(?:www\.)?twitter\.com\/([a-zA-Z0-9_]+)", markup)
    if match_obj:
        return list(set(match_obj))

class CrawlerThread(threading.Thread):
      def __init__(self, binarySemaphore, url, crawlDepth):
      	  self.binarySemaphore = binarySemaphore
	  self.url = url
	  self.crawlDepth = crawlDepth
	  self.threadId = hash(self)
          self.ret = {'twitter': [], 'email': [], 'linkedin': []}
          pool.add(url)
	  threading.Thread.__init__(self)

      def join(self):
          threading.Thread.join(self)
          return self.ret
      def run(self):
      	  """Print out all of the links on the given url associated with this particular thread. Grab the passed in
	  binary semaphore when attempting to write to STDOUT so that there is no overlap between threads' output."""
	  socket = urllib.urlopen(self.url)
	  urlMarkUp = socket.read()
	  linkHTMLParser = LinkHTMLParser()
          try:
	      linkHTMLParser.feed(urlMarkUp)
          except Exception:
              pass

          twitter = tweetParse(urlMarkUp)
          linkedin = linkedinParse(urlMarkUp)
          email = emailParse(urlMarkUp)
          if linkedin: self.ret['linkedin'] += linkedin
          if twitter: self.ret['twitter'] += twitter
          if email: self.ret['email'] += email

      	  self.binarySemaphore.acquire() # wait if another thread has acquired and not yet released binary semaphore
	  print "Thread #%d: Reading from %s" %(self.threadId, self.url)
	  print "Thread #%d: Crawl Depth = %d" %(self.threadId, self.crawlDepth)
      	  print "Thread #%d: Retreived the following links..." %(self.threadId)
	  urls = []
	  for link in linkHTMLParser.links:
	      link = urlparse.urljoin(self.url, link)
	      urls.append(link)
	      print "\t"+link
	  print ""
	  self.binarySemaphore.release()
	  for url in urls:
              domain = urlparse.urlparse(url).netloc
              old_domain = urlparse.urlparse(self.url).netloc
              if domain in allowed:
                  pass
              elif url in pool:
                  continue
              elif domain != old_domain:
                  continue
	      # Keep crawling to different urls until the crawl depth is less than 1
              if self.crawlDepth > 1:
	      	 t = CrawlerThread(self.binarySemaphore, url, self.crawlDepth-1)
                 t.start()
                 result = t.join()
                 for key in result.keys():
                     self.ret[key] = result[key] + self.ret[key]

class BlogFetch():
    def __init__(self, url, crawlDepth=3):
        self.url = url
        self.crawlDepth = crawlDepth
        self.binarySemaphore = threading.Semaphore(1)
    def fetch(self):
        t = CrawlerThread(self.binarySemaphore, self.url, self.crawlDepth)
        t.start()
        return t.join()

if __name__ == "__main__":
    b = BlogFetch("http://rickyhan.com", 3)
    print b.fetch()
