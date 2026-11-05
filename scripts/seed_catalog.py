"""Load the demo catalog into a deployed Products DynamoDB table."""
import json
import os
from decimal import Decimal
from pathlib import Path

import boto3

table_name = os.environ.get("PRODUCTS_TABLE")
if not table_name:
    raise SystemExit("Set PRODUCTS_TABLE to the table name from the SAM stack outputs.")
items = json.loads((Path(__file__).parents[1] / "backend" / "products.json").read_text(), parse_float=Decimal)
table = boto3.resource("dynamodb").Table(table_name)
with table.batch_writer() as batch:
    for item in items:
        item["price"] = Decimal(str(item["price"]))
        batch.put_item(Item=item)
print(f"Loaded {len(items)} catalog products into {table_name}.")
