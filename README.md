# Ozbargain Bot

This bot can post to both discord and slack and can post both [new deals as they come in from here](https://www.ozbargain.com.au/deals), and it can post deals that reach [the frontpage of ozbargain here](https://www.ozbargain.com.au/).

You can configure it to post these to two separate webhooks allowing you to simultaneously post both of these deal pages in one app deployment, or you can configure the app to only post one of these.

This can post to both **discord and slack**.

Python code can be built in both **AWS** or on a **linux machine**.

## Initial Setup

### Slack

Obtain the Slack webhook from the [slack app page here.](https://api.slack.com/apps)

### Discord

Obtain the Discord webhook [in the app](https://discord.com/app) by right clicking your server, then click "Server settings" > Integrations.

## Docker Deployment

To deploy this in docker:

```shell
make setup
make build
export OZBARGAIN_SLACK_WEBHOOK=https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXX
make run
```

docker-compose example:

```yaml
---
version: "3.7"
services:
  
```

## Deploy to AWS

This script requires the use of AWS SSM Parameters store to store timestamp data. We'll also use SAM to deploy this so make sure that's all installed and configured in your local environment.

Make sure you go into **SSM parameters store**, and add the parameters and associated **values** for the below (e.g. `/ozbargain/slack_webhook`, `/ozbargain/timestamp` etc.).

AWS Environment variables will look like this as the value points to an SSM params store key and the app will get the value of *that* key in SSM parameter store (i.e. env var -> ssm param key -> value of key in ssm param):

```shell
OZBARGAIN_TIMESTAMP_PARAMETER = "/ozbargain/timestamp"
OZBARGAIN_TIMESTAMP_FRONTPAGE_PARAMETER = "/ozbargain/timestamp_frontpage"
OZBARGAIN_SLACK_WEBHOOK_PARAMETER = "/ozbargain/slack_webhook"
OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE_PARAMETER = "/ozbargain/slack_webhook_frontpage"
OZBARGAIN_DISCORD_WEBHOOK_PARAMETER = "/ozbargain/discord_webhook"
OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE_PARAMETER = "/ozbargain/discord_webhook_frontpage"
OZBARGAIN_AWS_REGION = "ap-southeast-2"
```

In SSM, your parameters values will look like:

```shell
/ozbargain/slack_webhook = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
/ozbargain/slack_webhook_frontpage = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
/ozbargain/discord_webhook = "https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
/ozbargain/discord_webhook_frontpage = "https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
/ozbargain/timestamp = "1"    # This will be overwritten each time the app runs, just initialize it with whatever value for now.
/ozbargain/timestamp_frontpage = "1"    # This will be overwritten each time the app runs, just initialize it with whatever value for now.
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

## Deploy to Linux Instance

Hard code the values for these keys in the environment variables without the **_PARAMETER** suffix (you can use a file to record/get timestamp):

```shell
OZBARGAIN_SLACK_WEBHOOK = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_DISCORD_WEBHOOK = "https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE = "https://discord.com/api/webhooks/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_TIMESTAMP_FILE = "/path/to/file/oz2slack.timestamp"
OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE = "/path/to/file/oz2slack.timestamp.frontpage"
```

## Optional Variables

The following can optionally be set depending on your use case or for testing purposes:

```shell
OZBARGAIN_VERBOSE = "true"
OZBARGAIN_XML_FILE = "/path/to/file/feed"     # Specify an optional path to an xml file you want to load for testing. Remove this environment variable if you want to hit the ozbargain page.
OZBARGAIN_XML_FILE_FRONTPAGE = "/path/to/file/feed"     # Specify an optional path to an xml file you want to load for testing. Remove this environment variable if you want to hit the ozbargain page.
OZBARGAIN_TIMESTAMP_OVERRIDE = "1"    # If you want to override the timestamp that is set and get in ssm parameter/env.
OZBARGAIN_AWS_PROFILE = "default"     # Set the AWS profile that you want to use for the SSM calls (This isn't needed when it's deployed to AWS prod, mainly for local testing as the deployed code will have a policy already).
```
