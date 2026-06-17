---
blogpost: true
date: '2012-08-26'
author: Kevin Schaul
category: blog
title: A simple solution for integrating Django and WordPress RSS
slug: 2012-08-26-simple-solution-integrating-django-wordpress-rss
---

# A simple solution for integrating Django and WordPress RSS

Today I am releasing [django-wordpress-rss](https://github.com/kevinschaul/django-wordpress-rss) – a Django template tag for integrating Wordpress articles. It's available today via [PyPI](http://pypi.python.org/pypi/django-wordpress-rss/0.1.0).

This code was developed as an integral piece of the [Seattle Times Election Guide](http://elections.seattletimes.com/). I made it simple to dynamically pull in content based on a WordPress category.

How simple?

```
pip install django-wordpress-rss
```

    
```
WORDPRESS_RSS_BASE_URL = 'http://www.kevinschaul.com'
```

    
```
```
```
```
<ul>```
    <li><a href="{{ item.href }}">{{ item.title }}</a></li>
</ul>
```
```
```

Have ideas for improvement? [Open up an issue on GitHub](https://github.com/kevinschaul/django-wordpress-rss/issues).

