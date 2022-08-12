---
date: 2012-08-26 20:02:34+00:00
layout: post
slug: 2012-08-26-simple-solution-integrating-django-wordpress-rss
title: A simple solution for integrating Django and WordPress RSS
wordpress_id: 1024
---

Today I am releasing [django-wordpress-rss](https://github.com/kevinschaul/django-wordpress-rss) – a Django template tag for integrating Wordpress articles. It's available today via [PyPI](http://pypi.python.org/pypi/django-wordpress-rss/0.1.0).

This code was developed as an integral piece of the [Seattle Times Election Guide](http://elections.seattletimes.com/). I made it simple to dynamically pull in content based on a WordPress category.

How simple?

{% highlight bash linenos %}
pip install django-wordpress-rss
{% endhighlight %}

    
{% highlight bash linenos %}
WORDPRESS_RSS_BASE_URL = 'http://www.kevinschaul.com'
{% endhighlight %}

    
{% highlight html linenos %}
{% raw %}
{% load wordpress_rss %}
{% wordpress_rss rss_category 10 as rss_results %}
<ul>{% for item in rss_results %}
    <li><a href="{{ item.href }}">{{ item.title }}</a></li>
</ul>
{% endfor %}
{% endraw %}
{% endhighlight %}

Have ideas for improvement? [Open up an issue on GitHub](https://github.com/kevinschaul/django-wordpress-rss/issues).

