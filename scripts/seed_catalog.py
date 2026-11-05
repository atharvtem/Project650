"""Load the demo catalog into a deployed Products DynamoDB table via AWS CLI."""
import json
import os
import subprocess
from decimal import Decimal
from pathlib import Path

table_name = os.environ.get("PRODUCTS_TABLE")
if not table_name:
    raise SystemExit("Set PRODUCTS_TABLE to the table name from the SAM stack outputs.")
items = json.loads((Path(__file__).parents[1] / "backend" / "products.json").read_text(), parse_float=Decimal)
region = os.environ.get("AWS_REGION", "us-east-1")


def attribute(value):
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, str):
        return {"S": value}
    if isinstance(value, (int, float, Decimal)):
        return {"N": str(value)}
    if isinstance(value, list):
        return {"L": [attribute(v) for v in value]}
    if isinstance(value, dict):
        return {"M": {k: attribute(v) for k, v in value.items()}}
    raise TypeError(f"Unsupported DynamoDB catalog value: {type(value).__name__}")


for item in items:
    subprocess.run([
        "aws", "dynamodb", "put-item",
        "--table-name", table_name,
        "--region", region,
        "--no-cli-pager",
        "--item", json.dumps({key: attribute(value) for key, value in item.items()}),
    ], check=True)
print(f"Loaded {len(items)} catalog products into {table_name}.")
