# Setup

```shell
sam build --use-container
sam deploy --stack-name ozbargainbot --region ap-southeast-2 --s3-bucket <some_bucket> --capabilities CAPABILITY_IAM
```

This script requires the use of AWS SSM Parameters store to store timestamp data. Change this to a local file if you want to run it that way on your local machine.

If deploying the sam template, make sure you go in and update the environment variables and ensure you've got the following:

```shell
# Grab this from your browser making a request to the "https://www.ozbargain.com.au/deals/" page, open up devtools and look for the Request Header "Cookie" on the main /deals/ endpoint and grab everything in that header value starting with 'PHPSESSID='.
CURL_COOKIE = "PHPSESSID=XXXXXXXXXXXXXX; _ga=XXXXXXXXXXXXXXX"
SLACK_WEBHOOK = "https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXXXX"
OZBARGAIN_TIMESTAMP_PARAMETER = "/ozbargain/timestamp"
VERBOSE = "false"
```

The following should be set if you're testing locally:

```shell
AWS_REGION = "ap-southeast-2"
```
