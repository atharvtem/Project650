# Project Plan

## Project

**AWS-Based E-Commerce Storefront with AI Chatbot**

**Storefront brand:** Fieldnote is a working name introduced during implementation. It is not specified by the course handout or a team-approved project commitment; confirm the final name with the team before the presentation.

The team will build and deploy a cloud-based storefront on AWS. Users will register and sign in, browse and filter products, maintain a persistent cart, complete a simulated checkout, see prior orders, and ask a conversational assistant questions about the active product catalog.

## Professor-expectations checklist

The attached term-project handout asks teams to choose an AWS application or service, clearly describe the problem it solves and how success will be tested, provide a Week 10 status update, and finish with slides plus a 15-minute in-class presentation that includes a live demo. It grades timeliness (3 points), correct operation (7), technical accuracy and completeness of slides (7), presentation clarity and Q&A (5), and individual peer evaluation (8). The handout also requires citing resources, including AI tools, used in the final presentation.

| Expectation | Project response | Planned evidence |
|---|---|---|
| Clearly describe the problem and what the AWS app does | A cloud storefront demonstrates authenticated catalog access, per-user cart/order state, and natural-language product discovery. | Topic summary submitted by Week 4; project overview in final slides. |
| Define how the project will be tested | Test authentication, catalog filters, cart persistence, simulated order placement, order history, chatbot product accuracy, and separation between accounts. | Acceptance checklist and repeatable end-to-end scenarios. |
| Work as a team of 5–6 students | Divide implementation and presentation work by frontend, identity/API, database/checkout, chatbot, deployment/testing, and documentation/demo; assign ownership to actual team members. | Team task/ownership list to be added once members are known. |
| Provide a Week 10 status update | Report completed work, hurdles, and remaining work against the planned features. | Status update document submitted by Week 10. |
| Correctly operate the application/service (7 points) | Deploy the complete user journey with AWS services and verify it with separate accounts. | Live site and successful multi-user end-to-end demo. |
| Accurate and complete technical slides (7 points) | Explain request flow, identity, Lambda/API, DynamoDB data model, Bedrock grounding, deployment, results, and limitations. | Slides submitted before the course deadline; cite AWS sources and AI assistance. |
| Clear 15-minute talk with questions (5 points) | Use a concise architecture explanation, a timed live demo, and a conclusion; prepare answers about security, cost, failure cases, and design tradeoffs. | Rehearsed Week 15 presentation and live demo. |
| Individual peer evaluations (8 points) | Every teammate submits an evaluation for every other teammate by the Canvas deadline. | Each member confirms submission. |
| Submission dates | The handout says to check Canvas for precise deadlines. | Add exact dates from Canvas to the team calendar; do not infer them from the week numbers. |

The handout permits topic choice and expansion. The storefront, AWS architecture, and chatbot match its e-commerce sample directly and add a bounded AI feature. The professor's handout does not require a particular framework or dictate these exact AWS services; those are project design commitments and implementation choices.

## Scope and acceptance criteria

### Included

- Product catalog with seeded sample inventory and product detail views.
- Search and filters by category and price range.
- Cognito registration, sign-in, sign-out, and session-aware navigation.
- Persistent, account-specific cart with add, remove, and quantity update.
- Simulated checkout that validates the cart, records an order, and clears the cart.
- Account-specific order history.
- Chat interface for catalog questions and recommendations grounded in products retrieved from DynamoDB.
- Responsive, presentable web interface with loading, empty, and error states.
- AWS deployment using S3, CloudFront, Cognito, API Gateway, Lambda, DynamoDB, and Bedrock.

### Explicitly out of scope

Real payments, real shipping, inventory reservation across concurrent checkouts, production-scale recommendation training, and a fully autonomous agent. Keep the catalog modest (about 20–40 well-described products) so the team can finish and validate the full workflow.

### Definition of done

1. A new user can register, sign in, browse/filter products, add items to a cart, and see that cart after reloading/signing in again.
2. The user can simulate checkout and view the resulting order in order history.
3. A second account cannot read or alter the first account's cart or orders.
4. Protected API routes reject missing or invalid Cognito tokens.
5. A predefined chatbot prompt set tests attributes, category, price range, and stated requirements. Answers accurately reflect retrieved catalog data; no-match questions receive an honest no-result response.
6. The deployed app completes the end-to-end workflow during the final demonstration.

## Implementation phases

1. **Requirements and design:** Convert the rubric and commitments into acceptance scenarios. Define product fields, screens, API routes, and ownership split.
2. **Local interface and sample data:** Build the responsive browser app against local/mock catalog data. Keep frontend hosting separate from backend behavior.
3. **Cloud catalog slice:** Define AWS resources as infrastructure-as-code; deploy the S3/CloudFront frontend, API Gateway, a Python catalog Lambda, and DynamoDB catalog table. Connect the browser to live products.
4. **Authentication and user data:** Add Cognito and API authorization, then user-keyed carts and orders. Use the verified identity from the token for ownership, never a client-submitted user identifier.
5. **Storefront completion:** Implement cart operations, simulated checkout, and order history; verify persistence and account isolation.
6. **Chatbot:** Add a chat Lambda that retrieves matching product records and passes only relevant catalog context to Bedrock. Add prompt/response limits and grounding-oriented response rules.
7. **Hardening and test pass:** Run the written acceptance scenarios, test two or more accounts, address errors and accessibility basics, and set cost monitoring.
8. **Presentation and handoff:** Prepare the Week 10 status update, final technical slides, citations, rehearsed live demo, Q&A preparation, and peer-evaluation reminders.

## Delivery cadence

| Course point | Team output |
|---|---|
| Week 4 | Topic summary describing the app, problem addressed, AWS approach, and success criteria. |
| Week 10 | Status update: work completed, hurdles, and remaining work. |
| Before Week 15 | Submit slides by the Canvas deadline. |
| Week 15 | 15-minute presentation and live demonstration; answer audience questions. |
| Week 15 | Each student submits peer evaluations by the Canvas deadline. |

The exact calendar deadlines must be copied from Canvas. Schedule the deployment and demo rehearsal before the final week, not on presentation day.

## Working method

Build and connect the app in vertical slices, adding and demonstrating one AWS capability at a time. Keep the infrastructure definition and deployment instructions in the repository so the setup can be repeated. The team supplies/controls AWS account access and any required approvals; never commit access keys or other secrets. Start with a low-usage sandbox/account, enable a budget alert, and clean up resources when the project is complete.
