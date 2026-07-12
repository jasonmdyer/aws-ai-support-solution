
# AWS AI Travel Planner

End-to-end AI-powered travel planning assistant built on AWS using 20+ services — Lex, Bedrock, Comprehend, Rekognition, Transcribe, Translate, Polly, Textract, Personalize, and more. Plan trips with voice or text, get personalized itineraries, upload travel documents, identify landmarks from photos, and receive recommendations that improve over time.

## Architecture

![Architecture Diagram](architecture/architecture-diagram.png)

## Services Used

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

## Project Phases

- [x] Phase 1: Core Chatbot (Lex + Lambda)
- [x] Phase 2: Smart Travel Knowledge Base (Bedrock + RAG)
- [x] Phase 3: Sentiment + Entity Extraction (Comprehend)
- [ ] Phase 4: Voice + Multilingual Support (Transcribe + Polly + Translate)
- [ ] Phase 5: Document + Image Processing (Textract + Rekognition)
- [ ] Phase 6: Personalized Recommendations (Personalize)
- [ ] Phase 7: Security + Responsible AI (Guardrails + IAM + KMS + A2I)
- [ ] Phase 8: Monitoring + Orchestration (CloudWatch + Step Functions + SageMaker)
- [ ] Phase 9: Internal Knowledge Assistant (Amazon Q Business)

## Setup & Deployment

See [docs/setup-guide.md](docs/setup-guide.md) for full deployment instructions.

## Lessons Learned

See [docs/lessons-learned.md](docs/lessons-learned.md)

## Cost Breakdown

See [docs/cost-breakdown.md](docs/cost-breakdown.md)

## Demo

[Video Walkthrough](demo/demo-video-link.md)

Replace your Author section with:

## Author

[Jason Dyer](https://github.com/jasonmdyer) — Cloud Networking & Engineering Student, WGU
