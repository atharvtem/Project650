"""Write non-secret browser configuration from the deployed SAM stack outputs."""
import json
import subprocess
from pathlib import Path

region = "us-east-1"
stack_name = "fieldnote-store"
raw = subprocess.check_output([
    "aws", "cloudformation", "describe-stacks",
    "--stack-name", stack_name,
    "--region", region,
    "--query", "Stacks[0].Outputs",
    "--output", "json",
    "--no-cli-pager",
], text=True)
outputs = {row["OutputKey"]: row["OutputValue"] for row in json.loads(raw)}
config = {
    "region": region,
    "apiUrl": outputs["ApiUrl"],
    "userPoolId": outputs["UserPoolId"],
    "userPoolClientId": outputs["UserPoolClientId"],
    "cognitoDomain": outputs["CognitoHostedUiUrl"],
    "websiteUrl": outputs.get("WebsiteUrl", ""),
    "distributionId": outputs.get("CloudFrontDistributionId", ""),
}
Path(__file__).parents[1].joinpath("config.js").write_text(
    "window.FIELDNOTE_CONFIG = " + json.dumps(config, indent=2) + ";\n")
print("Wrote config.js with non-secret Fieldnote stack outputs.")
