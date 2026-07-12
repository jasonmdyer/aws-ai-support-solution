
# AWS AI Customer Support Bot

End-to-end AI customer support bot built on AWS using 20+ services — Lex, Bedrock, Comprehend, Rekognition, Transcribe, Translate, Polly, Textract, Personalize, and more. Covers chatbot design, RAG search, sentiment analysis, voice and multilingual support, image analysis, monitoring, security, and responsible AI guardrails.

## Architecture

![Architecture Diagram](architecture/architecture-diagram.png)

## Services Used

| Service | Purpose |
|---------|---------|
| Amazon Lex | Chatbot — intents, slots, conversation flow |
| Amazon Bedrock | LLM responses, RAG, agents, guardrails |
| Amazon Comprehend | Sentiment analysis |
| Amazon Rekognition | Image analysis |
| Amazon Transcribe | Speech-to-text |
| Amazon Translate | Multilingual support |
| Amazon Polly | Text-to-speech |
| Amazon Textract | Document extraction |
| Amazon Personalize | Recommendations |
| Amazon Kendra / Bedrock KB | Intelligent search |
| Amazon Q Business | Internal assistant |
| Amazon SageMaker | Custom model training + monitoring |
| Amazon S3 | Storage |
| AWS Lambda | Business logic |
| AWS Step Functions | Workflow orchestration |
| Amazon CloudWatch | Monitoring + alerts |
| AWS IAM | Access management |
| AWS KMS | Encryption |
| Amazon A2I | Human review loop |

## Project Phases

- [x] Phase 1: Core Chatbot (Lex + Lambda)
- [ ] Phase 2: Smart Knowledge Base (Bedrock + Kendra)
- [ ] Phase 3: Sentiment Analysis (Comprehend)
- [ ] Phase 4: Voice + Multilingual (Transcribe + Polly + Translate)
- [ ] Phase 5: Document + Image Processing (Textract + Rekognition)
- [ ] Phase 6: Personalized Recommendations (Personalize)
- [ ] Phase 7: Security + Responsible AI (Guardrails + IAM + KMS + A2I)
- [ ] Phase 8: Monitoring + Orchestration (CloudWatch + Step Functions + SageMaker)
- [ ] Phase 9: Internal Assistant (Amazon Q Business)

## Setup & Deployment

See [docs/setup-guide.md](docs/setup-guide.md) for full deployment instructions.

## Lessons Learned

See [docs/lessons-learned.md](docs/lessons-learned.md)

## Cost Breakdown

See [docs/cost-breakdown.md](docs/cost-breakdown.md)

## Demo

[Video Walkthrough](demo/demo-video-link.md)

## Author

Jason — AWS Certified AI Practitioner

