##QD Spider
A multi-threaded python website spider.

When provided with a URL, it will find all links recursively, and print a basic site-map in JSON format


##Usage
```
$ python ./qdspider.py http://www.dougalseeley.com
```


###Limitations due to time constraints:
+ Command line base href must start with a protocol (e.g. http://, ftp://).  This could be parsed out easily, given time.
+ If any of the links in the page are missing the protocol, then they must not have a domain, (e.g. google.com/helloworld/42).  Again this could be parsed out easily, given time.
+ Will not work with Single Page Applications whose pages are rendered in-browser (e.g. AngularJS pages).
+ Does not display the full tree, as this is more often than not, circular.
+ Does not throttle the number of connections made, can cause HTTP 429 responses (too many connections)
