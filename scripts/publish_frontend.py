"""Upload only the storefront's public files and refresh its CloudFront cache."""
import json
import mimetypes
import subprocess
from pathlib import Path

root = Path(__file__).parents[1]
region = "us-east-1"
stack_name = "fieldnote-store"
raw = subprocess.check_output([
    "aws", "cloudformation", "describe-stacks", "--stack-name", stack_name,
    "--region", region, "--query", "Stacks[0].Outputs", "--output", "json", "--no-cli-pager",
], text=True)
outputs = {row["OutputKey"]: row["OutputValue"] for row in json.loads(raw)}
bucket = outputs["FrontendBucketName"]
files = ["index.html", "styles.css", "app.js", "cloud.js", "config.js"]
for relative_path in files:
    path = root / relative_path
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    subprocess.run([
        "aws", "s3", "cp", str(path), f"s3://{bucket}/{relative_path}",
        "--region", region, "--content-type", content_type,
        "--cache-control", "no-cache", "--no-cli-pager",
    ], check=True)
subprocess.run([
    "aws", "cloudfront", "create-invalidation", "--distribution-id", outputs["CloudFrontDistributionId"],
    "--paths", "/*", "--region", region, "--no-cli-pager",
], check=True)
print(f"Published {len(files)} frontend files to s3://{bucket} and invalidated CloudFront.")
