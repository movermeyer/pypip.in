import os
import json

ENDPOINTS = {
    "format": ("format", "A badge describing the format that the Python library is packaged as (ex. wheel, source)"),
    "implementation": ("implementation", "A badge describing the Python implementations that the Python library is developed for (ex. cpython, PyPy)"),
    "license": ("l", "A badge describing the software license that the Python library is packaged as (ex. BSD, MIT)"),
    "py_versions": ("pyversions", "A badge describing the Python versions that the library supports (ex. 2.7, 3.4)"),
    "status": ("status", "A badge describing the development status of the Python library (ex. alpha, stable)"),
    "v": ("v", "A badge describing the version of the Python library. Alias of `version`"),
    "version": ("v", "A badge describing the version of the Python library."),
    "wheel": ("wheel", "A badge describing whether the Python library is packaged as a wheel (ex. yes, no).")
}

BADGE_FORMATS = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "json": "application/json"
}


def vtl_escape(text):
    # AWS Body Mapping Templates use Apache Velocity (VTL) markup.
    # This is a poor man's escaping of special VTL characters
    return text.replace('#', '#[[#]]#').replace('$', '#[[$]]#')


def format_as_template(text):
    return json.dumps(vtl_escape(text.replace('\r', ''))).strip('"').replace('\n', '\\n')


with open("egg_endpoint.txt", 'r', encoding='UTF-8') as fin:
    EGG_HTML = json.dumps(fin.read().replace('\r', '')).strip('"').replace('\n', '\\n')

EGG_ENDPOINT_TEMPLATE = """    "/egg/{{package}}/badge.{badge_format}": {{
      "get": {{
        "tags": [],
        "description": "The /egg endpoint has no analogue in shields.io. You might want /format or /wheel instead.",
        "produces": [
          "text/html"
        ],
        "parameters": [
          {{
            "name": "package",
            "in": "path",
            "description": "The PyPI package to produce the badge for",
            "required": true,
            "type": "string"
          }}
        ],
        "responses": {{
          "404": {{
            "description": "Resource Gone",
            "headers": {{
              "Content-Type": {{
                "type": "string",
                "description": "Media type of request"
              }}
            }}
          }}
        }},
        "x-amazon-apigateway-integration": {{
          "responses": {{
            "default": {{
              "statusCode": "404",
              "responseTemplates": {{
                "text/html": \"""" + EGG_HTML + """\"
              }},
              "responseParameters": {{
                "method.response.header.Content-Type": "'text/html'"
              }}
            }}
          }},
          "passthroughBehavior": "when_no_match",
          "requestTemplates": {{
            "application/json": "{{\\\"statusCode\\\": 200}}"
          }},
          "contentHandling": "CONVERT_TO_TEXT",
          "type": "mock"
        }}
      }}
    }},
"""

JS_TAGS = []
for json_file in (entry for entry in os.scandir(os.path.join("..", "js")) if entry.is_file() and entry.name.endswith(".js")):
    with open(json_file.path, 'r', encoding='UTF-8') as fin:
        JS_TAGS.append(f"""<script type="text/javascript">{fin.read()}</script>""")

CSS_TAGS = []
for css_file in (entry for entry in os.scandir(os.path.join("..", "css")) if entry.is_file() and entry.name.endswith(".css")):
    with open(css_file.path, 'r', encoding='UTF-8') as fin:
        CSS_TAGS.append(f"""<style>{fin.read()}</style>""")

with open(os.path.join("..", "index.html"), 'r', encoding='UTF-8') as fin:
    INDEX_HTML = format_as_template(fin.read().format(styles="\n".join(CSS_TAGS), scripts="\n".join(JS_TAGS)))

