# Setup

Obtain the slack webhook from [the slack app page here.](https://api.slack.com/apps)

## Deploy to AWS

This script requires the use of AWS SSM Parameters store to store timestamp data. We'll also use SAM to deploy this.

Make sure you go into SSM and add the values for the parameters inside the template (i.e. `/ozbargain/curl_cookie`, `/ozbargain/slack_webhook` and `/ozbargain/timestamp`) in parameter store (or whatever value you specified in your env for these parameters), so that it looks like this:

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
OZBARGAIN_CURL_COOKIE_PARAMETER = "/ozbargain/curl_cookie"
OZBARGAIN_SLACK_WEBHOOK_PARAMETER= "/ozbargain/slack_webhook"
OZBARGAIN_TIMESTAMP_PARAMETER = "/ozbargain/timestamp"
AWS_REGION = "ap-southeast-2"
```

Now build and deploy the app:

```shell
sam build --use-container
sam deploy --stack-name ozbargainbot --region ap-southeast-2 --s3-bucket <some_bucket> --capabilities CAPABILITY_IAM
```

## Deploy to Linux Instance

If not deploying this to AWS, hard code the values for these in the environment variables without the **_PARAMETER** suffix (you can use a file to record/get timestamp):

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
OZBARGAIN_CURL_COOKIE = "PHPSESSID=XXXXXXXXXXXXXX; _ga=XXXXXXXXXXXXXXX"
OZBARGAIN_SLACK_WEBHOOK = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_TIMESTAMP_FILE = "/path/to/file/oz2slack.timestamp"
```

## Optional Variables

The following can optionally be set depending on your use case or for testing purposes:

```shell
VERBOSE = "false"
XML_FILE = "/path/to/file/feed"     # Specify an optional path to an xml file you want to load for testing. Leave blank if you want to hit ozbargain feed.
TIMESTAMP_OVERRIDE = "1"    # If you want to override the timestamp that is set and get in ssm parameter.
```
