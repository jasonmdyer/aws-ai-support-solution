
# Setup & Deployment Guide

Complete step-by-step instructions to deploy the AWS AI Travel Planner from scratch.

---

## Prerequisites

- AWS Account (fully activated with billing set up)
- IAM admin user (do not deploy on root)
- Region: `us-east-1` (N. Virginia)
- Claude 4.5 Haiku model access enabled in Amazon Bedrock
- Python 3.12 Lambda runtime

---

## Phase 1: Core Chatbot (Lex + Lambda)

### Create the Lambda Function

1. Go to **Lambda** → Create function
2. Function name: `TravelPlannerFunction`
3. Runtime: Python 3.12
4. Architecture: x86_64
5. Timeout: 60 seconds (change in Configuration → General)
6. Memory: 256 MB
7. Paste code from `lambda/lambda_function.py`
8. Click Deploy

### Create the Lex Bot

1. Go to **Amazon Lex** → Create bot
2. Bot name: `TravelPlannerBot`
3. Language: English (US)
4. Create the following intents:

**PlanTrip Intent:**
- Sample utterances: "Plan a trip to {destination}", "I want to travel to {destination}", "Plan a trip"
- Slots:
  - `destination` (AMAZON.City) — "Where would you like to travel to?"
  - `travel_date` (AMAZON.Date) — "When do you want to leave?"
  - `duration` (AMAZON.Number) — "How many days is your trip?"
  - `trip_style` (custom slot: adventure, relaxation, cultural, budget, luxury) — "What style of trip?"
- Fulfillment: Lambda function → `TravelPlannerFunction`

**AnalyzePhoto Intent:**
- Sample utterances: "Analyze this photo", "What is in this image"
- Slots:
  - `photo_key` (AMAZON.AlphaNumeric)
- Fulfillment: Lambda function → `TravelPlannerFunction`

**AnalyzeDocument Intent:**
- Sample utterances: "Scan this document", "Read this file"
- Slots:
  - `document_key` (AMAZON.AlphaNumeric)
- Fulfillment: Lambda function → `TravelPlannerFunction`

**GetRecommendations Intent:**
- Sample utterances: "Get my recommendations", "What should I visit", "Recommend a destination"
- Slots:
  - `user_id` (AMAZON.AlphaNumeric)
- Fulfillment: Lambda function → `TravelPlannerFunction`

**Greeting Intent:**
- Sample utterances: "Hello", "Hi", "Hey", "Good morning"
- No slots
- Closing response: "Hello! I'm your AI Travel Planner. I can help you plan trips, analyze travel photos, scan documents, or give personalized recommendations. Where would you like to explore?"

5. Build the bot
6. Test in the Lex console

---

## Phase 2: Knowledge Base (Bedrock + RAG)

### Create the S3 Data Bucket

1. Go to **S3** → Create bucket
2. Bucket name: `travel-planner-kb-data` (or similar unique name)
3. Upload all files from `knowledge-base/` folder

### Create the Bedrock Knowledge Base

1. Go to **Amazon Bedrock** → Knowledge bases → Create
2. Name: `TravelPlannerKB`
3. Data source: S3 → point to your bucket
4. Embedding model: Titan Embeddings V2
5. Vector store: Quick create (OpenSearch Serverless)
6. Click Create → Sync the data source
7. Note the **Knowledge Base ID** (update in `lambda_function.py`)

### Test the KB

1. In the KB console, click Test
2. Select model: Claude 4.5 Haiku, US region
3. Query: "What are the best things to do in Japan?"
4. Verify it returns content from your travel guides

---

## Phase 3: Comprehend (Sentiment + Entities)

No console setup required — Comprehend is called directly from Lambda code. Just ensure:

1. Your AWS account has Comprehend activated
2. IAM policy includes `comprehend:DetectSentiment` and `comprehend:DetectEntities`

---

## Phase 4: Translate + Polly

### Create the Audio Bucket

1. Go to **S3** → Create bucket
2. Bucket name: `travel-planner-audio` (or similar unique name)
3. Default settings

### IAM Permissions

Add to your Lambda execution role:
- `translate:TranslateText`
- `polly:SynthesizeSpeech`
- `s3:PutObject` on audio bucket

---

## Phase 5: Textract + Rekognition

### Create the Uploads Bucket

1. Go to **S3** → Create bucket
2. Bucket name: `travel-planner-uploads-jmd` (or similar unique name)
3. Default settings

### IAM Permissions

Add to your Lambda execution role:
- `rekognition:DetectLabels`
- `textract:AnalyzeDocument`
- `s3:GetObject` on uploads bucket

---

## Phase 6: Personalize (Recommendations)

### Create IAM Role for Personalize

1. Go to **IAM** → Create role
2. Trusted entity: AWS service → Personalize
3. Attach policies:
   - `AmazonPersonalizeFullAccess`
   - Inline policy for S3 access to your data bucket

### Create the Data Bucket

1. Go to **S3** → Create bucket
2. Bucket name: `travel-planner-personalize-data`
3. Upload `personalize-data/interactions.csv`
4. Add bucket policy allowing Personalize service access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PersonalizeAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "personalize.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    },
    {
      "Sid": "PersonalizeListAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "personalize.amazonaws.com"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    }
  ]
}
