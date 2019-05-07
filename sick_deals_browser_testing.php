<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sick Testing</title>
</head>
</html>

<!--
    This is a testing script to scrape the OzBargain RSS Feed and send the data to Slack via an incoming webhook. This script provides verbose output and should be uses in browser calls
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
    echo "<h3>Checking if</h3><i>$pubDate</i><br><strong>is older than, or the same date as</strong><br><i>$lastPubDate</i>";
    if(strtotime($pubDate) <= strtotime($lastPubDate)) {
        echo "<h3>Breaking, Because it is!</h3>";
        echo "Title = $title";
        break;
    } else {
        echo "<h3>Continuing, Because it isn't...</h3>";

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
        echo var_dump($result);

        // Some error handling and logging of curl calls
        if (($result != "ok") || ($result === false)) {
            logErrors($ch,$title,$link,$description,$category,$categoryLink,$comments,$image,$dealer);
        }
        curl_close($ch);

        // Echoing output for testing
        echo "<br><br>" . "<b>title = </b>" . $title . "<br>";
        echo "<b>link = </b>" . $link . "<br>";
        echo "<b>Description = </b>" . $description . "<br>";
        echo "<b>category = </b>" . $category . "<br>";
        echo "<b>categoryLink = </b>" . $categoryLink . "<br>";
        echo "<b>image http link = </b>" . $image . "<br>";
        echo "<b>Dealer = </b>" . $dealer . "<br>";
        echo "<b>actual displayed image = </b>" . "<img src='$image' alt='error'><br><br>";
        echo "<b>Full JSON Payload Dump = </b>" . json_encode($payload) . "<br><br>";
        echo "<b>Full SickDeals XML Payload Dump = </b>";
        var_dump($ozbargainXml);
        echo "<br><br>";
        var_dump($sickData);
        echo "<br><br><hr><hr>";
    }
}

replacePubDate();