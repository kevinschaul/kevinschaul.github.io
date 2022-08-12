---
layout: post
title:  "Tips for debugging in Internet Explorer"
date:   2014-04-14 11:37:02
slug: 2014-04-14-tips-for-debugging-in-ie
show_on_homepage: false
---

Debugging in old browsers hurts. Here are some tips I use to ease the pain.

### Use virtual machines

Instead of having to keep old, rusty Windows XP/Vista/whatever laying around
with specific versions of Internet Explorer, just use virtual machines.
It&rsquo;s remarkably painless with [VirtualBox](https://www.virtualbox.org/)
and a fantastic script called [`ievms`](https://github.com/xdissent/ievms).

`ievms` sets up VirtualBox with machines pre-installed with whichever versions
of Internet Explorer you choose. Fair warning: It takes a solid amount of time
to download and install everything.

### Run a local server, access it from your virtual machines

The real power of virtual machines comes from creating pathways between them
and the physical machine running them. To run a Python web server (from the
command line):

{% highlight bash %}
$ python -m SimpleHTTPServer
{% endhighlight %}

Your content will be server at [http://0.0.0.0:8000](http://0.0.0.0:8000).

_Bonus tip_: Devices on the same network can access what you&rsquo;re
serving, too, making mobile debugging equally easy (read: still not that easy).
Find your IP address (on OS X, it&rsquo;s shown under `System Preferences` ->
`Network`), and visit
[http://your.ip.address.here:8000](http://your.ip.address.here:8000) from your
phone.

### When things hopelessly break, use Depict

A lot of new techniques for data visualization simply do not work in old
versions of Internet Explorer. If all else fails,
[`depict`](https://github.com/kevinschaul/depict) makes it easy to generate
fallback images to replace the &ldquo;broken&rdquo; content.

`depict` takes a screenshot of a given HTML element. It can be used quite
creatively, but in it&rsquo;s simplest form looks something like this:

{% highlight bash %}
$ depict http://0.0.0.0:1337 complex-chart.png -s '#chart'
{% endhighlight %}

Those are all of my IE-debugging secrets. I&rsquo;d love to hear yours.

