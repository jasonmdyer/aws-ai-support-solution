
import json
import boto3
import base64

KNOWLEDGE_BASE_ID = "UNCTZY1UHS"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"
AUDIO_BUCKET = "travel-planner-audio"
UPLOADS_BUCKET = "travel-planner-uploads-jmd"
PERSONALIZE_CAMPAIGN_ARN = "arn:aws:personalize:us-east-1:975193805465:campaign/travel-recommendation-campaign"
GUARDRAIL_ID = "c63g8amj9rxj"
GUARDRAIL_VERSION = "DRAFT"
KMS_KEY_ID = "f8239126-96aa-4058-8347-3b31d5d97fe3"

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
comprehend = boto3.client("comprehend", region_name=REGION)
translate_client = boto3.client("translate", region_name=REGION)
polly_client = boto3.client("polly", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)
textract_client = boto3.client("textract", region_name=REGION)
rekognition_client = boto3.client("rekognition", region_name=REGION)
personalize_runtime = boto3.client("personalize-runtime", region_name=REGION)
kms_client = boto3.client("kms", region_name=REGION)

# Map destinations to language codes for Translate
DESTINATION_LANGUAGES = {
    "japan": "ja",
    "tokyo": "ja",
    "kyoto": "ja",
    "osaka": "ja",
    "italy": "it",
    "rome": "it",
    "florence": "it",
    "costa rica": "es",
    "thailand": "th",
    "bangkok": "th",
    "iceland": "is",
    "france": "fr",
    "paris": "fr",
    "germany": "de",
    "spain": "es",
    "mexico": "es",
    "brazil": "pt",
    "south korea": "ko",
    "china": "zh",
    "india": "hi"
}

# Common travel phrases to translate
TRAVEL_PHRASES = [
    "Hello",
    "Thank you",
    "Excuse me",
    "Where is the bathroom?",
    "How much does this cost?",
    "I need help",
    "Do you speak English?",
    "The check, please",
    "Where is the train station?",
    "Goodbye"
]


# ─── Phase 7: Guardrails — Check content safety ───
def apply_guardrail(text, source="OUTPUT"):
    """Apply Bedrock Guardrail to check content for safety violations."""
    try:
        response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[{"text": {"text": text}}]
        )
        action = response.get("action", "NONE")
        if action == "GUARDRAIL_INTERVENED":
            blocked_response = "I'm sorry, I can't help with that request. Please ask about legitimate travel planning topics."
            return {"blocked": True, "message": blocked_response}
        return {"blocked": False, "message": text}
    except Exception as e:
        return {"blocked": False, "message": text}


# ─── Phase 7: KMS — Encrypt sensitive data ───
def encrypt_pii(plaintext):
    """Encrypt sensitive user data (passport numbers, credit cards, etc.)."""
    try:
        response = kms_client.encrypt(
            KeyId=KMS_KEY_ID,
            Plaintext=plaintext.encode("utf-8")
        )
        encrypted = base64.b64encode(response["CiphertextBlob"]).decode("utf-8")
        return encrypted
    except Exception as e:
        return None


def decrypt_pii(encrypted_text):
    """Decrypt sensitive user data."""
    try:
        ciphertext = base64.b64decode(encrypted_text)
        response = kms_client.decrypt(
            CiphertextBlob=ciphertext,
            KeyId=KMS_KEY_ID
        )
        return response["Plaintext"].decode("utf-8")
    except Exception as e:
        return None


# ─── Phase 6: Personalize — Get recommendations for a user ───
def get_recommendations(user_id):
    """Get personalized destination recommendations for a user."""
    try:
        response = personalize_runtime.get_recommendations(
            campaignArn=PERSONALIZE_CAMPAIGN_ARN,
            userId=user_id,
            numResults=5
        )
        recommendations = []
        for item in response["itemList"]:
            recommendations.append(item["itemId"])
        return recommendations
    except Exception as e:
        return None


# ─── Phase 5: Rekognition — Identify landmarks from photos ───
def analyze_image(bucket, key):
    """Detect labels/landmarks from an uploaded travel photo."""
    response = rekognition_client.detect_labels(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key
            }
        },
        MaxLabels=15,
        MinConfidence=75
    )

    labels = []
    for label in response["Labels"]:
        labels.append({
            "name": label["Name"],
            "confidence": round(label["Confidence"], 1)
        })

    landmark_keywords = ["landmark", "monument", "temple", "castle", "tower",
                         "bridge", "cathedral", "mosque", "shrine", "palace",
                         "statue", "ruins", "pyramid"]
    detected_landmarks = []
    for label in labels:
        if any(keyword in label["name"].lower() for keyword in landmark_keywords):
            detected_landmarks.append(label["name"])

    return {
        "labels": labels,
        "landmarks": detected_landmarks
    }


