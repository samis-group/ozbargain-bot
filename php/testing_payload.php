<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Testing Failed OzB Payloads</title>
</head>
</html>

<!--
    This is a script to test failed OzB payloads from failed.txt
-->

<?php

include 'hooks.php';
include 'functions.php';
include 'vars.php';

$sickData = $xmlOzB->channel->item;

$title = replaceStrTitle($sickData->title);
$link = replaceStr($sickData->link);
$descriptionLong = html_entity_decode(strip_tags($sickData->description), ENT_QUOTES | ENT_HTML5);
$description = replaceStr(substr($descriptionLong,0,200));
$category = replaceStr($sickData->category);
$categoryLink = replaceStr($sickData->category['domain']);

// Images are apparently optional (thanks OZB feed). so we need to check it's existence before calling "attributes" function on a non-object, otherwise, error on these two tags and script breaks!
if(isset($sickData->children($nsMedia)->thumbnail[0])) {
    $image = replaceStr($sickData->children($nsMedia)->thumbnail[0]->attributes());
} else {
    $image = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png";
}
if(isset($sickData->children($nsOzb)->meta[0])) {
    $dealer = $sickData->children($nsOzb)->meta[0]->attributes()->link;
}

$payload = [
    "blocks" => [
        [
            "type" => "divider"
        ],
        [
            "type" => "context",
            "elements" => [
                [
                    "type" => "image",
                    "image_url" => "$image",
                    "alt_text" => "Images"
                ],
                [
                "type" => "mrkdwn",
                "text" => "Category | <$categoryLink|*$category*>"
                ]
            ]
        ],
        [
            "type" => "section",
            "text" => [
                "type" => "mrkdwn",
                "text" => "<$link|*$title*>"
            ],
        ],
        [
            "type" => "section",
            "text" => [
                "type" => "mrkdwn",
                "text" => "```$description \n\n ... <$link|*_See More_*>```",
            ],
            "accessory" => [
                "type" => "image",
                "image_url" => "$image",
                "alt_text" => "$title"
            ]
        ],
        [
            "type" => "actions",
            "elements" => [
                [
                    "type" => "button",
                    "text" => [
                        "type" => "plain_text",
                        "text" => "View OzB Page"
                    ],
                    "style" => "primary",
                    "url" => "$link"
                ],
                [
                    "type" => "button",
                    "text" => [
                        "type" => "plain_text",
                        "text" => "Grab Deal"
                    ],
                    "url" => "$dealer"
                ]
            ]

        ],
    ],
];

// Adding payload tag to be sent via curl
$data = "payload=" . json_encode($payload);

// Sending data via Curl
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $testHook);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
$result = curl_exec($ch);
echo var_dump($result);
curl_close($ch);

// Echoing output for testing
echo "<br><br>" . "<b>title = </b>" . $title . "<br>";
echo "<b>category = </b>" . $category . "<br>";
echo "<b>categoryLink = </b>" . $categoryLink . "<br>";
echo "<b>image http link = </b>" . $image . "<br>";
echo "<b>link = </b>" . $link . "<br>";
echo "<b>Description = </b>" . "$description" . "<br>";
echo "<b>Dealer Link = </b>" . $dealer . "<br>";
echo "<b>actual displayed image = </b>" . "<img src='$image' alt='error'><br><br>";
echo "<b>Full JSON Payload Dump = </b>" . json_encode($payload) . "<br><br>";
echo "<b>Full SickDeals XML Payload Dump = </b>";
var_dump($xmlSickFeed);
echo "<br><br><hr><hr>";
