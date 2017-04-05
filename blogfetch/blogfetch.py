import threading, urllib2, urlparse
from HTMLParser import HTMLParser
import re

pool = set()
MAX_POOL = 400

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

def titleParse(markup):
    match_obj = re.findall(r'(?:<title>)(.+?)(?:</title>)', markup)
    if match_obj:
        return list(set(match_obj))

def nameParse(markup):
    match_obj = re.findall('name is (.+?)(?: and|\W)', markup)
    if match_obj:
        return list(set(match_obj))

def deCFEmail(fp):
    r = int(fp[:2],16)
    email = ''.join([chr(int(fp[i:i+2], 16) ^ r) for i in range(2, len(fp), 2)])
    return email

def emailParse(markup):
    if re.findall(r'email-protection', markup):
        match = re.findall(r'data-cfemail="(\w+)"', markup)
        if match:
            return [deCFEmail(match[0])]
    match_obj = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', markup)
    if match_obj:
        return list(set(match_obj))

def linkedinParse(markup):
    match_obj = re.findall(r'linkedin.com/in/(.+?)"', markup)
    if match_obj:
        res = list(set(match_obj))
        return filter(lambda x: 'share' not in x, res)

def tweetParse(markup):
    match_obj = re.findall(r"http(?:s)?:\/\/(?:www\.)?twitter\.com\/([a-zA-Z0-9_]+)", markup)
    if match_obj:
        res = list(set(match_obj))
        [res.remove(i) for i in ['intent','share'] if i in res]
        return res

class CrawlerThread(threading.Thread):
      def __init__(self, binarySemaphore, url, crawlDepth=3, originalDepth=3, allowed={}):
          """
             Note: originalDepth should be the same as crawlDepth.
             This is used to determine how far the crawler has strayed
             away in a tail recursion.
          """
          self.urlMarkUp = ''
      	  self.binarySemaphore = binarySemaphore
	  self.url = url
	  self.crawlDepth = crawlDepth
	  self.originalDepth = originalDepth
	  self.threadId = hash(self)
          self.result = {key:[] for key in ['linkedin', 'twitter', 'name', 'title', 'email', 'url']}
          self.allowed = allowed
          pool.add(re.sub(r'#.*$', '', url))
	  threading.Thread.__init__(self)

      def join(self):
          threading.Thread.join(self)
          return self.result

      def update_result(self):
          is_top = self.crawlDepth == self.originalDepth
          if is_top:
              self.result['url'] = [self.url]

              title = titleParse(self.urlMarkUp)
              if title: self.result['title'] += title

              name = nameParse(self.urlMarkUp)
              if name: self.result['name'] += name

          twitter = tweetParse(self.urlMarkUp)
          linkedin = linkedinParse(self.urlMarkUp)
          email = emailParse(self.urlMarkUp)
          if linkedin: self.result['linkedin'] += linkedin
          if twitter: self.result['twitter'] += twitter
          if email: self.result['email'] += email

      def recurse(self):
      	  self.binarySemaphore.acquire() # wait if another thread has acquired and not yet released binary semaphore
	  urls = []
	  for link in self.linkHTMLParser.links:
	      link = urlparse.urljoin(self.url, link)
	      urls.append(link)
	      # print "\t"+link
	  # print ""
	  self.binarySemaphore.release()

          depth_from_root = self.originalDepth - self.crawlDepth
          # print self.crawlDepth, depth_from_root
          if depth_from_root == 0:
              if not self.url.endswith('contact'):
                  if self.url.endswith('/'):
                      urls.append(self.url+'contact')
                  else:
                      urls.append(self.url+'/contact')

              apex_of_subdomain = re.findall(r"\.(\w+\.\w+)", self.url)
              if apex_of_subdomain: # if is under a subdomain blog.blah.com -> blah.com
                  apex = apex_of_subdomain[0]
                  self.allowed[apex] = True
                  urls.append('http://' + apex)


	  for url in urls:
              domain = urlparse.urlparse(url).netloc
              old_domain = urlparse.urlparse(self.url).netloc

              if len(pool) > MAX_POOL:
                  break

              if re.sub(r'#.*$', '', url) in pool:
                  continue
              elif domain in self.allowed and self.allowed[domain]:
                  self.allowed[domain] = False
                  pass
              elif domain != old_domain:
                  continue

	      # Keep crawling to different urls until the crawl depth is less than 1
              if self.crawlDepth > 1:
                  t = CrawlerThread(self.binarySemaphore, url, self.crawlDepth-1, self.crawlDepth, self.allowed)
                  t.start()
                  result = t.join()
                  for key in result.keys():
                      self.result[key] = result[key] + self.result[key]

      def run(self):
      	  """Print out all of the links on the given url associated with this particular thread. Grab the passed in
	  binary semaphore when attempting to write to STDOUT so that there is no overlap between threads' output."""
          headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36' }
          req = urllib2.Request(self.url, None, headers)
          try:
	      socket = urllib2.urlopen(req)
          except urllib2.HTTPError:
              return
          content_type = socket.headers['content-type']
          if 'text' not in content_type: return
	  self.urlMarkUp = socket.read()
	  self.linkHTMLParser = LinkHTMLParser()
          try:
	      self.linkHTMLParser.feed(self.urlMarkUp)
          except Exception:
              pass

          self.update_result()

	  # print "Thread #%d: Reading from %s" % (self.threadId, self.url)
	  # print "Thread #%d: Crawl Depth = %d" % (self.threadId, self.crawlDepth)
      	  # print "Thread #%d: Retreived the following links..." % (self.threadId)

          self.recurse()


class BlogFetch():
    def __init__(self, url, crawlDepth=3):
        self.url = url
        self.crawlDepth = crawlDepth
        self.binarySemaphore = threading.Semaphore(1)
    def fetch(self):
        t = CrawlerThread(binarySemaphore=self.binarySemaphore,
                          url=self.url,
                          crawlDepth=self.crawlDepth,
                          originalDepth=self.crawlDepth,
                          allowed={'github.com': True,
                                   'linkedin.com': True,
                                   'stackoverflow.com': True,
                                   'github.io': True,
                                   'plus.google.com': True,
                                  }
                          )
        t.start()
        res = t.join()
        return {key: list(set(res[key])) for key in res}
