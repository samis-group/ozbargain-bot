# Ozbargain Bot

## Initial Setup

### Slack

Obtain the Slack webhook from the [slack app page here.](https://api.slack.com/apps)

### Discord

Obtain the Discord webhook [in the app](https://discord.com/app) by right clicking your server, then click "Server settings" > Integrations.

### AWS

This script requires the use of AWS SSM Parameters store to store timestamp data. We'll also use SAM to deploy this so make sure that's all installed and configured.

Make sure you go into SSM and add the values for the parameters inside the template (i.e. `/ozbargain/curl_cookie`, `/ozbargain/slack_webhook` and `/ozbargain/timestamp`) in parameter store.

## Deploy

Steps to deploy it to either AWS or a linux machine.

### Deploy to AWS

AWS Environment variables will look like this as the value points to an SSM params store key and it will get the value of *that* key in SSM parameter store:

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
OZBARGAIN_CURL_COOKIE_PARAMETER = "/ozbargain/curl_cookie"
OZBARGAIN_SLACK_WEBHOOK_PARAMETER= "/ozbargain/slack_webhook"
OZBARGAIN_DISCORD_WEBHOOK_PARAMETER= "/ozbargain/discord_webhook"
OZBARGAIN_TIMESTAMP_PARAMETER = "/ozbargain/timestamp"
OZBARGAIN_AWS_REGION = "ap-southeast-2"
```

The [template.yaml](template.yaml) file is configured to deploy the above environment variables for you. Change as desired.

Now let's build and deploy the app (*Replace `some_bucket` with a bucket of your choosing*):

```shell
# First specify the credentials you will be using if it is not "default" (ensure aws cli is setup and/or tokens are generated):
export AWS_PROFILE="PROFILE_NAME"

# Now build and deploy the image
sam build --use-container
sam deploy --stack-name ozbargainbot --region ap-southeast-2 --s3-bucket <some_bucket> --capabilities CAPABILITY_IAM
```

### Deploy to Linux Instance

If not deploying this to AWS, hard code the values for these in the environment variables without the **_PARAMETER** suffix (you can use a file to record/get timestamp):

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
OZBARGAIN_CURL_COOKIE = "PHPSESSID=XXXXXXXXXXXXXX; _ga=XXXXXXXXXXXXXXX"
OZBARGAIN_SLACK_WEBHOOK = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_DISCORD_WEBHOOK = "https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_TIMESTAMP_FILE = "/path/to/file/oz2slack.timestamp"
```

### Optional Variables

The following can optionally be set depending on your use case or for testing purposes:

```shell
VERBOSE = "true"
XML_FILE = "/path/to/file/feed"     # Specify an optional path to an xml file you want to load for testing. Leave blank if you want to hit ozbargain feed.
TIMESTAMP_OVERRIDE = "1"    # If you want to override the timestamp that is set and get in ssm parameter.
AWS_PROFILE = "default"     # Set the AWS profile that you want to use for the SSM calls.
```