# ─── Phase 5: Textract — Extract text from travel documents ───
def extract_document_text(bucket, key):
    """Extract text from boarding passes, passports, hotel confirmations."""
    response = textract_client.detect_document_text(
        Document={
            "S3Object": {
                "Bucket": bucket,
                "Name": key
            }
        }
    )

    lines = []
    for block in response["Blocks"]:
        if block["BlockType"] == "LINE":
            lines.append(block["Text"])

    extracted_text = "\n".join(lines)

    prompt = f"""Analyze this text extracted from a travel document and identify key travel details:
{extracted_text}

Extract and organize:
- Document type (boarding pass, hotel confirmation, passport, visa, etc.)
- Traveler name
- Destination
- Dates (departure, arrival, check-in, check-out)
- Flight/booking numbers
- Any other relevant travel details

Format the response clearly."""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    })
    model_response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )
    response_body = json.loads(model_response["body"].read())
    return response_body["content"][0]["text"]


# ─── Phase 5: Get landmark info from KB ───
def get_landmark_info(landmarks, labels):
    """Use detected landmarks/labels to query KB for travel info."""
    search_terms = landmarks if landmarks else [l["name"] for l in labels[:5]]
    query = f"Tell me about these travel destinations or landmarks: {', '.join(search_terms)}"

    retrieve_response = bedrock_agent.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}}
    )

    chunks = []
    for result in retrieve_response.get("retrievalResults", []):
        text = result.get("content", {}).get("text", "")
        if text:
            chunks.append(text)

    if not chunks:
        return None

    context = " ".join(chunks)
    prompt = f"Based on this travel info: {context} --- The user uploaded a photo that contains: {', '.join(search_terms)}. Provide helpful travel tips and information about what they're looking at."

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    })
    model_response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )
    response_body = json.loads(model_response["body"].read())
    return response_body["content"][0]["text"]


# ─── Phase 4: Translate — Get useful phrases in destination language ───
def get_translated_phrases(destination):
    """Translate common travel phrases to the destination's language."""
    lang_code = None
    for key, code in DESTINATION_LANGUAGES.items():
        if key in destination.lower():
            lang_code = code
            break

    if not lang_code:
        return None

    translated_phrases = []
    for phrase in TRAVEL_PHRASES:
        try:
            response = translate_client.translate_text(
                Text=phrase,
                SourceLanguageCode="en",
                TargetLanguageCode=lang_code
            )
            translated_phrases.append({
                "english": phrase,
                "translated": response["TranslatedText"]
            })
        except Exception:
            continue

    return translated_phrases


# ─── Phase 4: Polly — Convert itinerary to audio ───
def generate_audio(text, destination):
    """Convert itinerary text to speech and save to S3."""
    clean_text = text[:2900].replace("#", "").replace("*", "").replace("|", "")

    try:
        response = polly_client.synthesize_speech(
            Text=clean_text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            Engine="standard"
        )

        audio_key = f"itineraries/{destination.lower().replace(' ', '-')}-itinerary.mp3"
        s3_client.put_object(
            Bucket=AUDIO_BUCKET,
            Key=audio_key,
            Body=response["AudioStream"].read(),
            ContentType="audio/mpeg"
        )

        audio_url = f"https://{AUDIO_BUCKET}.s3.amazonaws.com/{audio_key}"
        return audio_url

    except Exception as e:
        return None


# ─── Phase 3: Comprehend — Sentiment + Entity Extraction ───
def analyze_user_input(text):
    """Detect sentiment and extract entities from user input."""
    sentiment_response = comprehend.detect_sentiment(
        Text=text,
        LanguageCode="en"
    )
    sentiment = sentiment_response["Sentiment"]
    sentiment_scores = sentiment_response["SentimentScore"]

    entities_response = comprehend.detect_entities(
        Text=text,
        LanguageCode="en"
    )
    entities = entities_response["Entities"]

    extracted = {
        "locations": [],
        "dates": [],
        "quantities": [],
        "other": []
    }

    for entity in entities:
        if entity["Type"] == "LOCATION":
            extracted["locations"].append(entity["Text"])
        elif entity["Type"] == "DATE":
            extracted["dates"].append(entity["Text"])
        elif entity["Type"] == "QUANTITY":
            extracted["quantities"].append(entity["Text"])
        else:
            extracted["other"].append({"type": entity["Type"], "text": entity["Text"]})

    return {
        "sentiment": sentiment,
        "sentiment_scores": sentiment_scores,
        "entities": extracted
    }


