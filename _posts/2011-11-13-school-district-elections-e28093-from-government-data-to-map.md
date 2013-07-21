---
date: 2011-11-13 21:51:21+00:00
layout: post
slug: 2011-11-13-school-district-elections-from-government-data-to-map
title: "School district elections - From government data to map"
wordpress_id: 65
---

_Note: This isn't meant to be a tutorial. It's merely a representation of the steps I had to take to produce [this map](http://www.minnpost.com/data/schoollevies/), so that journalists can better understand the process. As has been said, it isn't magic, and more transparency helps everyone. I tried to authentically represent the complexity of this programming problem, and not over- or under-simplify it._

This past week, I worked with election data for the first time. Beth Hawkins, education reporter at MinnPost, wanted to do something special for the school district levy election. She forwarded me a document from the Minnesota Secretary of State containing information about the then upcoming election. She was hoping for a way to display, on a map, which school districts passed their referendums.

Simple, right?

**Clean that data**

Working with data is all about its transformation into information. Here's a piece of the file [from the state](http://electionresults.sos.state.mn.us/20111108/  ).

    
    MN;;;5031;SCHOOL DISTRICT QUESTION 1 (ISD #11);000011;9001;YES;;;NP;36;36;20698;63.03255474007900;32837
    MN;;;5031;SCHOOL DISTRICT QUESTION 1 (ISD #11);000011;9002;NO;;;NP;36;36;12139;36.96744525992000;32837
    MN;;;5032;SCHOOL DISTRICT QUESTION 2 (ISD #11);000011;9001;YES;;;NP;36;36;16580;50.59968871120300;32767
    MN;;;5032;SCHOOL DISTRICT QUESTION 2 (ISD #11);000011;9002;NO;;;NP;36;36;16187;49.40031128879600;32767
    MN;;;5033;SCHOOL DISTRICT QUESTION 3 (ISD #11);000011;9001;YES;;;NP;36;36;14725;45.00993428091000;32715
    MN;;;5033;SCHOOL DISTRICT QUESTION 3 (ISD #11);000011;9002;NO;;;NP;36;36;17990;54.99006571908900;32715


Luckily, they also provide files that explain what those numbers mean. Another file lays out codes for each school district.

    
    11;ANOKA-HENNEPIN;2;Anoka
    11;ANOKA-HENNEPIN;27;Hennepin


If you piece these two together, you'll find that these results are for Anoka-Hennepin School District (see the “000011” in each line above? That corresponds to the “11” in the second file).

The other numbers represent the different votes (YES/NO), votes for, precincts reporting and a few other fields. We’re only interested in the percent of yes votes – since all the precincts have reported and the results are final, we can assume that 50 percent or above means the levy passed.

But before we can jump into that, we need to turn the semicolon-delimited files into .csv files (a form of Excel spreadsheets). I created a csv file (questions-results.csv) that contained only a line of headings, so I could easily keep track of which number means what. I then appended ( ">>" ) the election results data to this file, making it a traditional .csv file with [csvcut](http://readthedocs.org/docs/csvkit/en/0.2.0/scripts/csvcut.html).

    
    csvcut -d ';' school-questions-results.csv >> questions-results.csv


Now that the data is in proper format, it can be opened in Excel to be further examined (or if you're a hardcore ninja like Jeff Guntzel, you can [perform an audit with his masterful script](http://www.jsguntzel.com/skinnynotebook/2011/10/28/super-quick-data-audit-with-this-csvkit-shell-script/)).

**Prep a shapefile**

This data is useless unless we show our readers what's interesting. I got the shapefile for Minesota school districts from [here](http://www.census.gov/cgi-bin/geo/shapefiles2010/main) (if you ever need a shapefile, look here).

I used the wonderful [ShpEscape](http://shpescape.com/) site to convert the shapefile into a Google Fusion Table. For those following along at home, click on visualize -> map to see the shapefile.

I needed to join our election data with the shapefile stuff, so I exported the Fusion Table as a csv. Excel didn't like the formatting, so I imported the csv into Google Docs as a spreadsheet. Here's where the fun began.

I discovered that the shapefile had an ID for each district, but it wasn't the same ID as our election data. To make matters worse, the names didn't closely match up, either.

Sometimes a hacker has to give it up and do things manually. This was one of those times. I went through the election data file, adding a column with the election's ID to each district in the shapefile.  Since it was something I knew I'd only have to do once, it wasn't a huge deal.

I exported this new file as a csv and wrote one of the craziest python scripts in my life.

**What story can this data tell?**

I met with our editor to figure out the best way to display the data. The school districts voted on different levies, some passed three, some passed one, some passed none. Since they didn't vote on something universal, we decided to simple show the percentage of levies that each school district passed.

My script looks at each line in the election results data, looping through the shapefile to find the corresponding district. Since each district voted on a different number of ballots and each on question was on its own line, I created a dict (python's version of key/value pairs) and put all the data I cared about in it.

I extracted two cases:



	
  1. This is the first question that we are looking at for this district, so add the shapefile information and calculate the percent of yes/no votes (obviously 100 or 0).

	
  2. This is another question for the same district, so recalculate the percentage and add it to the information already established.


Finally, I loop through the dict and write a new csv file. My final file had only the rows I wanted: geometry (shapefile info), name of school district, percent of levies passed, number of levies passed, and total number of levies voted on.

This script is clearly not optimized, but since it's only run once to generate the data, it really doesn't matter.

**Put this on the map**

Finally, the data was ready to tell a story. I uploaded my new csv file into Fusion Tables, and Kaeti Hinck picked out some colors to display the different percentages. We then embedded it into our site.

**Takeaway**

Data journalism ins't magic, and traditional journalists should know that. If you want to be better at your job, work to understand the process behind other fields, too.

Obviously every programming problem is different, but this should be a nice insight to the process. Let's start discussions in newsrooms to promote programming literacy.

View the final map [here](http://www.minnpost.com/data/schoollevies/).
