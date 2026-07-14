import json
import os
import string
import random
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "url-shortener-table")
table = dynamodb.Table(TABLE_NAME)

CHARS = string.ascii_letters + string.digits


def _response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body_dict),
    }


def _generate_short_id(length=6):
    return "".join(random.choice(CHARS) for _ in range(length))


def create_short_url(event, context):
    """POST /shorten  { "url": "https://example.com" }"""
    try:
        body = json.loads(event.get("body") or "{}")
        long_url = body.get("url")

        if not long_url or not long_url.startswith(("http://", "https://")):
            return _response(400, {"error": "Please provide a valid 'url' starting with http:// or https://"})

        # Generate a unique short id, retry on rare collision
        for _ in range(5):
            short_id = _generate_short_id()
            try:
                table.put_item(
                    Item={"short_id": short_id, "long_url": long_url},
                    ConditionExpression="attribute_not_exists(short_id)",
                )
                break
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    continue
                raise
        else:
            return _response(500, {"error": "Could not generate a unique short URL, please try again"})

        host = event.get("headers", {}).get("Host", "")
        stage = event.get("requestContext", {}).get("stage", "")
        base_url = f"https://{host}/{stage}" if host else ""

        return _response(201, {
            "short_id": short_id,
            "short_url": f"{base_url}/{short_id}" if base_url else short_id,
            "long_url": long_url,
        })

    except json.JSONDecodeError:
        return _response(400, {"error": "Request body must be valid JSON"})
    except Exception as e:
        return _response(500, {"error": str(e)})


def redirect_short_url(event, context):
    """GET /{short_id} -> 302 redirect to the original URL"""
    try:
        short_id = event.get("pathParameters", {}).get("short_id")
        if not short_id:
            return _response(400, {"error": "Missing short_id in path"})

        result = table.get_item(Key={"short_id": short_id})
        item = result.get("Item")

        if not item:
            return _response(404, {"error": "Short URL not found"})

        return {
            "statusCode": 302,
            "headers": {"Location": item["long_url"]},
            "body": "",
        }

    except Exception as e:
        return _response(500, {"error": str(e)})
