
import json
import boto3

KNOWLEDGE_BASE_ID = "UNCTZY1UHS"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
comprehend = boto3.client("comprehend", region_name=REGION)


# ─── Phase 3: Comprehend — Sentiment + Entity Extraction ───
def analyze_user_input(text):
    """Detect sentiment and extract entities from user input."""
    # Detect sentiment
    sentiment_response = comprehend.detect_sentiment(
        Text=text,
        LanguageCode="en"
    )
    sentiment = sentiment_response["Sentiment"]
    sentiment_scores = sentiment_response["SentimentScore"]

    # Detect entities (locations, dates, quantities, etc.)
    entities_response = comprehend.detect_entities(
        Text=text,
        LanguageCode="en"
    )
    entities = entities_response["Entities"]

    # Organize extracted entities by type
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

    # Adjust tone based on sentiment
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

    # Get the raw user input for Comprehend analysis
    user_input = event.get("inputTranscript", "")

    # Analyze user input with Comprehend
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

    # If Comprehend found entities, use them to enhance/override slots
    if analysis and analysis["entities"]["locations"]:
        # Use first detected location if slot is generic
        detected_location = analysis["entities"]["locations"][0]
        if destination.lower() in ["somewhere", "anywhere", ""]:
            destination = detected_location

    try:
        sentiment = analysis["sentiment"] if analysis else None
        result = get_travel_info(destination, travel_date, num_travelers, budget, trip_style, sentiment)

        # Add sentiment-aware prefix
        if analysis and analysis["sentiment"] == "NEGATIVE":
            message = "I understand planning can be stressful — let me help make this easy for you!\n\n" + result
        elif analysis and analysis["sentiment"] == "POSITIVE":
            message = "Love the enthusiasm! Here's your trip plan:\n\n" + result
        else:
            message = result

    except Exception as e:
        message = f"ERROR: {str(e)}"

    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {"name": "PlanTrip", "state": "Fulfilled"},
            "sessionAttributes": {
                "sentiment": analysis["sentiment"] if analysis else "UNKNOWN",
                "detected_entities": json.dumps(analysis["entities"]) if analysis else "{}"
            }
        },
        "messages": [{"contentType": "PlainText", "content": message}]
    }

