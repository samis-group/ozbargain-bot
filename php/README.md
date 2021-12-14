# Oz2Slack

This is a script that sends Ozbargain RSS feed items to a Slack channel using an incoming webhook

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system

### Prerequisites

The software you need to install and have loaded in your environment:

```
Ensure that you're running PHP and that you've installed the SimpleXML module and have loaded it.
```

Make sure you've got RAM setup and you have '/tmp' mounted on your server. This is where your curl request will store it's cookie data that will be transmitted as the header information. If you don't have this setup, go into "functions.php" and adjust lines 25-26 according to where you'd like to store this cookie data. Make sure the storage is persistant upon restarts.

### Installing

How to get this running in your linux environment, first clone the repo:

```
git clone https://github.com/th3cookie/oz2slack.git
```

You need to create a "hooks.php" file when you clone this repo in the Oz2Slack directory. That file is where you will store your hooks. Here is what "hooks.php" should look like:
 
```
<?php

$testHook = "YOUR_HOOK_HERE";

$sickDealsHook = "YOUR_HOOK_HERE";
```

You need to also edit the "functions.php" file on line 27 with your session ID that you grabbed from a browser loading the RSS feed (mine was chrome):

Cron Jobs should be setup as follows (the second cron job is optional if the script isn't pulling the XML data and storing it, using the curl header and session ID data), get curl in shell to do the job. You can get your session ID by loading the feed in your browser and opening dev tools, going into feed and looking at the headers, or use Postman, whatever works. Use the 'which' command to find the location of the php and curl binaries in your shell environment:

```
*/5 * * * * /bin/php ~/oz2slack/sick_deals_testing.php > ~/oz2slack/logs/log`date +\%H\%M`.txt
*/2 * * * * /bin/curl -H 'cache-control: max-age=0' -H 'cookie: G_ENABLED_IDPS=google; PHPSESSID=INSERT_YOUR_SESSION_ID' https://www.ozbargain.com.au/deals/feed -o ~/ozxml.xml
```

If you will be installing this on a linux server, ensure the following is set/run (completely depending on your environment) and if you're running this on a cron, ensure you setup symlinks back to the home users directory as this is where PHP thinks it needs to store and load the files it handles, because the users path variable that the user is running the cron for, has a home directory which is set as such, so you need to symlink to account for this. Alternatively, setup a PHP user and do all of this that way (which I won't cover). Please run these commands from where you cloned the git repo:

```
chown -R apache:apache oz2slack
chmod +x oz2slack/check.sh
ln -s oz2slack/pubdate.txt ~/pubdate.txt
ln -s oz2slack/ozxml.xml ~/ozxml.xml
ln -s oz2slack/ozb.xml ~/ozb.xml
ln -s oz2slack/failed.txt ~/failed.txt
```

## Built With

* PHP 7.3

## Acknowledgments

* The people at Hostopia AU that have helped me get this project done, whether little or small feedback