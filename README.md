# Food Chat Bot

This project is a food ordering chatbot that uses Dialogflow to interact with users, MySQL to store menu details, and FastAPI as the web development framework. The chatbot can handle various intents such as creating an order, tracking an order, and cancelling an order. This project is implemented by following the [YouTube tutorial by codebasics](https://www.youtube.com/watch?v=2e5pQqBvGco&ab_channel=codebasics).

![Website_Screenshot](https://github.com/merajshaikh3/Food-Chat-Bot/assets/47921927/2c583c70-1a90-4850-8adc-f8d712b670a9)

## Features
* **Order Creation:** Users can create new orders through the chatbot.
* **Order Tracking:** Users can track their existing orders.
* **Order Cancellation:** Users can cancel their orders if needed.

## Technology Stack
* **Dialogflow:** Used to create and train the chatbot.
* **MySQL:** Stores menu details and other relevant data.
* **FastAPI:** Acts as the web development framework.
* **ngrok:** Used to expose the local API endpoint securely over HTTPS for Dialogflow fulfillment.

## File Structure
* **db_helper.py:** Contains Python code to add and retrieve data from the MySQL database.
* **generic_helper.py:** Contains Python code to process text.
* **main.py:** Processes data from Dialogflow and makes necessary updates to the database (handle_request is the path function that interacts with Dialogflow and coordinates with other functions to place, cancel and track user orders)
* **frontend/home.html:** Contains the front-end HTML where the chatbot will appear.

  
