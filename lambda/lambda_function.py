
import json
import boto3

KNOWLEDGE_BASE_ID = "UNCTZY1UHS"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"
AUDIO_BUCKET = "travel-planner-audio"

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
comprehend = boto3.client("comprehend", region_name=REGION)
translate_client = boto3.client("translate", region_name=REGION)
polly_client = boto3.client("polly", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

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
    # Trim text to Polly's limit (3000 chars for synthesize_speech)
    clean_text = text[:2900].replace("#", "").replace("*", "").replace("|", "")

    try:
        response = polly_client.synthesize_speech(
            Text=clean_text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            Engine="standard"
        )

        # Save audio to S3
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
    slots = intent["slots"]

    user_input = event.get("inputTranscript", "")

    # Phase 3: Analyze sentiment + entities
    analysis = None
    if user_input:
        analysis = analyze_user_input(user_input)

    # Extract slot values
    destination = slots["destination"]["value"]["interpretedValue"]
    travel_date = slots["travel_date"]["value"]["interpretedValue"]
    num_travelers = slots["num_travelers"]["value"]["interpretedValue"]
    budget = slots["budget"]["value"]["interpretedValue"]
    trip_style = slots.get("trip_style", {})
    if trip_style and trip_style.get("value"):
        trip_style = trip_style["value"]["interpretedValue"]
    else:
        trip_style = "general"

    # Comprehend entity override
    if analysis and analysis["entities"]["locations"]:
        detected_location = analysis["entities"]["locations"][0]
        if destination.lower() in ["somewhere", "anywhere", ""]:
            destination = detected_location

    try:
        sentiment = analysis["sentiment"] if analysis else None
        result = get_travel_info(destination, travel_date, num_travelers, budget, trip_style, sentiment)

        # Sentiment-aware prefix
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

