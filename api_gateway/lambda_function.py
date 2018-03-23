import boto3


PYPIP_IN_REGEX_TO_SHIELDS_IO = {
    "format": "format",
    "implementation": "implementation",
    "license": "l",
    "py_versions": "pyversions",
    "status": "status",
    "v": "v",
    "version": "v",
    "wheel": "wheel"
}


def pypip_in_to_shields_io(event):
    query_data = event["queryStringParameters"] or {}
    query_data = [("label", x[1]) if x[0] == "text" else x for x in query_data.items()]

    endpoint = event["path"].split('/')[1]
    package = event["pathParameters"]["package"]
    badge_format = event["path"].split('.')[1]
    shields_path = PYPIP_IN_REGEX_TO_SHIELDS_IO[endpoint]

    if endpoint in ["d", "download"]:
        period = [x[1] for x in query_data if x[0] == "period"]
        query_data = [x for x in query_data if x[0] != "period"]
        if len(period) > 0:
            period = period[0]
            if period == "day":
                shields_path = "dd"
            elif period == "week":
                shields_path = "dw"
            elif period == "month":
                shields_path = "dm"
            else:
                shields_path = "dm"
        else:
            shields_path = "dm"

    query_data = ["=".join(x) for x in query_data]
    query = "&".join(query_data)

    return f"https://img.shields.io/pypi/{shields_path}/{package}.{badge_format}{'?' if query else ''}{query}"



def lambda_handler(event, context):
    headers = event["headers"] or {}
    referer = headers.get("x-amzn-Remapped-Referer") or headers.get("Referer")
    referer_counts = boto3.resource('dynamodb').Table('referer_counts')
    
    referer_counts.update_item(
        Key={
            'url': str(referer),
        },
        UpdateExpression='SET hits = if_not_exists(hits, :initial) + :incr',
        ExpressionAttributeValues={
            ':initial': 0,
            ':incr': 1
        }
    )
    
    out = {}
    out["statusCode"] = 307
    out['body'] = ""
    
    try:
        out['headers'] = { 
            'Location' : pypip_in_to_shields_io(event),
            'Access-Control-Allow-Origin': '*'
        }
    except KeyError:
        raise
        out["statusCode"] = 404
        
    return out
