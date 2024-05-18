# Restart video from 1:36:00
# Restart video from 2:11:00
# Restart video from 2:46:00

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {}

@app.post("/") # I was initially making an error by typing the 'get' method here
async def handle_request(request: Request):
    #Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from DialogFlow
    # in diagnostic info check the fulfillment request tab

    #intent represents the intent which was triggered when the user typed in something
    #since we are writing code for tracking order, we're only interested in tracking intent
    intent = payload['queryResult']['intent']['displayName']

    #parameter here, represents the number in the user's query. In our case it is order id.
    #paramaeters is a dictionary
    parameters = payload['queryResult']['parameters']

    #output context represents the active context at the time (after intent has been decided)
    output_contexts = payload['queryResult']['outputContexts']

    #output contexts is a list of dictionaries
    #output_contexts[0] => gets the first element of the dictionary
    #output_contexts[0]['name'] => gets the value for the 'name' key in the first element of the list
    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])


    # we are creating this intent handler dictionary to avoid multiple if-else statements
    # by creating a dict you can do something as simple as x = dict[context] and call any function you like (let's see if this is true)
    intent_handler_dict = {
        "order.add - context: ongoing-order": add_to_order,
        "order.remove - context: ongoing-order": remove_from_order,
        "order.complete - context: ongoing-order": complete_order,
        "track.order - context: ongoing-tracking": track_order
    }

    # The below return function returns the required function from dictionary and passes the 'parameter' variable to it
    # if intent = "order.add...." then intent_handler_dict[intent](parameters) => add_to_order(parameters)
    # as you can see in the above comment, 'parameters' & 'session_id' is passed to 'add_to_order' function as arguments
    return intent_handler_dict[intent](parameters, session_id)


def add_to_order(parameters: dict, session_id: str):
    # you get this info from the diagnostics api
    food_items = parameters["food-item"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify the food items and quantities properly. Seems like some of the food items items don't have quantities" 
    else:
        # new_food_dict is different from the inprogress_dict we created above
        # inprogress_dict will contain all orders until they are confirmed
        # new_food_dict will only contain incremental orders
        # another way to think about this is that: new_food_dict will store incremental order and then dump it into the inprogress-dict
        # an analogy: new_food_dict is like a truck taking items to a warehouse to store. Here the warehouse is inprogress_dict
        # incremental orders => the first order user is placing, add on orders etc
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            #since this is a dictionary we have made a copy and then updated to it instead of directly updating the original dictionary
            #it has something to do with mutability/immutability of dictionaries
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])

        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having some trouble finding your order. Sorry! Can you place your order again?"
        })
    
    #we'll first need to get the current order details of the session/user before we can delete it
    current_order = inprogress_orders[session_id]
    #this is the list of food items that need to be deleted
    #we'll get this information from dialogflow in API response
    food_items = parameters["food-item"]

    #will keep track of items that were removed from the current order
    #if you need to delete more than 1 item then list becomes helpful in handling the data
    removed_items = []
    
    #will keep track of non-existent items that user wanted to delete from current order
    #e.g. "delete dosa from the order" current_order = pizza, lassi
    #if more than 1 such item exists then storing it in a list becomes helpful
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            pass
        else:
            removed_items.append(item)
            del current_order[item]
    
    if len(removed_items) > 0:
        fulfillment_text = f"Removed {','.join(removed_items)} from your order!"

    if len(no_such_items) > 0:
        fulfillment_text = f"Your current order does not have {','.join(no_such_items)}"

    if len(current_order) == 0:
        fulfillment_text += "Your order is empty" 
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f"Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def complete_order(parameters: dict, session_id: str):
    # using the session id you need to find a key in the inprogress orders
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having trouble find your order. Sorry! Can you place a new order"
    else:
        order = inprogress_orders[session_id]
        # this is the order_id we'll be returning to the user after they confirm their order
        order_id = save_to_db(order) #this is a new function which will save the order to db

        if order_id == -1:
           fulfillment_text = "Sorry, I couldn't process your order due to a backend error. \nPlease place a new order"
        else:
            #get_total_order_price is the db_helper function which will call the user defined function in MySQL to fetch the total price of the order
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome! We have placed your order." \
                                f" Here is your order id # {order_id}." \
                                f"Your order total is {order_total} which you can pay the time of delivery."

    #once order is added to db it will be removed from the inprogress_orders dictionary
    del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def save_to_db(order: dict):
    #This function will help save the final order to the db
    next_order_id = db_helper.get_next_order_id()

    #this for-loop will take each item along with its order id and insert it into the db
    #remeber that before inserting the food entry we also need to know its unit price
    #without the unit price we won't be able to calculate the total price
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    #we will now add this order to the tracking table as well
    #after sometime when the user enters their tracking id for the status we should be able to fetch the tracking order status
    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id
    

    # we are moving away from this because the if-else route is resulting in multiple if-else statements
    """
    if intent == "track.order - context: ongoing-tracking":
        return track_order(parameters) 

        # the below code was written just to check if the webhook call is working or not
        
        return JSONResponse(content={
            "fulfillmentText": f"Received =={intent}== in the backend"
        })
        
    elif intent == "order.add - context: ongoing-order":
        pass
    elif intent == "order.complete - context: ongoing-order":
        pass
    elif intent == "order.remove - context: ongoing-order":
        pass
    """
# DialogFlow does not have a buffer/transient memory to store in-progress order before it is placed
# We will have to figure out a way to store in-progress order in our backend before it is finalised and stored in a db
# One way is to store the transient data in the db
# Probably you can add an additional column in the 'orders' db called 'status' and have values like 'in-progress' and 'complete'
# Not sure why, but codebasics has not decided to go that path, instead they've decided to store the temporary information in a db at a session level
# Each session_id represents one E2E conversation with the bot (this isn't an exact definition - generally it is 30 min i.e. any order placed in 30 mins time frame from a particular user after opening the app will go to the same session id)
# The below dictionary is a nested dictionary. 
# In the outer dictionary session_id is key and order quantity is value whereas in the inner dictionary the food item is key and its quantity is value.
"""
inprogress_prders = {
    "session_id_1": {"pizzas":2,"samosa":1},
    "session_id_2": {"chhole": 1}
} 
"""

def track_order(parameters: dict, session_id: str):
    order_id = parameters['number']
    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"
    
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# POST APIs cannot be seen in the browser. Only GET APIs can be seen.
    
