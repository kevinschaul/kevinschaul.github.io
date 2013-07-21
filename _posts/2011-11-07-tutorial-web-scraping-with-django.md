---
date: 2011-11-07 07:21:06+00:00
layout: post
slug: 2011-11-07-tutorial-web-scraping-with-django
title: "Tutorial: Web scraping with Django"
wordpress_id: 45
---

For a recent [MinnPost](http://www.minnpost.com) project, we wanted to scrape court dockets, so I figured I'd break out a python script in the wonderful [ScraperWiki](https://scraperwiki.com/). One of my favorite features is that you can schedule a scraper to run automatically. One of my least favorite features is that the limit on automatic scrapers is once per day. We needed something to run every half hour.

**Enter Django**

It seems that every news hacker is using [Django](https://www.djangoproject.com/) for something these days, and why not? It's fast, flexible and a major headache to deploy (I'll expand on this in a later post).

To build the scraper, I wrote a python script that used [requests](http://docs.python-requests.org/en/latest/index.html) and [lxml](http://lxml.de/), invoked by a cron call to a Django command.

Here's the site we want to scrape (and a great example of how "open" government really isn't): [Minneapolis court dockets](http://www.mnd.uscourts.gov/calendars/mpls/index.html)

**models.py**

The models.py file is very simple, containing only the fields we want to scrape.

{% highlight python linenos %}
from django.db import models
  
class Case(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    court = models.CharField(max_length=60)
    description = models.CharField(max_length=1024)
    def __unicode__(self):
        return self.description
{% endhighlight %}

This should be self-explanatory if you're at all familiar with Django; if not, I highly recommend the [official tutorial](https://docs.djangoproject.com/en/1.3/intro/tutorial01/).

**The scraping script**

Using requests and lxml, scraping in python is downright enjoyable. Look how easy it is to grab a site's source and convert it into a useful object:
    
{% highlight python linenos %}
r = requests.get(url)
root = lxml.html.fromstring(r.content)
{% endhighlight %}

Boom.

Take a look at the source code of the [court dockets site](http://www.mnd.uscourts.gov/calendars/mpls/index.html), and you'll see how fun it is to scrape most government sites. The information we want to get is nested in four tables (!), all without ids or classes.

Luckily, one of these tables has an attribute that we can immediately jump to. Here's the code I'm using to get the contents we want:
    
{% highlight python linenos  %}
import requests
import lxml
from lxml import html

# To grab the URL and convert into an lxml object ...
r = requests.get('http://www.mnd.uscourts.gov/calendars/mpls/index.html')
root = lxml.html.fromstring(r.content)
for tr in root.cssselect("table[cellpadding=1] tr")[1:]:
    tds = tr.cssselect("td")
    start = tds[1].text_content().strip()
    end = tds[2].text_content().strip()
    description = tds[3].text_content().strip()
{% endhighlight %}

The text_content() function takes what's inside an html element sans html tags, and strip() removes whitespace.

**The magic - Django commands**

Django commands are scripts that can do whatever you like, easily invoked through the command line:
    
{% highlight bash linenos  %}
python manage.py nameofacommand
{% endhighlight %}

This is great to keep everything inside a Django project, and the scripts are easily accessible. These files are stored inside your app -> management -> commands (my full path is minnpost/dockets/management/commands/scrapedockets.py). If you don't have these folders already, create them, but don't forget to add __init.py__ files. I turned my scraping code into a command called scrapedockets.py  - full code below.

{% highlight python linenos %}
from django.core.management.base import BaseCommand
from minnpost.dockets.models import Case

import requests
import lxml
from lxml import html
import time, datetime

class Command(BaseCommand):
    help = 'Scrapes the sites for new dockets'

    def handle(self, *args, **options):
        self.stdout.write('\nScraping started at %s\n' % str(datetime.datetime.now()))

        courts = {'Minneapolis': 'http://www.mnd.uscourts.gov/calendars/mpls/index.html', 'St. Paul': 'http://www.mnd.uscourts.gov/calendars/stp/index.html', 'Duluth': 'http://www.mnd.uscourts.gov/calendars/dul/index.html', 'Fergus Falls & Bemidji': 'http://www.mnd.uscourts.gov/calendars/ff/index.html'}

        for court, url in courts.iteritems():
            self.stdout.write('Scraping url: %s\n' % url)
            r = requests.get(url)
            root = lxml.html.fromstring(r.content)
            # Find the correct table element, skip the first row
            for tr in root.cssselect('table[cellpadding=1] tr')[1:]:
                tds = tr.cssselect('td')
                start = tds[1].text_content().strip()
                end = tds[2].text_content().strip()
                description = tds[3].text_content().strip()
                convertedStart = convertTime(start)
                convertedEnd = convertTime(end)
                dbStart = datetime.datetime.fromtimestamp(convertedStart)
                dbEnd = datetime.datetime.fromtimestamp(convertedEnd)

                if not Case.objects.filter(start=dbStart, end=dbEnd, court=court, description=description):
                    c = Case(start=dbStart, end=dbEnd, court=court[:60], description=description[:1024])
                    c.save()

now = time.gmtime(time.time())

def convertTime(t):
    """Converts times in format HH:MMPM into seconds from epoch (but in CST)"""
    convertedTime = time.strptime(t + ' ' + str(now.tm_mon) + ' ' + str(now.tm_mday) + ' ' + str(now.tm_year), "%I:%M%p %m %d %Y")
    return time.mktime(convertedTime)
    # This used to add 5 * 60 * 60 to compensate for CST
{% endhighlight %}

Django commands require a class Command that extends BaseCommand and has a function handle(). This is called when the command is invoked.

I wrote an (admittedly) bad function to convert the times into seconds to store them in the database. I believe I went against a general rule, which is to store times in GMT, but I don't competely understand how Django uses the timezone settings. Help?

Anyway, I end up with variables for each piece of information I want to store. I check if a Case already exists with the same information, and if it doesn't, I create it and save it to the database. I used python's slice operator to make sure the court and description aren't too long (according to the database setup I created in models.py).

**The magic, pt. 2 - Cron**

To make this worthwhile, we need it to run on its own every half hour. Unix systems make this simple, with a daemon called Cron. If you're using Ubuntu, [here's a nice guide](https://help.ubuntu.com/community/CronHowto) (other distros will be very similar). Cron schedules scripts to be run at different intervals, and its uses are virtually limitless.

I created a script, scrapedockets.sh, which simply calls the Django command we just walked through.

{% highlight bash linenos %}
#!/bin/bash
python manage.py scrapedockets
{% endhighlight %}

Don't forget to make it executable:

{% highlight bash linenos %}
sudo chmod +x scrapedockets.sh
{% endhighlight %}

I used a crontab on the default user to call the scrapedockets.sh Django command every half hour. Edit your crontab using the command:

{% highlight bash linenos %}
crontab -e
{% endhighlight %}

Each line is something you want cron to do. Here's what mine looks like:

{% highlight bash linenos %}
*/30 * * * * /opt/django-projects/minnpost/scripts/scrapedockets.sh >> /opt/log/scrapedockets.log
{% endhighlight %}

Cron will run the script scrapedockets.sh every 30 minutes (any minute value evenly divisible by 30) and log output to scrapedockets.log. I encourage you to [look at a guide](https://help.ubuntu.com/community/CronHowto) to see what the structure is.

If everything is set up, your Django database should start filling up with information. Build some views, and show the world what you've found.

**If you know a better way, please share!**

I'm far from an expert, so if you see something fishy here, leave a comment or tweet at @kevinschaul.

