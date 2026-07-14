
# Lessons Learned

Key takeaways and challenges encountered while building the AWS AI Travel Planner.

---

## IAM & Permissions

- Always verify IAM policy changes saved correctly — propagation can take 30-60 seconds
- Lambda execution roles need explicit permissions for every AWS service called
- When a service returns `AccessDeniedException`, check the inline policy first before creating new ones
- S3 bucket policies are separate from IAM — both may be needed (e.g., Personalize requires a bucket policy)

## Amazon Bedrock

- Knowledge Base IDs are region-specific — if your KB is in us-east-1, your Lambda must also call us-east-1
- After syncing a KB data source, test queries directly in the KB console before calling from Lambda
- AWS now requires inference profiles for model access — use the `us.` prefix on model IDs (e.g., `us.anthropic.claude-sonnet-4-20250514`)
- Guardrails add a safety layer but don't noticeably slow down responses

## Amazon Personalize

- Minimum 1,000 interactions required for data import — plan your training data accordingly
- CSV encoding matters — files must be UTF-8 with no BOM, no extra whitespace
- The Personalize schema field names must be uppercase (USER_ID, ITEM_ID, TIMESTAMP, EVENT_TYPE)
- Solution training takes 20-40 minutes — campaign creation takes another 5-10 minutes
- Delete datasets before dataset groups when cleaning up

## Amazon Polly

- Neural engine voices are deprecated for some regions — use `Engine="generative"` instead of `Engine="neural"`
- Not all voices support all engines — test in the Polly console first
- Audio files save to S3 — ensure your Lambda has `s3:PutObject` permission on the audio bucket

## Amazon Rekognition

- Images must be valid JPEG or PNG — web-downloaded images may be WebP disguised as .jpg
- Re-save images through Paint or an image editor to ensure correct format
- Rekognition labels can be used for smart routing — if "Document", "Page", or "Text" labels appear, route to Textract instead

## Amazon Comprehend

- Requires account activation — new AWS accounts may need to complete sign-up before using Comprehend
- Account-level activation must be done from the root account, not IAM users

## API Gateway + CORS

- CORS errors are the most common frontend issue — both OPTIONS method response AND Lambda response must return `Access-Control-Allow-Origin: *`
- Enable Lambda Proxy Integration for clean request/response passthrough
- Always redeploy the API to the `prod` stage after any changes — changes don't apply until deployed

## S3 Static Website Hosting

- Bucket names are globally unique — add a suffix like your initials or account ID
- Must uncheck "Block all public access" before adding a public bucket policy
- The website URL format is: `http://BUCKET.s3-website-REGION.amazonaws.com`

## Lambda Configuration

- Default 3-second timeout is too short for AI services — set to 30-60 seconds
- Memory affects CPU allocation — 256 MB is good for AI workloads
- Always test with realistic payloads — fake base64 data will fail image processing services

## General Architecture

- Start with one service at a time and verify before adding the next
- Lambda test events are invaluable — save JSON test events for each intent
- Smart detection (using Rekognition to determine photo vs document) creates a better UX than making users choose
- A single API Gateway with two routes (/plan for chat, /upload for files) keeps the frontend simple

