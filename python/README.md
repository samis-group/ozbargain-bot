# Setup

```shell
sam build --use-container
sam deploy --stack-name ozbargainbot --region ap-southeast-2 --s3-bucket <some_bucket> --capabilities CAPABILITY_IAM
```

This script requires the use of AWS SSM Parameters store to store timestamp data. Change this to a local file if you want to run it that way on your local machine.

If deploying the sam template, make sure you go into SSM and add the parameters inside the template (i.e. `/ozbargain/curl_cookie`, `/ozbargain/slack_webhook` and `/ozbargain/timestamp`) in parameter store.

Also, if using params store, ensure the environment variables point to the above keys (i.e. they are suffix'ed with **'_PARAMETER'**, e.g. `OZBARGAIN_CURL_COOKIE_PARAMETER`), or alternatively update the environment variables in the lambda after deploying the app with the following:

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
OZBARGAIN_CURL_COOKIE_PARAMETER = "/ozbargain/curl_cookie"
OZBARGAIN_SLACK_WEBHOOK_PARAMETER= "/ozbargain/slack_webhook"
OZBARGAIN_TIMESTAMP_PARAMETER = "/ozbargain/timestamp"
VERBOSE = "false"
```

If not using params store, hard code them in the environment vars without the **_PARAMETER** suffix:

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
OZBARGAIN_CURL_COOKIE = "PHPSESSID=XXXXXXXXXXXXXX; _ga=XXXXXXXXXXXXXXX"
OZBARGAIN_SLACK_WEBHOOK = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_TIMESTAMP_PARAMETER = "/ozbargain/timestamp"
VERBOSE = "false"
```

The following should be set if you're testing locally:

```shell
AWS_REGION = "ap-southeast-2"
XML_FILE = "/root/feed"     # Specify an optional path to an xml file you want to load for testing. Leave blank if you want to hit ozbargain feed.
TIMESTAMP_OVERRIDE = "1"    # If you want to override the timestamp that is set and get in ssm parameter.
```
