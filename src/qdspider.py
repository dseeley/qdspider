#!/usr/bin/python -u

"""
 (c) Copyright 2016 Dougal Seeley.  All rights reserved.
"""

import sys
from Queue import Queue
import threading
import urllib2
import re
import json
from HTMLParser import HTMLParser

# This is the output - a tree defining the structure of the website from the starting point.
linkTree = [
    {'link': "/",
     'children': []}
]

# Save a simple list of visited links, so we don't visit them again (and cause infinite loop).  This is quicker than parsing linkTree.
linksVisited = []


# Extends threading.Thread.  An individual instance of this is used to process each URL
# Get URL, extract urls, add to queue
class cUrlWorker(threading.Thread):
    def __init__(self, queue, baseHref):
        threading.Thread.__init__(self)
        self.urlQueue = queue
        self.baseHref = baseHref
        self.lock = threading.Lock()

    def run(self):
        while True:
            link, linkTreeObj = self.urlQueue.get()

            # This is passed 'by reference' into the child queue objects so we can create a nested tree of the site.
            linkTreeChildArray = []

            # Set a lock to prevent concurrent writing to the global data structure
            self.lock.acquire()
            if link not in linksVisited:
                linksVisited.append(link)
                linkTreeObj.append({"link": link, "children": linkTreeChildArray})

                try:
                    urlResp = urllib2.urlopen(link)
                    pageHTML = urlResp.read().decode('utf-8')

                    # Create a parser object and feed it the HTML from the link
                    oLinkParser = cLinkParser(self.baseHref)
                    print "feeding: " + link
                    oLinkParser.feed(pageHTML)

                    for eachExternalLink in oLinkParser.externalLinks:
                        if eachExternalLink not in linksVisited:
                            linkTreeChildArray.append({"link": eachExternalLink})

                    for eachStaticContent in oLinkParser.staticContent:
                        if eachStaticContent not in linksVisited:
                            linkTreeChildArray.append({"link": eachStaticContent})

                    # For each internal link, add it to the processing queue, it will get picked up by the next available thread.
                    for eachInternalLink in oLinkParser.internalLinks:
                        if not re.search('^' + self.baseHref, eachInternalLink, flags=re.IGNORECASE):  # If this link is not preceded by the baseHref, prepend it.
                            eachInternalLink = self.baseHref + '/' + re.sub('^\/(.*).*', r'\1', eachInternalLink)  # Normalise the URL (remove the leading '/' if present, then add it back.
                        if eachInternalLink not in linksVisited:
                            self.urlQueue.put((eachInternalLink, linkTreeChildArray))  # Append to the queue
                        else:
                            linkTreeChildArray.append({"link": eachInternalLink})

                except urllib2.HTTPError, resp:
                    print("urllib2.HTTPError getting " + resp.url + ": code: " + str(resp.code) + " :: " + resp.reason)
                except:
                    print "Unexpected error:", sys.exc_info()[0]

            self.lock.release()

            self.urlQueue.task_done()


# Extends HTMLParser.  An instance of this is used per thread to parse out the relevant data from the HTML received.
class cLinkParser(HTMLParser):
    def __init__(self, baseHref):
        HTMLParser.__init__(self)
        self.baseHref = baseHref
        self.staticContent = []
        self.externalLinks = []
        self.internalLinks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    if re.search('^' + self.baseHref, attr[1], flags=re.IGNORECASE) or re.search('^[\/#].*', attr[1], flags=re.IGNORECASE):
                        # print "inurl: " + attr[1]
                        if attr[1] not in self.internalLinks:
                            self.internalLinks.append(attr[1])
                    else:
                        # print "exurl: " + attr[1]
                        if attr[1] not in self.externalLinks:
                            self.externalLinks.append(attr[1])
        elif tag == 'img':
            for attr in attrs:
                if attr[0] == 'src':
                    # print "img: " + attr[1]
                    if attr[1] not in self.staticContent:
                        self.staticContent.append(attr[1])


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: ' + sys.argv[0] + '  <url, e.g. http://www.dougalseeley.com>\n')
        sys.exit(1)

    # The first url we provide on the command line - the search is performed using this as a starting point
    topURL = sys.argv[1]
    baseHref = re.sub('((?:.*?://)?[^\/]+).*', r'\1', topURL)

    # This queue will hold all the URLs being parsed
    urlQueue = Queue()

    # Seed the queue
    urlQueue.put((topURL, linkTree[0]['children']))

    # Create a thread pool.
    for oUrlWorker in range(10):
        oUrlWorker = cUrlWorker(urlQueue, baseHref)
        oUrlWorker.setDaemon(1)
        oUrlWorker.start()

    # This blocks on the queue until it's empty
    urlQueue.join()

    print json.dumps(linkTree, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    main()
