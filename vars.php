<?php

// Storing variables that don't change

$sickFeed = "https://www.ozbargain.com.au/deals/feed";
$xmlSickFeed = new SimpleXMLElement($sickFeed, null, true);
$xmlOzB = simplexml_load_file("ozb.xml", null, true);
$ozbargainXml = simplexml_load_file("ozxml.xml", null, true);

$pubDateFile = 'pubdate.txt';

$nsMedia = "http://search.yahoo.com/mrss/";
$nsOzb = "https://www.ozbargain.com.au";