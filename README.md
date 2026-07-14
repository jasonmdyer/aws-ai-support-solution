Let me remove the Project Structure section entirely and replace it with something cleaner — just a simple list:


# ✈️ AWS AI Travel Planner

End-to-end AI-powered travel planning assistant built on AWS using 20+ services — Lex, Bedrock, Comprehend, Rekognition, Transcribe, Translate, Polly, Textract, Personalize, and more. Plan trips with voice or text, get personalized itineraries, upload travel documents, identify landmarks from photos, and receive recommendations that improve over time.

🔗 **[Live Demo](http://travel-planner-frontend-jmd.s3-website-us-east-1.amazonaws.com)**

---

## 📸 Screenshots

<!-- Add screenshots here -->

---

## 🏗️ Architecture

![Architecture Diagram](architecture/architecture-diagram.png)

---

## 🔄 How It Works

**Chat Flow:**
> User → API Gateway → Lambda (API Handler) → Amazon Lex → Lambda (Main) → Bedrock KB + Comprehend + Personalize → Claude 4.5 Haiku → Translate + Polly + KMS → Guardrails → Response

**Photo Upload Flow:**
> User uploads image → API Gateway → Lambda (API Handler) → Rekognition (detect type) → Photo detected → Rekognition labels + Claude travel tips → Response

**Document Upload Flow:**
> User uploads document → API Gateway → Lambda (API Handler) → Rekognition (detect type) → Document detected → Textract extraction + Claude analysis → Response

**Security & Monitoring (applied to all flows):**
> Bedrock Guardrails (content filtering) • KMS (encryption) • CloudWatch (metrics + logs + alarms) • IAM (access control)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗺️ Trip Planning | Conversational itinerary generation powered by RAG + Claude 4.5 Haiku |
| 📸 Photo Analysis | Upload travel photos — AI identifies landmarks and provides travel tips |
| 📄 Document Scanner | Smart detection auto-routes documents to Textract for data extraction |
| 🌍 Recommendations | Personalized destination suggestions based on user interaction history |
| 🗣️ Multilingual | Auto-translates key phrases to the destination's local language |
| 🎧 Audio Generation | Text-to-speech itinerary narration via Amazon Polly |
| 🔒 Security | AI Guardrails for content filtering + KMS encryption |
| 📊 Monitoring | Real-time CloudWatch metrics, structured logging, and alarms |
| 🌐 Web Interface | Clean, responsive frontend hosted on S3 with file upload support |

---

## 🛠️ Services Used

| Service | Purpose |
|---------|---------|
| Amazon Lex | Chatbot — handles trip planning conversation flow |
| Amazon Bedrock | LLM-powered itinerary generation and travel Q&A |
| Bedrock Knowledge Base | RAG over travel guides, visa docs, city info |
| Bedrock Agents | Chains actions: search → build itinerary → recommend |
| Bedrock Guardrails | Prevents unsafe recommendations (dangerous areas, scams) |
| Amazon Comprehend | Sentiment detection + entity extraction (cities, dates, budgets) |
| Amazon Rekognition | Identifies landmarks and scenes from uploaded photos |
| Amazon Transcribe | Voice input for hands-free trip planning |
| Amazon Translate | Translates common phrases for destination language |
| Amazon Polly | Reads itinerary back via text-to-speech |
| Amazon Textract | Extracts info from passports, boarding passes, hotel confirmations |
| Amazon Personalize | Learns preferences over time for smarter recommendations |
| Amazon Q Business | Personal travel knowledge base search |
| Amazon SageMaker | Cost prediction model by destination |
| Amazon S3 | Stores travel docs, images, audio, knowledge base files |
| AWS Lambda | Business logic — routing, processing, budget calculations |
| AWS Step Functions | Orchestrates full workflow from input to itinerary output |
| Amazon CloudWatch | Monitoring and alerts |
| AWS IAM | Access control across all services |
| AWS KMS | Encrypts personal travel data |
| Amazon A2I | Human review for complex edge cases (visa questions) |

---

## 📈 Project Phases

- [x] Phase 1: Core Chatbot (Lex + Lambda)
- [x] Phase 2: Smart Travel Knowledge Base (Bedrock + RAG)
- [x] Phase 3: Sentiment + Entity Extraction (Comprehend)
- [x] Phase 4: Voice + Multilingual Support (Transcribe + Polly + Translate)
- [x] Phase 5: Document + Image Processing (Textract + Rekognition)
- [x] Phase 6: Personalized Recommendations (Personalize)
- [x] Phase 7: Security + Responsible AI (Guardrails + IAM + KMS + A2I)
- [x] Phase 8: Monitoring + Orchestration (CloudWatch + Step Functions + SageMaker)
- [ ] Phase 9: Internal Knowledge Assistant (Amazon Q Business)

---

## 📁 Project Structure

- `lambda/lambda_function.py` — Main Lambda, Lex fulfillment (Phases 1-8)
- `lambda/api_handler.py` — API Gateway Lambda, chat + upload + smart detection
- `frontend/index.html` — S3-hosted responsive web interface
- `knowledge-base/` — Travel guides (Costa Rica, Iceland, Japan, Mexico, Thailand)
- `personalize-data/interactions.csv` — Training data for recommendation engine
- `tests/` — Lambda test events (PlanTrip, AnalyzePhoto, AnalyzeDocument, GetRecommendations)
- `test-images/` — Sample images for Rekognition and Textract testing
- `architecture/` — Architecture diagram
- `docs/` — Setup guide, lessons learned, cost breakdown
- `demo/` — Demo video link

---

## 🚀 Setup & Deployment

See [docs/setup-guide.md](docs/setup-guide.md) for full deployment instructions.

### Quick Start Prerequisites

- AWS Account with access to Bedrock, Lex, Comprehend, Translate, Polly, Rekognition, Textract, Personalize
- Python 3.12 runtime for Lambda
- Claude 4.5 Haiku model enabled in Amazon Bedrock (us-east-1)

### Key Setup Steps

1. **Knowledge Base** — Create S3 bucket, upload travel guides, create Bedrock KB, sync
2. **Lex Bot** — Create bot with PlanTrip, AnalyzePhoto, AnalyzeDocument, GetRecommendations intents
3. **Lambda Functions** — Deploy `lambda_function.py` (main) and `api_handler.py` (API handler)
4. **Personalize** — Create dataset group, import interactions.csv, train solution, create campaign
5. **Security** — Create Bedrock Guardrail + KMS key
6. **API Gateway** — Create REST API with `/plan` and `/upload` endpoints
7. **Frontend** — Deploy `index.html` to S3 static website bucket

---

## 🧪 Testing

Use the JSON files in `tests/` as Lambda test events:

| Test File | Intent | Lambda Target |
|-----------|--------|---------------|
| `test-event.json` | PlanTrip | TravelPlannerFunction |
| `photo-test-event.json` | AnalyzePhoto | TravelPlannerFunction |
| `document-test-event.json` | AnalyzeDocument | TravelPlannerFunction |
| `recommendation-test-event.json` | GetRecommendations | TravelPlannerFunction |

---

## 💡 Lessons Learned

See [docs/lessons-learned.md](docs/lessons-learned.md)

---

## 💰 Cost Breakdown

See [docs/cost-breakdown.md](docs/cost-breakdown.md)

---

## 🎬 Demo

[Video Walkthrough](demo/demo-video-link.md)

---

## 👨‍💻 Author

[Jason Dyer](https://github.com/jasonmdyer) — Cloud Networking & Engineering Student, WGU


Replaced the project structure with a simple bullet list — no tree diagrams, no tables. Clean and renders perfectly on GitHub. Copy and paste!
