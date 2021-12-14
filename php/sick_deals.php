<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sick Deals</title>
</head>
</html>

<!--
    This is a script to scrape the OzBargain RSS Feed and send the data to Slack via an incoming webhook. Set this script up to run on a cron every 2-5 or so minutes
-->

<?php

require 'hooks.php';
// require '../slack/hooks.php';
require 'functions.php';
require 'vars.php';

getXmlData();

foreach($ozbargainXml->channel->item as $sickData) {

    // First assign variables to the RSS feed data and replace unicode characters
    $title = replaceStrTitle($sickData->title);
    $link = replaceStr($sickData->link);
    $descriptionLong = html_entity_decode(strip_tags($sickData->description), ENT_QUOTES | ENT_HTML5);
    $description = replaceStr(substr($descriptionLong,0,200));
    $category = replaceStr($sickData->category);
    $categoryLink = replaceStr($sickData->category['domain']);
    $comments = replaceStr($sickData->comments);
    $pubDate = $sickData->pubDate;

    // Images are apparently optional (thanks OZB feed). so we need to check it's existence before calling "attributes" function on a non-object, otherwise, error on these two tags and script breaks!
    if(isset($sickData->children($nsMedia)->thumbnail[0])) {
        $image = replaceStr($sickData->children($nsMedia)->thumbnail[0]->attributes());
    } else {
        $image = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png";
    }
    if(isset($sickData->children($nsOzb)->meta[0])) {
        $dealer = $sickData->children($nsOzb)->meta[0]->attributes()->link;
    }

    // Testing the Last Sent date to Slack using pubDate in XML feed, Once it hits this date, it breaks the code completely, then at the end of the code, writes the new date (first date) to this file.
    $lastPubDate = file_get_contents($pubDateFile);
    if(strtotime($pubDate) <= strtotime($lastPubDate)) {
        break;
    } else {
        $payload = readyPayload($title,$link,$description,$category,$categoryLink,$comments,$image,$dealer);

        // Adding data tag to be sent via curl
        $data = "payload=" . json_encode($payload);

        // Sending payload via Curl
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $testHook);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        $result = curl_exec($ch);

        // Some error handling and logging of curl calls
        if (($result != "ok") || ($result === false)) {
            logErrors($ch,$title,$link,$description,$category,$categoryLink,$comments,$image,$dealer);
        }
        curl_close($ch);
    }
}

replacePubDate();