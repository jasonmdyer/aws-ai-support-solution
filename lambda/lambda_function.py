
import json
import boto3

KNOWLEDGE_BASE_ID = "UNCTZY1UHS"
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-1"

bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)

def get_travel_info(destination, travel_date, num_travelers, budget, trip_style):
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
    prompt = f"Using this travel info: {context} --- Answer this: {query}. Departure: {travel_date}."
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

def lambda_handler(event, context):
    intent = event["sessionState"]["intent"]
    slots = intent["slots"]
    destination = slots["destination"]["value"]["interpretedValue"]
    travel_date = slots["travel_date"]["value"]["interpretedValue"]
    num_travelers = slots["num_travelers"]["value"]["interpretedValue"]
    budget = slots["budget"]["value"]["interpretedValue"]
    trip_style = slots.get("trip_style", {})
    if trip_style and trip_style.get("value"):
        trip_style = trip_style["value"]["interpretedValue"]
    else:
        trip_style = "general"
    try:
        result = get_travel_info(destination, travel_date, num_travelers, budget, trip_style)
        message = result
    except Exception as e:
        message = f"ERROR: {str(e)}"
    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {"name": "PlanTrip", "state": "Fulfilled"}
        },
        "messages": [{"contentType": "PlainText", "content": message}]
    }

