import json

def lambda_handler(event, context):
    slots = event['sessionState']['intent']['slots']
    destination = slots['destination']['value']['interpretedValue']
    travel_date = slots['travel_date']['value']['interpretedValue']
    num_travelers = slots['num_travelers']['value']['interpretedValue']
    budget = slots['budget']['value']['interpretedValue']
    trip_style = slots['trip_style']['value']['interpretedValue']
    per_person = int(budget) // int(num_travelers)
    message = "Here's your trip summary:" + chr(10) + chr(10) + "Destination: " + destination + chr(10) + "Date: " + travel_date + chr(10) + "Travelers: " + num_travelers + chr(10) + "Total Budget: $" + budget + chr(10) + "Per Person: $" + str(per_person) + chr(10) + "Trip Style: " + trip_style + chr(10) + chr(10) + "I'll start building your " + trip_style + " itinerary for " + destination + ". Stay tuned for recommendations!"
    response = {"sessionState": {"dialogAction": {"type": "Close"}, "intent": {"name": event['sessionState']['intent']['name'], "state": "Fulfilled"}}, "messages": [{"contentType": "PlainText", "content": message}]}
    return response
