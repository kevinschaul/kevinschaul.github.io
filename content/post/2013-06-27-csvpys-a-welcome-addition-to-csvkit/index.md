---
date: 2013-06-27 13:32:11+00:00
layout: post
slug: 2013-06-27-csvpys-a-welcome-addition-to-csvkit
title: csvpys - A welcome addition to csvkit
wordpress_id: 1470
show_on_homepage: false
blurb: The brilliant Krzysztof Dorosz has developed csvpys, an extension to the data journalist must-have csvkit.
---

The open source community has come through yet again.

The brilliant [Krzysztof Dorosz](https://twitter.com/krzysztofdorosz) has developed [csvpys](https://github.com/cypreess/csvkit/blob/master/docs/scripts/csvpys.rst), an extension to the data journalist must-have [csvkit](http://csvkit.readthedocs.org/en/latest/).

(If you're already lost, read up on [what it can do for you](http://www.anthonydebarros.com/2011/09/11/csvkit-data-files/). It's well worth your time.)

csvpys allows users to compute new columns in csv files using an arbitrary line of python code. As it iterates through each row in the csv file, csvpys makes the python one-liner aware of each entry in that row in a local variable. The tool even [imports handy modules](https://github.com/cypreess/csvkit/blob/master/docs/scripts/csvpys.rst#scripting-language) for use in your python code.

Of course, many common uses of csvpys can also be done with Excel functions, but at the massive cost of human interaction in data manipulation. Especially in data journalism contexts, the ultimate goal is to automate all data manipulation (using [Make](http://bost.ocks.org/mike/make/), scripts, or however else it can be done). csvpys gives scripters much more room for creativity.

Use it to compute medians, distinguish important value boundaries, properly capitalize names, regex certain rows, anything. The possibilities are endless.

As a short example, pretend we have a csv containing White House salaries from 2012:

```
$ csvcut some-white-house-salaries-2012-cut.csv | csvlook
```

    |----------------------+---------|
    |  Name                | Salary  |
    |----------------------+---------|
    |  Aberger, Marie E.   | 42000   |
    |  Abrevaya, Sandra    | 90000   |
    |  Agnew, David P.     | 153500  |
    |  Ahmed, Rumana A.    | 42565   |
    |  Albino, James       | 93000   |
    |  Alcantara, Elias    | 42000   |
    |  Anderson, Amanda D. | 102000  |
    |  Anello, Russell M.  | 92001   |
    |  Arguelles, Adam J.  | 102000  |
    |----------------------+---------|

Our news application does something special for those with Salaries over $100,000, and we'd like to have this as a row in our spreadsheet. First instinct might be to (*shudder*) fire up Excel and write a quick function to do the calculation. But, this introduces the possibility of human error, and isn't as quickly reproducible as running a script with a bunch of commands.

With csvpys:

```
$ csvpys -s Bankroller "int(c[2]) >= 100000" some-white-house-salaries-2012-cut.csv | csvlook
```

    |----------------------+--------+-------------|
    |  Name                | Salary | Bankroller  |
    |----------------------+--------+-------------|
    |  Aberger, Marie E.   | 42000  | False       |
    |  Abrevaya, Sandra    | 90000  | False       |
    |  Agnew, David P.     | 153500 | True        |
    |  Ahmed, Rumana A.    | 42565  | False       |
    |  Albino, James       | 93000  | False       |
    |  Alcantara, Elias    | 42000  | False       |
    |  Anderson, Amanda D. | 102000 | True        |
    |  Anello, Russell M.  | 92001  | False       |
    |  Arguelles, Adam J.  | 102000 | True        |
    |----------------------+--------+-------------|

Just add that to your Makefile, and you'll never accidentally mangle your data again. How's that for automation?

