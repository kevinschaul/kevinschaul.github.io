---
date: 2012-02-09 03:30:03+00:00
layout: post
slug: 2012-02-09-pdf-to-searchable-sortable-table
title: 'Tutorial: From pdf to searchable, sortable table'
---

At MinnPost, we wanted to find a good way to turn pdf files into a searchable, sortable database. With many election finance reports going public in the past few weeks, I figured I'd share what I've learned &mdash; now's the perfect time.

[Here is the final deployed table](http://www.minnpost.com/data/marriage-amendment-funds-oppose/).

It all starts with a pdf file from the government. As things go these days, the specific report we were concerned with wasn't available in csv format, even though the data begs to be comma separated. For those following along at home, I am using [this report](http://www.cfbreport.state.mn.us/rptViewer/viewRptsPCF.php?pcfID=60054). The report is basically in a table format, which simplifies things greatly.

We want to convert the pdf to a fixed-width text file. This means the text file will include spacing to keep the basic table structure intact. We can then use Google Refine to help us turn the data into an actual table format (finally!) and clean it up. Here goes!

My stellar boss [Kaeti Hinck](https://twitter.com/#!/kaeti) recommended I check out [xpdf](http://www.foolabs.com/xpdf/download.html), a command-line tool with a handy pdf-to-text option. Download and install according to the instructions. To convert the pdf, use this command:

{% highlight bash linenos %}
pdftotext -layout name_of_pdf.pdf name_of_output.txt
{% endhighlight %}

Check out the text file you just created. It should look very much like the pdf; the spacing is key.

Now, import it into [Google Refine](http://code.google.com/p/google-refine/) (if you don't have it, you need it). I hadn't used Refine at all up until this project, and I can see myself using it much more from here on. In the update preview, skip as many lines as needed to get past the title pages. Then, carefully click your mouse to place the column lines where they should be. Make these as accurate as possible. Then, create the project.

![Using Google Refine]({{ site.url }}/assets/posts/2012-02-08-pdf-to-searchable-sortable-table/google-refine.png)

Here comes the tricky part: We end up with a file that has multiple rows with each record. I'm certainly not a Refine master, but I did manage to figure out a way to fix this. Take a few minutes to look up tutorials on Refine. Here are a few things I learned along the way:
	
* Many of my cells that look blank actually had spaces in them. To get rid of all these spaced fields by hovering over a few, clicking edit, and deleting all the spaces. Apply this to all identical cells.

* Play around with different faceting techniques. There's likely a way to solve your issue in Refine, and faceting is a huge part in that.

* My file was set up so that if a person donated on multiple dates, their name would only show the first time. I corrected this by flagging all the cells without a date and filling down (after the addresses were nixed).

When the data looked good, I exported as a csv. The file had each donation listed separately, so anyone who donated more than once was in my file more than once. I fixed this with a simple Python script that added each persons donations together, so that each person took up one row in the csv.

I imported this into Excel (*shudder*) to use a few calculations to display the names correctly. Here I compiled contributions to other organizations (more pdf files turned to csv).

Finally, I had a working spreadsheet of all donors. After checking accuracy (highly recommended), I threw these into [Table-Setter](http://propublica.github.com/table-setter/) (also highly recommended) and deployed.

The toughest part was getting the data into a csv file, but thanks to a few open source tools, life wasn't bad. It sure beats manually typing all 200-plus pages, and is much more reliable.

Again, [check out the final deployed table](http://www.minnpost.com/data/marriage-amendment-funds-oppose/).

The editors at MinnPost are always stretching my talents, and I always strive to let others take from what I've learned. Feel free to show me a better way, or to say hello.

