# AWS deployment handoff

## Deployed status

The `fieldnote-store` stack is deployed in `us-east-1`. It currently includes Cognito, API Gateway, Lambda, two on-demand DynamoDB tables, a private S3 frontend bucket, and CloudFront. The 15 sample products are loaded.

- Storefront: https://d29smamqrn6vkt.cloudfront.net/
- Public catalog API: https://jamjl4xlnk.execute-api.us-east-1.amazonaws.com/products
- Cognito sign-in is served through the user pool's hosted UI.

The website and public catalog endpoint have returned HTTP 200. The remaining deployment check is a user-driven sign-up and authenticated end-to-end flow. The demo account and chat should then be checked in the browser.

## User step: create a test account

Open the storefront, select **Sign in**, then choose **Sign up** on the Cognito page. Complete the email verification code sent to you. Keep your password and verification code private; they are entered directly into AWS Cognito's hosted page, not into this chat. After sign-in, try adding a product to the bag, refreshing the page, placing a simulated order, checking order history, and asking the assistant a catalog question.

## Account and cost ownership

The project owner controls AWS account access. Before future deployments, confirm:

1. The intended account and region (`us-east-1`) are still selected.
2. The $5 monthly budget alert remains active. It sends an alert but does not stop spending.
3. AWS CLI and SAM are installed and authenticated locally. Never send access keys in chat or commit them.
4. Amazon Nova Lite (`amazon.nova-lite-v1:0`) is the configured chat model. The first Bedrock invocation may reveal account-specific model availability or permissions.
5. Review the CloudFormation change set before applying future stack changes.

I cannot access your AWS sign-in. Enter passwords and email verification codes only in the Cognito page.

## Deploy outline

For a future infrastructure change, from the repository root:

```sh
sam build --template-file infra/template.yaml
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

Keep the existing stack name `fieldnote-store` and region `us-east-1`. The deployed `AllowedOrigin` is the CloudFront website origin. The stack's Cognito callback URLs include both the CloudFront URL and `http://localhost:8000` for local development. Keep generated identifiers in frontend config only; they are not access keys.

After a stack deployment, refresh the browser configuration, seed catalog rows if needed, and publish the frontend files:

```sh
python3 scripts/write_frontend_config.py
AWS_REGION=us-east-1 PRODUCTS_TABLE=<ProductsTableName output> python3 scripts/seed_catalog.py
python3 scripts/publish_frontend.py
```

No real payment data is collected; checkout only writes a simulated order.

## Cleanup

When the class demo is finished, delete the CloudFormation stack and verify the stack resources are gone. DynamoDB tables are intentionally not configured for point-in-time recovery, and the stack does not enable product-image storage, a domain, or a NAT gateway. Review the Billing console for lingering usage and remove the budget alert only if you no longer need it.
