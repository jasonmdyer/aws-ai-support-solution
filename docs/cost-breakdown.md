
# Cost Breakdown

Estimated monthly costs for running the AWS AI Travel Planner at low usage (demo/portfolio level).

---

## Free Tier Eligible Services

| Service | Free Tier Allowance | Project Usage |
|---------|-------------------|---------------|
| AWS Lambda | 1M requests/month, 400K GB-seconds | Well within limits |
| Amazon S3 | 5 GB storage, 20K GET, 2K PUT | Well within limits |
| Amazon Comprehend | 50K units/month (first 12 months) | Well within limits |
| Amazon Translate | 2M characters/month (first 12 months) | Well within limits |
| Amazon Rekognition | 5K images/month (first 12 months) | Well within limits |
| Amazon Textract | 1K pages/month (first 3 months) | Well within limits |
| Amazon Polly | 5M characters/month (first 12 months) | Well within limits |
| API Gateway | 1M API calls/month (first 12 months) | Well within limits |
| CloudWatch | 10 custom metrics, 5 GB logs | Well within limits |

## Paid Services (No Free Tier)

| Service | Pricing | Estimated Monthly Cost |
|---------|---------|----------------------|
| Amazon Bedrock (Claude 4.5 Haiku) | ~$0.80/1M input tokens, ~$4/1M output tokens | $1-5 (light demo use) |
| Bedrock Knowledge Base (OpenSearch Serverless) | ~$0.24/hr per OCU (minimum 2 OCUs) | $350/month if always on |
| Amazon Personalize | ~$0.05/hr (training) + $0.02/recommendation | $5-15 (with active campaign) |
| KMS | $1/key/month + $0.03/10K requests | ~$1 |

## Cost Optimization Tips

- **Bedrock KB (biggest cost):** Delete the OpenSearch Serverless collection when not demoing. Recreate and sync when needed.
- **Personalize Campaign:** Delete the campaign when not in use. Recreate from the trained solution when needed.
- **Lambda:** Already serverless — zero cost when not invoked.
- **S3:** Pennies per month at demo scale.

## Estimated Total

| Scenario | Monthly Cost |
|----------|-------------|
| Always running (KB + Personalize active) | ~$370-380 |
| Demo only (spin up as needed) | ~$5-20 |
| Completely off (just S3 storage) | ~$0.05 |

## Recommendation

For a portfolio project, keep the OpenSearch Serverless collection and Personalize campaign **deleted** between demos. Spin them up 30 minutes before showing the project, then tear down after. This keeps costs under $20/month.

