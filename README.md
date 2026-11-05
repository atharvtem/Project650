# AWS E-Commerce Storefront with AI Chatbot

A serverless e-commerce demonstration built on AWS. Shoppers will browse a product catalog, create an account, maintain a persistent cart, complete a simulated checkout, view their order history, and ask a catalog-grounded chatbot for product information and recommendations.

## Planned stack

- **Frontend:** Interactive single-page web app hosted in Amazon S3 and delivered by Amazon CloudFront.
- **Authentication:** Amazon Cognito user pool.
- **API and compute:** Amazon API Gateway routes invoke Python AWS Lambda functions.
- **Data:** Amazon DynamoDB stores catalog products, user carts, and orders.
- **Chatbot:** A Python Lambda retrieves relevant catalog items from DynamoDB and calls Amazon Bedrock to generate a grounded response.

The frontend files are static, but the app is dynamic: browser JavaScript calls the API for live catalog, account, cart, order, and chatbot operations. No payment processing will be included.

## Status

The storefront is deployed to CloudFront and its product catalog is served by the live API backed by DynamoDB. Cognito Hosted UI is configured for account sign-in. Cart, simulated checkout, order history, and Bedrock chat are wired to the protected API; they still need an end-to-end pass with a real test account. No payment processing is included.

**Live storefront:** [Fieldnote (working name)](https://d29smamqrn6vkt.cloudfront.net/)

## Run locally

Open `index.html` in a browser, or serve this directory with any static file server. For example, with Python installed run `python3 -m http.server 8000` from the project directory and visit `http://localhost:8000`. The demo stores its cart, account, and order history in that browser's local storage. Use a throwaway password; the demo account is not secure authentication.

## Project documents

- [Project plan](PROJECT_PLAN.md) — phases, milestones, and professor-expectation checklist.
- [Project guide](PROJECT_GUIDE.md) — what the app does, how its architecture works, and why each service is used.
- [AWS deployment handoff](DEPLOYMENT.md) — account-specific prerequisites and the planned deployment steps.

## Cost note

The design uses usage-based/serverless services and should be inexpensive at classroom scale, but it is not guaranteed to be free. Bedrock model inference is metered, and storage, logging, API traffic, data transfer, account age, region, and free-tier eligibility can affect the bill. Create an AWS Budget alert before deployment and remove project resources after grading if they are no longer needed.