# ─── Phase 2: Bedrock KB Retrieval + Generation ───
def get_travel_info(destination, travel_date, num_travelers, budget, trip_style, sentiment=None):
    """Retrieve from KB and generate itinerary with sentiment-aware responses."""
    query = f"Plan a {trip_style} trip to {destination} for {num_travelers} people with a budget of {budget}"
    retrieve_response = bedrock_agent.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}}
    )
    chunks = []
    for result in retrieve_response.get("retrievalResults", []):
        text = result.get("content", {}).get("text", "")
        if text:
            chunks.append(text)
    if not chunks:
        return "I could not find relevant travel information. Try a different destination."
    context = " ".join(chunks)

    tone_instruction = ""
    if sentiment == "NEGATIVE":
        tone_instruction = "The user seems frustrated or unhappy. Be extra helpful, empathetic, and reassuring. "
    elif sentiment == "POSITIVE":
        tone_instruction = "The user is excited! Match their enthusiasm and add fun suggestions. "
    elif sentiment == "MIXED":
        tone_instruction = "The user seems uncertain. Be clear, organized, and offer flexible options. "

    prompt = f"{tone_instruction}Using this travel info: {context} --- Answer this: {query}. Departure: {travel_date}."
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    })
    model_response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )
    response_body = json.loads(model_response["body"].read())
    return response_body["content"][0]["text"]


