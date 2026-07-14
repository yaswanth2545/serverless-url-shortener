# Serverless URL Shortener

A small, free-tier-friendly cloud project built on AWS:

- **AWS Lambda** — runs the application code (Python)
- **API Gateway** — exposes HTTP endpoints
- **DynamoDB** — stores short-id → long-url mappings
- **AWS SAM** — defines and deploys the infrastructure as code

## Architecture

```
Client ──POST /shorten──▶ API Gateway ──▶ Lambda (create_short_url) ──▶ DynamoDB
Client ──GET  /{id}────▶ API Gateway ──▶ Lambda (redirect_short_url) ──▶ DynamoDB ──▶ 302 redirect
```

## Project structure

```
serverless-url-shortener/
├── src/
│   ├── handler.py        # Lambda function code
│   └── requirements.txt
├── template.yaml          # AWS SAM template (infra as code)
├── .gitignore
└── README.md
```

## Prerequisites

- An AWS account (free tier is enough)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed
- Python 3.12

## Deploy to AWS

```bash
# Build the project
sam build

# Deploy (guided the first time - it will ask for stack name, region, etc.)
sam deploy --guided
```

After deployment, SAM will print an `ApiUrl` output — that's your base API URL.

## Usage

**Shorten a URL:**
```bash
curl -X POST https://<ApiUrl>/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.anthropic.com"}'
```

Response:
```json
{
  "short_id": "aZ3xQ1",
  "short_url": "https://<ApiUrl>/aZ3xQ1",
  "long_url": "https://www.anthropic.com"
}
```

**Visit the short URL** (redirects to the original):
```bash
curl -L https://<ApiUrl>/aZ3xQ1
```

## Local testing (optional)

```bash
sam local start-api
```

Then hit `http://127.0.0.1:3000/shorten` the same way as above.

## Cleanup

To remove all AWS resources created by this project:

```bash
sam delete
```

## Possible extensions

- Add custom short-id aliases
- Add click-count analytics per short URL
- Add an expiry (TTL) on DynamoDB items
- Add a simple frontend (S3 + CloudFront)
