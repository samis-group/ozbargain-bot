<?php

require 'vars.php';

function replaceStr($str) {
    // Function to Search and Replace Arrays for encoding Unicode Characters so Slack can interpret them
    $replaceFrom = ["&", "<", ">"];
    $replaceTo = [urlencode("&"), urlencode("<"), urlencode(">")];
    $replacedStr = str_replace($replaceFrom, $replaceTo, $str);
    return $replacedStr;
}

function replaceStrTitle($str) {
    // Function to Search and Replace Arrays for encoding Unicode Characters so Slack can interpret them
    $replaceFrom = ["&", "<", ">"];
    $replaceTo = [urlencode("&"), urlencode("{"), urlencode("}")];
    $replacedStr = str_replace($replaceFrom, $replaceTo, $str);
    return $replacedStr;
}

function getXmlData() {
    $ch = curl_init();
    $fp = fopen("ozxml.xml", "w");
    global $sickFeed;
    curl_setopt($ch, CURLOPT_HTTPHEADER, array(
        'cache-control: max-age=0',
        'cookie: G_ENABLED_IDPS=google; <INSERT_SESSION_ID>'
    ));
    curl_setopt($ch, CURLOPT_URL, $sickFeed);
    curl_setopt($ch, CURLOPT_FILE, $fp);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);

    $xmlContents = curl_exec ($ch);
    fwrite($fp, $xmlContents);
    
    curl_close ($ch);
    fclose($fp);
}

function replacePubDate() {
    global $ozbargainXml;
    global $pubDateFile;
    $pubDate = $ozbargainXml->channel->item[0]->pubDate;
    file_put_contents($pubDateFile, $pubDate);
}

function logErrors($ch,$title,$link,$description,$category,$categoryLink,$comments,$image,$dealer) {
    $payload = readyPayload($title,$link,$description,$category,$categoryLink,$comments,$image,$dealer);
    echo 'Curl error: ' . curl_error($ch);
    $failedFile = 'failed.txt';
    $handle = fopen($failedFile, 'a') or die('Cannot open file:  '.$failedFile);
    $data = "This payload FAILED TO SEND TO SICK DEALS, Please investigate: \n\n" . curl_error($ch) . "\n\n";
    $data .= "title = " . $title . "\n";
    $data .= "link = " . $link . "\n";
    $data .= "Description = " . "$description" . "\n";
    $data .= "category = " . $category . "\n";
    $data .= "categoryLink = " . $categoryLink . "\n";
    $data .= "image = " . $image . "\n";
    $data .= "Dealer = " . $dealer . "\n";
    $data .= "Full JSON Payload Dump:\n\n" . json_encode($payload) . "\n\n";
    $data .= "Full SickDeals XML:\n\n";
    ob_start();
    var_dump($ozbargainXml);
    $data2 = ob_get_clean();
    $data3 = "\n\n------------------------------------------------------------------------------------------------------------\n\n\n";
    fwrite($handle, $data);
    fwrite($handle, $data2);
    fwrite($handle, $data3);
    fclose($handle);
}

function readyPayload($title,$link,$description,$category,$categoryLink,$comments,$image,$dealer) {
// Payload Data Array that will be converted to JSON and sent via Curl
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
                "text" => "```$description...```",
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
                ],
                [
                    "type" => "button",
                    "text" => [
                        "type" => "plain_text",
                        "text" => "Comments"
                    ],
                    "style" => "danger",
                    "url" => "$comments"
                ]
            ]
        ],
    ],
];

return $payload;
}