# ─── Lambda Handler ───
def lambda_handler(event, context):
    intent = event["sessionState"]["intent"]
    intent_name = intent["name"]
    slots = intent["slots"]

    user_input = event.get("inputTranscript", "")

    # ─── Phase 7: Check user input with Guardrail ───
    if user_input:
        guardrail_check = apply_guardrail(user_input, source="INPUT")
        if guardrail_check["blocked"]:
            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {"name": intent_name, "state": "Fulfilled"}
                },
                "messages": [{"contentType": "PlainText", "content": guardrail_check["message"]}]
            }

    # ─── Phase 6: Handle GetRecommendations intent ───
    if intent_name == "GetRecommendations":
        user_id = slots.get("user_id", {})
        if user_id and user_id.get("value"):
            user_id = user_id["value"]["interpretedValue"]
        else:
            user_id = "user_001"

        recommendations = get_recommendations(user_id)

        if recommendations:
            message = f"🌍 **Personalized Recommendations for you:**\n\n"
            message += f"Based on your travel history, here are your top destinations:\n\n"
            for i, rec in enumerate(recommendations, 1):
                destination_name = rec.replace("-", " ").title()
                message += f"{i}. **{destination_name}**\n"
            message += f"\nWould you like me to plan a trip to any of these?"
        else:
            message = "I don't have enough travel history to make recommendations yet. Tell me where you'd like to go!"

        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": "GetRecommendations", "state": "Fulfilled"}
            },
            "messages": [{"contentType": "PlainText", "content": message}]
        }

    # ─── Phase 5: Handle AnalyzePhoto intent ───
    if intent_name == "AnalyzePhoto":
        s3_key = slots.get("photo_key", {})
        if s3_key and s3_key.get("value"):
            s3_key = s3_key["value"]["interpretedValue"]
        else:
            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {"name": "AnalyzePhoto", "state": "Fulfilled"}
                },
                "messages": [{"contentType": "PlainText", "content": "Please provide the filename of your uploaded photo."}]
            }

        try:
            image_analysis = analyze_image(UPLOADS_BUCKET, s3_key)

            labels_text = ", ".join([f"{l['name']} ({l['confidence']}%)" for l in image_analysis["labels"]])
            message = f"📸 **Photo Analysis:**\n\nI detected: {labels_text}\n"

            if image_analysis["landmarks"]:
                message += f"\n🏛️ **Landmarks found:** {', '.join(image_analysis['landmarks'])}\n"

                landmark_info = get_landmark_info(image_analysis["landmarks"], image_analysis["labels"])
                if landmark_info:
                    message += f"\n📖 **Travel Info:**\n{landmark_info}"

        except Exception as e:
            message = f"ERROR analyzing photo: {str(e)}"

        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": "AnalyzePhoto", "state": "Fulfilled"}
            },
            "messages": [{"contentType": "PlainText", "content": message}]
        }

    # ─── Phase 5: Handle AnalyzeDocument intent ───
    if intent_name == "AnalyzeDocument":
        doc_key = slots.get("document_key", {})
        if doc_key and doc_key.get("value"):
            doc_key = doc_key["value"]["interpretedValue"]
        else:
            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {"name": "AnalyzeDocument", "state": "Fulfilled"}
                },
                "messages": [{"contentType": "PlainText", "content": "Please provide the filename of your uploaded document."}]
            }

        try:
            doc_analysis = extract_document_text(UPLOADS_BUCKET, doc_key)
            message = f"📄 **Document Analysis:**\n\n{doc_analysis}"

        except Exception as e:
            message = f"ERROR analyzing document: {str(e)}"

        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": "AnalyzeDocument", "state": "Fulfilled"}
            },
            "messages": [{"contentType": "PlainText", "content": message}]
        }

    # ─── Phase 7: Handle EncryptPII intent ───
    if intent_name == "EncryptPII":
        pii_data = slots.get("pii_data", {})
        if pii_data and pii_data.get("value"):
            pii_data = pii_data["value"]["interpretedValue"]
        else:
            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {"name": "EncryptPII", "state": "Fulfilled"}
                },
                "messages": [{"contentType": "PlainText", "content": "Please provide the sensitive data to encrypt."}]
            }

        encrypted = encrypt_pii(pii_data)
        if encrypted:
            message = f"🔒 **Data Encrypted Successfully**\n\nYour sensitive information has been securely encrypted using AWS KMS.\n\n**Encrypted token:** `{encrypted[:50]}...`\n\n✅ Original data is NOT stored — only the encrypted version is retained."
        else:
            message = "ERROR: Unable to encrypt data. Please try again."

        return {
            "sessionState": {
                "dialogAction": {"type": "Close"},
                "intent": {"name": "EncryptPII", "state": "Fulfilled"}
            },
            "messages": [{"contentType": "PlainText", "content": message}]
        }

    # ─── Phase 1-4: Handle PlanTrip intent ───
    analysis = None
    if user_input:
        analysis = analyze_user_input(user_input)

    destination = slots["destination"]["value"]["interpretedValue"]
    travel_date = slots["travel_date"]["value"]["interpretedValue"]
    num_travelers = slots["num_travelers"]["value"]["interpretedValue"]
    budget = slots["budget"]["value"]["interpretedValue"]
    trip_style = slots.get("trip_style", {})
    if trip_style and trip_style.get("value"):
        trip_style = trip_style["value"]["interpretedValue"]
    else:
        trip_style = "general"

    if analysis and analysis["entities"]["locations"]:
        detected_location = analysis["entities"]["locations"][0]
        if destination.lower() in ["somewhere", "anywhere", ""]:
            destination = detected_location

    try:
        sentiment = analysis["sentiment"] if analysis else None
        result = get_travel_info(destination, travel_date, num_travelers, budget, trip_style, sentiment)

        # Phase 7: Check AI output with Guardrail
        guardrail_output = apply_guardrail(result, source="OUTPUT")
        if guardrail_output["blocked"]:
            result = guardrail_output["message"]

        if analysis and analysis["sentiment"] == "NEGATIVE":
            message = "I understand planning can be stressful — let me help make this easy for you!\n\n" + result
        elif analysis and analysis["sentiment"] == "POSITIVE":
            message = "Love the enthusiasm! Here's your trip plan:\n\n" + result
        else:
            message = result

        # Phase 4: Add translated phrases
        phrases = get_translated_phrases(destination)
        if phrases:
            phrase_section = "\n\n---\n## 🗣️ Useful Phrases\n"
            for p in phrases:
                phrase_section += f"- **{p['english']}** → {p['translated']}\n"
            message += phrase_section

        # Phase 4: Generate audio version
        audio_url = generate_audio(result, destination)
        if audio_url:
            message += f"\n\n🎧 **Listen to your itinerary:** {audio_url}"

        # Phase 6: Add personalized recommendations
        session_user = event.get("sessionState", {}).get("sessionAttributes", {}).get("user_id", "user_001")
        recommendations = get_recommendations(session_user)
        if recommendations:
            rec_section = "\n\n---\n## 🌍 You Might Also Like\n"
            for rec in recommendations[:3]:
                if rec.lower() != destination.lower():
                    rec_section += f"- **{rec.replace('-', ' ').title()}**\n"
            message += rec_section

    except Exception as e:
        message = f"ERROR: {str(e)}"

    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {"name": "PlanTrip", "state": "Fulfilled"},
            "sessionAttributes": {
                "sentiment": analysis["sentiment"] if analysis else "UNKNOWN",
                "detected_entities": json.dumps(analysis["entities"]) if analysis else "{}",
                "audio_url": audio_url if 'audio_url' in dir() else ""
            }
        },
        "messages": [{"contentType": "PlainText", "content": message}]
    }