HEADER = """
{
  "swagger": "2.0",
  "info": {
    "description": "A recreation of the (shuttered) pypip.in API that uses shields.io instead",
    "title": "pypip.in Replacement API",
    "version": "1.0.0"
  },
  "schemes": [
    "https",
    "http"
  ],
  "paths": {
    "/": {
      "get": {
        "tags": [],
        "description": "The main landing page of the new pypip.in",
        "produces": [
          "text/html"
        ],
        "responses": {
          "200": {
            "description": "OK",
            "headers": {
              "Content-Type": {
                "type": "string",
                "description": "Media type of request"
              }
            }
          }
        },
        "x-amazon-apigateway-integration": {
          "responses": {
            "default": {
              "statusCode": "200",
              "responseTemplates": {
                "text/html": \"""" + INDEX_HTML + """\"
              },
              "responseParameters": {
                "method.response.header.Content-Type": "'text/html'"
              }
            }
          },
          "passthroughBehavior": "when_no_match",
          "requestTemplates": {
            "application/json": "{\\\"statusCode\\\": 200}"
          },
          "contentHandling": "CONVERT_TO_TEXT",
          "type": "mock"
        }
      }
    },
"""

MIME_TYPE_LIST = [f"\"{mime_type}\"" for mime_type in BADGE_FORMATS.values()]
MIDDLE = f"""
  }},
  "definitions": {{}},
  "x-amazon-apigateway-binary-media-types" : [
    {', '.join(MIME_TYPE_LIST)}
  ]
"""

STYLE_PARAM = """,
          {
            "name": "style",
            "in": "query",
            "description": "The style you want to use for the badge (flat is the default as of Feb 1st 2015)",
            "required": false,
            "type": "string"
          }
"""

STYLE_PARAM_MAPPING = """,
            \"integration.request.querystring.style\": \"method.request.querystring.style\""""

CONTENT_HANDLING = """,
              "contentHandling": "CONVERT_TO_BINARY"""

AWS_ENDPOINT_TEMPLATE = """
      {{
        "location": {{
          "type": "METHOD",
          "path": "/format/{{package}}/badge.{badge_format}",
          "method": "GET"
        }},
        "properties": {{
          "tags": [],
          "summary": "{description}"
        }}
      }},
"""

FOOTER = """
}

"""

with open("endpoint_template.txt", 'r') as fin:
    ENDPOINT_TEMPLATE = fin.read()


def main():
    # Generate a Swagger 2.0 file that can be imported into AWS API Gateway.
    # If it seems overly complicated, I would agree.
    # There are a number of things I am working around:
    # - Amazon doesn't support the latest versions of OpenAPI, only Swagger 2.0
    # - Amazon has a bug where you cannot use Swagger's templating of a file's extension (https://forums.aws.amazon.com/thread.jspa?messageID=836050)
    # - shields.io has a bug where sending a valid `style` parameter to their json endpoints causes crashes (https://github.com/badges/shields/issues/1577)

    with open("swagger.json", 'w') as fout:
        fout.write(HEADER)

        for index, badge_format in enumerate(BADGE_FORMATS.keys()):
            fout.write(EGG_ENDPOINT_TEMPLATE.format(badge_format=badge_format))

        total_count = len(ENDPOINTS) * len(BADGE_FORMATS)
        processed_count = 0
        for endpoint, (mapped_endpoint, description) in ENDPOINTS.items():
            for badge_format, result_type in BADGE_FORMATS.items():
                processed_count += 1
                operation_id = f"get-{endpoint}-badge-{badge_format}"
                is_last = "," if processed_count != total_count else ""
                style_param = STYLE_PARAM if badge_format != 'json' else ""
                style_param_mapping = STYLE_PARAM_MAPPING if badge_format != 'json' else ""
                content_handling = CONTENT_HANDLING if badge_format == 'png' else ""
                fout.write(ENDPOINT_TEMPLATE.format(endpoint=endpoint,
                                                    mapped_endpoint=mapped_endpoint,
                                                    badge_format=badge_format,
                                                    description=description,
                                                    operation_id=operation_id,
                                                    result_type=result_type,
                                                    style_param=style_param,
                                                    style_param_mapping=style_param_mapping,
                                                    content_handling=content_handling,
                                                    is_last=is_last))
        fout.write(MIDDLE)
        fout.write(FOOTER)


if __name__ == '__main__':
    main()
