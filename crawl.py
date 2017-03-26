import threading, urllib, urlparse
from HTMLParser import HTMLParser
import re

pool = set()
allowed = ['github.com', 'linkedin.com', 'stackoverflow.com', 'github.io', 'plus.google.com']
ret = []

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
          pool.add(url)
	  threading.Thread.__init__(self)

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

          twitters = tweetParse(urlMarkUp)
          linkedins = linkedinParse(urlMarkUp)
          emails = emailParse(urlMarkUp)
          if linkedins:
              print 'linkedin' , linkedins
          if twitters:
              print 'twitter' , twitters
          if emails:
              print 'email' , emails

      	  self.binarySemaphore.acquire() # wait if another thread has acquired and not yet released binary semaphore
	  # print "Thread #%d: Reading from %s" %(self.threadId, self.url)
	  # print "Thread #%d: Crawl Depth = %d" %(self.threadId, self.crawlDepth)
      	  # print "Thread #%d: Retreived the following links..." %(self.threadId)
	  urls = []
	  for link in linkHTMLParser.links:
	      link = urlparse.urljoin(self.url, link)
	      urls.append(link)
	      # print "\t"+link
	  # print ""
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
	      	 CrawlerThread(binarySemaphore, url, self.crawlDepth-1).start()



if __name__ == "__main__":
   binarySemaphore = threading.Semaphore(1)
   urls = [("http://rickyhan.com", 3)]
   for (url, crawlDepth) in urls:
       CrawlerThread(binarySemaphore, url, crawlDepth).start()
