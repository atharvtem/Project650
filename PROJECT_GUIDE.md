# Project Guide: AWS E-Commerce Storefront with AI Chatbot

## What we are building

This project is a small but complete online-store demonstration. It addresses the need to connect the parts of a cloud application into one working experience: public product discovery, authenticated user activity, durable data, and a natural-language interface to that data.

A shopper can create an account, sign in, browse and filter a curated catalog, keep a cart between visits, simulate an order, and review past orders. The chatbot helps shoppers find products by asking questions in ordinary language. It answers from the live catalog records rather than treating the language model as the source of product facts.

It is a learning/demo storefront, not a real commerce platform: there are no payment cards, payment processor, real fulfillment, or production stock guarantees.

## How the app can be dynamic while the frontend is static

“Static” describes how the frontend files are delivered, not what the experience can do. S3 stores HTML, CSS, JavaScript, and images. CloudFront serves those files to the browser. Once loaded, the JavaScript runs in the user's browser and sends requests to the API for data and actions. A single-page application can change the visible page without downloading a new HTML file for every action.

For example, selecting a price filter triggers a request to the product API, which returns the matching products. Adding to cart sends an authenticated request; Lambda updates DynamoDB; the UI then redraws with the returned cart. Sign-in, checkout, order history, and chatbot messages follow the same pattern. The frontend does not connect directly to DynamoDB or Bedrock.

## Architecture and service roles

```text
Browser (interactive JavaScript app)
  ├── S3 + CloudFront: deliver the static frontend securely and quickly
  └── API Gateway HTTP API: HTTPS application endpoints
        ├── Cognito JWT authorizer: validate protected requests
        └── Python Lambda functions
              ├── DynamoDB: product catalog, carts, orders
              └── Bedrock: model inference for catalog-grounded chat
```

| Service | What it does here | Why it fits |
|---|---|---|
| Amazon S3 | Stores built frontend files and optional product images. | No web server needs to run just to serve HTML/JS/CSS. |
| Amazon CloudFront | Delivers the frontend over HTTPS and caches static assets. | Separates fast public asset delivery from the application API. |
| Amazon Cognito User Pools | Registers users and provides sign-in tokens. | Managed authentication avoids storing passwords in the project database. |
| Amazon API Gateway (HTTP API) | Exposes routes such as `/products`, `/cart`, `/orders`, and `/chat`. | Routes requests to Lambda and can validate Cognito JWTs on protected routes. |
| AWS Lambda (Python) | Implements product queries, cart operations, simulated checkout, order history, and chat orchestration. | Event-driven compute runs only when invoked and matches the proposed serverless design. |
| Amazon DynamoDB | Stores products and user-owned carts/orders. | Managed NoSQL storage fits simple key-based lookups and avoids database servers. |
| Amazon Bedrock | Generates a conversational answer from the relevant catalog records. | Adds natural-language product discovery while keeping the application data as the source of truth. |
| Amazon CloudWatch | Captures function/API logs and optional alarms. | Helps debug the deployed workflow; log volume should be kept modest. |

Use CloudFront with a private S3 origin (origin access control) rather than making the bucket broadly public. Configure the CloudFront distribution to serve the SPA entry point for frontend routes, and configure API CORS for the deployed frontend origin.

## Request flows

### Public catalog browse

1. Browser fetches the app bundle from CloudFront (S3 origin).
2. The app requests product data from API Gateway.
3. A catalog Lambda reads DynamoDB and returns only the fields needed by the page.
4. Browser renders products and any active search/filter state.

### Authenticated cart and checkout

1. User signs in through Cognito; the browser holds a short-lived access token according to the client configuration.
2. Browser sends the token in the `Authorization: Bearer …` header for protected API calls.
3. API Gateway validates the JWT and includes the verified claims in the Lambda event.
4. Lambda derives the owner key from those verified claims, reads/writes the owner's cart, and rejects any attempt to choose another user's key.
5. Checkout validates cart contents, writes an order record, and clears the cart. It does not charge money.

### Catalog-grounded chatbot

1. Browser submits a question to the protected chat endpoint.
2. Chat Lambda extracts useful criteria (for example category, maximum price, or desired features) and retrieves a small set of matching catalog items.
3. Lambda sends the question and the retrieved product details to Bedrock with instructions to answer only from those details, cite product names/prices in the response, and say when no suitable match is found.
4. Browser shows the response and product links/cards. Do not send the full database or secrets to the model.

For the first version, ordinary DynamoDB filters and keyword matching are enough. A vector database/embeddings pipeline is intentionally unnecessary for a small, structured catalog and would add complexity and cost.

## Data model direction

Start with a few focused tables or a clearly documented single-table design; do not over-engineer. A straightforward three-table design is easiest to explain in a course presentation:

- **Products:** partition key `productId`; category, title, description, price, attributes, image URL, active flag. A category index can support common filters; price filtering can be applied to a small result set or designed into an index if needed.
- **Carts:** partition key `userId` derived from Cognito `sub`; cart lines stored as product ID plus quantity and validated product pricing. Keep cart writes owned by the server.
- **Orders:** partition key `userId`, sort key `createdAt#orderId`; immutable snapshot of purchased product names, unit prices, quantities, total, and simulated status.

Do not trust prices or ownership sent by the browser. On checkout, re-read product prices from the catalog and compute totals in Lambda. Treat orders as snapshots so later catalog edits do not rewrite the purchase history.

## Cost expectations

