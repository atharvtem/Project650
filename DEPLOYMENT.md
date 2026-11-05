# AWS deployment handoff

The AWS template in `infra/template.yaml` creates a Cognito user pool and browser client, a public product route, protected cart/order/chat routes, one Python Lambda, and two on-demand DynamoDB tables. The storefront is not wired to these endpoints yet; this file records the deployment setup for the next integration slice.

## Before the first deploy

The project owner will need to:

1. Choose the AWS account and region for the class demo. Use one region for Cognito, Lambda, DynamoDB, and Bedrock.
2. Create an AWS Budget alert in Billing before deploying. A budget alert sends a notification but does not stop usage.
3. Confirm that AWS SAM CLI and AWS credentials are available on the deployment machine. Do not send access keys in chat or commit them.
4. Check Bedrock model availability and enable/request access for the selected model in that region. The default is Claude 3 Haiku; the region/account may require a different model ID or inference profile.
5. Approve the CloudFormation change set when deploying. It creates billable AWS resources.

Those steps need your AWS account and approval. I can prepare and review the code before then; I cannot access your AWS sign-in or approve changes in your account.

## Deploy outline

From the repository root, after prerequisites are ready:

```sh
sam build --template-file infra/template.yaml
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

Choose a descriptive stack name, the intended region, and allow SAM to create the deployment-role resources it requests. Set `AllowedOrigin` to the local origin for development (`http://localhost:8000`), then to the exact CloudFront origin after frontend hosting is added. Set `ChatModelId` to the model ID available in that region. Keep the generated stack outputs private to the project team; they are configuration identifiers, not access keys.

After deployment, load sample catalog rows:

```sh
PRODUCTS_TABLE=<ProductsTableName output> python3 scripts/seed_catalog.py
```

The API URL, user pool ID, and browser client ID are outputs. These values can be used in frontend configuration once the browser app is connected to Cognito and the API. No real payment data is collected; checkout only writes a simulated order.

## Cleanup

When the class demo is finished, delete the CloudFormation stack and verify the stack resources are gone. DynamoDB tables are intentionally not configured for point-in-time recovery, and the stack does not enable product-image storage, a domain, or a NAT gateway. Review the Billing console for lingering usage and remove the budget alert only if you no longer need it.
