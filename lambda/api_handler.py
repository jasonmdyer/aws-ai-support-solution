
import json
import boto3
import uuid
import base64

lex_client = boto3.client("lexv2-runtime", region_name="us-east-1")
lambda_client = boto3.client("lambda", region_name="us-east-1")
s3_client = boto3.client("s3", region_name="us-east-1")
rekognition_client = boto3.client("rekognition", region_name="us-east-1")

BOT_ID = "XVFZTLXLFO"
BOT_ALIAS_ID = "TSTALIASID"
LOCALE_ID = "en_US"
UPLOAD_BUCKET = "travel-planner-uploads-jmd"
MAIN_LAMBDA = "TravelPlannerFunction"

# Labels that indicate a document (not a scenic photo)
DOCUMENT_LABELS = {"Document", "Page", "Text", "Invoice", "Receipt", "Letter", "Paper", "File", "Form", "Menu", "Ticket", "Label"}

# CORS headers
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
}


def lambda_handler(event, context):
    """Bridge between API Gateway and Lex bot + file upload handler."""
    
    # Handle OPTIONS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }
    
    # Determine which endpoint was called
    path = event.get("path", "")
    
    if "/upload" in path:
        return handle_upload(event)
    else:
        return handle_chat(event)


def handle_upload(event):
    """Handle file upload to S3, detect type, and trigger appropriate analysis."""
    
    try:
        body = json.loads(event.get("body", "{}"))
        filename = body.get("filename", "upload.jpg")
        file_content = body.get("fileContent", "")
        content_type = body.get("contentType", "image/jpeg")
        
        # Decode base64 file content
        file_bytes = base64.b64decode(file_content)
        
        # Upload to S3
        file_key = f"uploads/{filename}"
        s3_client.put_object(
            Bucket=UPLOAD_BUCKET,
            Key=file_key,
            Body=file_bytes,
            ContentType=content_type
        )
        
        # Determine analysis type
        is_image = content_type.startswith("image/")
        
        if is_image:
            # First, run Rekognition to check if it's a document or a photo
            intent_name = detect_image_type(file_bytes)
        else:
            # Non-image files (PDFs, etc.) go straight to document analysis
            intent_name = "AnalyzeDocument"
        
        # Set the correct slot name based on intent
        if intent_name == "AnalyzeDocument":
            slot_name = "document_key"
        else:
            slot_name = "photo_key"
        
        # Call the main Lambda directly
        lex_event = {
            "sessionState": {
                "intent": {
                    "name": intent_name,
                    "state": "ReadyForFulfillment",
                    "slots": {
                        slot_name: {
                            "value": {
                                "interpretedValue": file_key,
                                "originalValue": file_key,
                                "resolvedValues": [file_key]
                            }
                        }
                    }
                }
            },
            "inputTranscript": f"Analyze {filename}",
            "bot": {
                "id": BOT_ID,
                "name": "TravelPlannerBot",
                "version": "DRAFT",
                "localeId": LOCALE_ID
            }
        }
        
        # Invoke main Lambda
        response = lambda_client.invoke(
            FunctionName=MAIN_LAMBDA,
            InvocationType="RequestResponse",
            Payload=json.dumps(lex_event)
        )
        
        # Parse the response
        payload = json.loads(response["Payload"].read())
        messages = payload.get("messages", [])
        
        if messages:
            bot_reply = "\n".join([msg.get("content", "") for msg in messages])
        else:
            bot_reply = "File uploaded successfully but I couldn't analyze it. Please try again."
        
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": bot_reply})
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": f"Upload error: {str(e)}"})
        }


def detect_image_type(file_bytes):
    """Use Rekognition to determine if an image is a document or a scenic photo."""
    
    try:
        response = rekognition_client.detect_labels(
            Image={"Bytes": file_bytes},
            MaxLabels=10,
            MinConfidence=80
        )
        
        labels = {label["Name"] for label in response.get("Labels", [])}
        
        # If any document-related labels are detected, treat as document
        if labels & DOCUMENT_LABELS:
            return "AnalyzeDocument"
        else:
            return "AnalyzePhoto"
            
    except Exception:
        # If Rekognition fails, default to photo analysis
        return "AnalyzePhoto"


def handle_chat(event):
    """Handle chat messages via Lex."""
    
    body = json.loads(event.get("body", "{}"))
    user_message = body.get("message", "")
    user_id = body.get("userId", str(uuid.uuid4()))
    
    try:
        # Send message to Lex
        response = lex_client.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId=user_id,
            text=user_message
        )
        
        # Extract the bot's response messages
        messages = response.get("messages", [])
        if messages:
            bot_reply = "\n".join([msg.get("content", "") for msg in messages])
        else:
            # Check session state for dialog action
            session_state = response.get("sessionState", {})
            dialog_action = session_state.get("dialogAction", {})
            intent = session_state.get("intent", {})
            
            # If Lex is eliciting a slot, build a prompt
            if dialog_action.get("type") == "ElicitSlot":
                slot_name = dialog_action.get("slotToElicit", "")
                bot_reply = f"I'd like to help plan your trip! Could you tell me your {slot_name.replace('_', ' ')}?"
            elif dialog_action.get("type") == "Close":
                bot_reply = "Your request has been processed!"
            else:
                bot_reply = "I'm your AI Travel Planner! Try saying 'Plan a trip to Japan' or 'Get my recommendations'."
        
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": bot_reply})
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": f"Error: {str(e)}"})
        }

