"""HTTP API for the Fieldnote demo storefront."""
import json
import os
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr, Key

dynamodb = boto3.resource("dynamodb")
products_table = dynamodb.Table(os.environ["PRODUCTS_TABLE"])
user_data_table = dynamodb.Table(os.environ["USER_DATA_TABLE"])
bedrock = boto3.client("bedrock-runtime")
CHAT_MODEL_ID = os.environ.get("CHAT_MODEL_ID", "")


def json_safe(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value


def response(status, body):
    return {"statusCode": status, "headers": {"content-type": "application/json"}, "body": json.dumps(json_safe(body))}


def body_json(event):
    try:
        return json.loads(event.get("body") or "{}")
    except (TypeError, json.JSONDecodeError):
        raise ValueError("Request body must be valid JSON.")


def owner_id(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    # Cognito's verified subject is the only account key accepted by this API.
    return claims.get("sub")


def list_products(event):
    result = products_table.scan(FilterExpression=Attr("active").eq(True))
    rows = result.get("Items", [])
    while result.get("LastEvaluatedKey"):
        result = products_table.scan(ExclusiveStartKey=result["LastEvaluatedKey"], FilterExpression=Attr("active").eq(True))
        rows.extend(result.get("Items", []))
    query = event.get("queryStringParameters") or {}
    category = query.get("category", "")
    search = query.get("search", "").lower().strip()
    min_price = float(query.get("minPrice", 0) or 0)
    max_price = float(query.get("maxPrice", "inf") or "inf")
    rows = [p for p in rows if (not category or p.get("category") == category)
            and min_price <= float(p.get("price", 0)) <= max_price
            and (not search or search in " ".join(str(p.get(k, "")) for k in ("name", "category", "description", "color")).lower())]
    return response(200, {"products": sorted(rows, key=lambda p: p["productId"])})


def get_cart(user_id):
    item = user_data_table.get_item(Key={"userId": user_id, "sk": "CART"}).get("Item")
    return item or {"userId": user_id, "sk": "CART", "items": {}}


def cart_payload(cart):
    result = []
    for product_id, quantity in cart.get("items", {}).items():
        product = products_table.get_item(Key={"productId": product_id}).get("Item")
        if product and product.get("active") and int(quantity) > 0:
            result.append({"product": product, "quantity": int(quantity)})
    return {"items": result, "count": sum(row["quantity"] for row in result),
            "subtotal": sum(float(row["product"]["price"]) * row["quantity"] for row in result)}


def update_cart(user_id, product_id, quantity):
    product = products_table.get_item(Key={"productId": product_id}).get("Item")
    if not product or not product.get("active"):
        return response(404, {"error": "Product not found."})
    cart = get_cart(user_id)
    items = cart.get("items", {})
    if quantity <= 0:
        items.pop(product_id, None)
    else:
        items[product_id] = quantity
    user_data_table.put_item(Item={"userId": user_id, "sk": "CART", "items": items, "updatedAt": datetime.now(timezone.utc).isoformat()})
    return response(200, cart_payload({"items": items}))


def checkout(user_id):
    cart = get_cart(user_id)
    lines = []
    total = Decimal("0")
    for product_id, raw_qty in cart.get("items", {}).items():
        qty = int(raw_qty)
        if qty < 1 or qty > 99:
            return response(400, {"error": "Each item quantity must be between 1 and 99."})
        product = products_table.get_item(Key={"productId": product_id}).get("Item")
        if not product or not product.get("active"):
            return response(409, {"error": "A product in your cart is no longer available."})
        price = Decimal(str(product["price"]))
        total += price * qty
        lines.append({"productId": product_id, "name": product["name"], "price": price, "quantity": qty})
    if not lines:
        return response(400, {"error": "Your cart is empty."})
    now = datetime.now(timezone.utc).isoformat()
    order_id = str(uuid.uuid4())[:8].upper()
    order = {"userId": user_id, "sk": f"ORDER#{now}#{order_id}", "orderId": order_id, "createdAt": now,
             "items": lines, "total": total, "status": "SIMULATED"}
    # Store the immutable order snapshot and clear its cart as one atomic write.
    dynamodb.meta.client.transact_write_items(TransactItems=[
        {"Put": {"TableName": user_data_table.name, "Item": {k: _av(v) for k, v in order.items()}}},
        {"Put": {"TableName": user_data_table.name, "Item": {k: _av(v) for k, v in {"userId": user_id, "sk": "CART", "items": {}, "updatedAt": now}.items()}}},
    ])
    return response(201, {"order": order})


def _av(value):
    from boto3.dynamodb.types import TypeSerializer
    return TypeSerializer().serialize(value)


def list_orders(user_id):
    result = user_data_table.query(KeyConditionExpression=Key("userId").eq(user_id) & Key("sk").begins_with("ORDER#"), ScanIndexForward=False)
    return response(200, {"orders": result.get("Items", [])})


def chat(user_id, question):
    question = question.strip()
    if not question or len(question) > 500:
        return response(400, {"error": "Ask a question between 1 and 500 characters."})
    day = datetime.now(timezone.utc).date().isoformat()
    throttle_key = {"userId": user_id, "sk": f"CHAT#{day}"}
    try:
        result = user_data_table.update_item(Key=throttle_key, UpdateExpression="ADD #n :one", ExpressionAttributeNames={"#n": "requests"}, ExpressionAttributeValues={":one": 1}, ReturnValues="UPDATED_NEW")
        if int(result["Attributes"]["requests"]) > 20:
            return response(429, {"error": "Daily chat limit reached. Please try again tomorrow."})
    except Exception:
        return response(503, {"error": "Chat is temporarily unavailable."})
    result = products_table.scan(FilterExpression=Attr("active").eq(True))
    catalog = result.get("Items", [])
    words = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 2}
    ranked = sorted(catalog, key=lambda p: sum(1 for w in words if w in (p.get("name", "") + " " + p.get("category", "") + " " + p.get("description", "") + " " + " ".join(p.get("details", []))).lower()), reverse=True)
    numeric = re.search(r"(?:under|below|less than)\s+\$?(\d+)", question.lower())
    relevant = [p for p in ranked if (not numeric or float(p["price"]) <= float(numeric.group(1)))][:5]
    if not relevant or not any(words.intersection(set(re.findall(r"[a-z0-9]+", (p.get("name", "") + " " + p.get("category", "") + " " + p.get("description", "")).lower()))) for p in relevant):
        return response(200, {"answer": "I could not find a clear match in our collection for that yet. Try a category, material, or budget and I can look again.", "products": []})
    context = [{k: p.get(k) for k in ("name", "category", "price", "color", "description", "details")} for p in relevant]
    prompt = ("You are Fieldnote's product guide. Answer only from the catalog records below. Never invent stock, materials, features, or prices. "
              "If the records do not support an answer, say so. Keep the answer concise and name prices for recommendations.\n\n"
              f"CATALOG RECORDS:\n{json.dumps(json_safe(context))}\n\nSHOPPER QUESTION:\n{question}")
    try:
        result = bedrock.invoke_model(modelId=CHAT_MODEL_ID, contentType="application/json", accept="application/json",
            body=json.dumps({"messages": [{"role": "user", "content": [{"text": prompt}]}],
                             "inferenceConfig": {"maxTokens": 220, "temperature": 0.2}}))
        answer = json.loads(result["body"].read())["output"]["message"]["content"][0]["text"]
        return response(200, {"answer": answer, "products": context})
    except Exception:
        return response(503, {"error": "The product guide is temporarily unavailable."})


def handler(event, _context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    user_id = owner_id(event)
    try:
        if method == "GET" and path == "/products":
            return list_products(event)
        if not user_id:
            return response(401, {"error": "Sign in to continue."})
        if method == "GET" and path == "/cart":
            return response(200, cart_payload(get_cart(user_id)))
        if method == "POST" and path == "/cart/items":
            data = body_json(event)
            product_id = str(data.get("productId", ""))
            quantity = int(data.get("quantity", 1))
            if not product_id or not 1 <= quantity <= 99:
                return response(400, {"error": "Provide a product ID and quantity from 1 to 99."})
            current = int(get_cart(user_id).get("items", {}).get(product_id, 0))
            return update_cart(user_id, product_id, min(99, current + quantity))
        if path.startswith("/cart/items/") and method in ("PUT", "DELETE"):
            product_id = path.rsplit("/", 1)[-1]
            quantity = 0 if method == "DELETE" else int(body_json(event).get("quantity", 0))
            if quantity < 0 or quantity > 99:
                return response(400, {"error": "Quantity must be between 0 and 99."})
            return update_cart(user_id, product_id, quantity)
        if method == "GET" and path == "/orders":
            return list_orders(user_id)
        if method == "POST" and path == "/orders":
            return checkout(user_id)
        if method == "POST" and path == "/chat":
            return chat(user_id, str(body_json(event).get("question", "")))
        return response(404, {"error": "Route not found."})
    except ValueError as exc:
        return response(400, {"error": str(exc)})
    except Exception:
        # Do not expose internal errors or user data in API responses.
        return response(500, {"error": "Something went wrong. Please try again."})