This is a low-traffic student app, so the non-AI infrastructure can be free or very low cost if usage stays within the applicable free allowances and the team avoids optional always-on resources. It is **not safe to promise a $0 bill**: rates and free-tier eligibility depend on account history, region, feature choice, and usage. AWS currently advertises up to $200 in credits for eligible new accounts, with a six-month free plan and credits expiring within 12 months; verify the actual account's billing page before relying on this.

| Service | Classroom-scale expectation | Cost watch-outs |
|---|---|---|
| S3 | Tiny static site and a few product images should be very inexpensive; eligible new accounts may have credits. | Storage, requests, data transfer, and old uploads/versions can accumulate. |
| CloudFront | Likely free at demo traffic if within current monthly free allowances. | Traffic, invalidations, logs, extra edge features, and account/pricing-plan details can change the result. |
| Cognito | Likely free for a small user pool under the current direct-user MAU allowance for eligible Lite/Essentials plans. | Plan, advanced security features, federation, and account settings affect price. |
| API Gateway HTTP API | Low usage should fit free allowance for eligible accounts or otherwise cost little. | Requests and data transfer are metered; REST API has a different rate, so prefer HTTP API unless a needed feature requires REST. |
| Lambda | Likely free/very low for light use within request and compute allowances. | Long-running/high-memory functions, provisioned concurrency, and VPC/NAT architecture add cost. Avoid a NAT gateway. |
| DynamoDB | Tiny catalog/cart/order data should be inexpensive; available free capacity depends on using the eligible configuration and account. | Provisioned capacity is billed while allocated; on-demand operations and storage are metered. Choose the free-tier-compatible table mode after checking the account. |
| Bedrock | **The primary variable and the one service to assume may cost money.** It is generally metered by model and input/output tokens; do not assume it is covered by Lambda or other free tiers. | Repeated prompts, long catalog context, large outputs, or more expensive models increase the bill. Limit context and response length; use a suitable low-cost model available in the chosen region; set a per-user request limit. |
| CloudWatch | Small logs volume should be low; keep only what is useful for the demo. | Log ingestion and retention can create unexpected recurring charges. Set retention and avoid logging tokens or personal data. |

Practical controls: create an AWS Budget alert before deployment; use a dedicated project environment and one region; avoid NAT gateways, provisioned concurrency, paid database add-ons, and paid domain registration unless required; cap chatbot requests and token output; set short log retention; and delete demo resources after the course. A budget alert notifies but does not automatically stop spending.

Pricing references checked on 2026-11-05: [S3](https://aws.amazon.com/s3/pricing/), [CloudFront](https://aws.amazon.com/cloudfront/pricing/), [Cognito](https://aws.amazon.com/cognito/pricing/), [API Gateway](https://aws.amazon.com/api-gateway/pricing/), [Lambda](https://aws.amazon.com/lambda/pricing/), [DynamoDB](https://aws.amazon.com/dynamodb/pricing/), and [Bedrock](https://aws.amazon.com/bedrock/pricing/). Consult the account-specific AWS Pricing Calculator and Billing console before deployment.

## Security, correctness, and demo quality

- Make the S3 origin private and use CloudFront access controls.
- Use Cognito JWT authorization for protected routes; keep catalog reads public only if the team wants anonymous browsing.
- Use least-privilege Lambda roles: product read where needed, cart/order access only where required, and Bedrock invoke permission only for the chat function.
- Derive `userId` from validated Cognito claims, never from a body/query parameter.
- Validate quantities, product IDs, request sizes, and checkout data in Lambda.
- Do not store credentials, AWS keys, access tokens, or chat secrets in source control or logs.
- Have the chatbot state when it has insufficient catalog evidence and never invent price, availability, or product details.
- Test with at least two separate accounts to prove user data separation, plus a predefined prompt set for chat accuracy.

## Testing and demonstration plan

Maintain a small repeatable acceptance checklist:

1. Register two users, sign in/out, and confirm invalid or absent tokens cannot call protected routes.
2. Browse all products and check category/price filters against known seeded data.
3. For user A, add/update/remove products and confirm the cart persists after refresh and sign-in again.
4. Sign in as user B and confirm user A's cart and orders are not visible.
5. Simulate checkout as user A; verify an order record and cleared cart, then verify order history remains visible only to A.
6. Run chatbot prompts for named attributes, categories, max/min price, preference-based recommendations, and a no-match requirement. Compare answers with the DynamoDB catalog.
7. Perform the same flow against the deployed URL and rehearse within the presentation time.

## Build and deployment workflow

Use small vertical slices rather than a single late integration. First make the UI run locally with mock data; next deploy the catalog path; then add Cognito and account-specific state; then the chatbot; finally prepare the demo. Define the cloud stack in a repeatable infrastructure-as-code template (AWS SAM/CloudFormation is a reasonable fit for API Gateway, Lambda, DynamoDB, and Cognito). Keep only non-secret identifiers/configuration in frontend build settings. The team controls account login and deployment approvals; do not commit credentials. During each cloud phase, deploy one service path, inspect it, and verify its acceptance scenario before moving on.

## Presentation and source-credit notes

The final presentation should explain the problem, the request/data flow, why each AWS service is used, the implemented behavior, test results, cost/security choices, and remaining limitations. Use architecture and request-flow diagrams plus a live demo, with time reserved for questions. Cite AWS documentation, any code/assets/data reused, and AI assistance (including ChatGPT/Codex) in the slides because the professor's handout explicitly asks for AI tools to be cited like other resources. Every student submits their own peer-evaluation forms.
