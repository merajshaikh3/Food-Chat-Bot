import mysql.connector
global cnx

cnx = mysql.connector.connect(
    host='localhost', #e.g. 'localhost' or an IP address
    user='root',
    password='root123',
    database='pandeyji_eatery' 
)

def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        #Calling the stored procedure
        cursor.callproc("insert_order_item", (food_item,quantity,order_id))

        #Committing the changes
        cnx.commit()

        #Closing the cursor
        cursor.close()

        print("Order item inserted successfully!")

        return 1
    
    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        cnx.rollback()

        return -1
    
    except Exception as e:
        print(f"An error occurred: {e}")
        # Rollback changes if necessary
        cnx.rollback()

        return -1

def get_total_order_price(order_id):
    cursor = cnx.cursor()

    #Executing the SQL query to get the total order price
    #get_total_order_price() is a user defined function written by codebasics in SQL to calculate total order price
    #You can go to the mySQL database and check the left tab under functions
    #He did not show how he created this function
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    #Fetching the result
    result = cursor.fetchone()[0]

    #Closing the cursor
    cursor.close()

    return result 



def get_next_order_id():
    cursor = cnx.cursor()

    # Executing the SQL query to get the next available order_id
    query = "SELECT MAX(order_id) from orders"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    # Returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1

def insert_order_tracking(order_id, status):
    #This function will take a newly generated order id and insert it into the order tracking table
    cursor = cnx.cursor()

    #Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    #Committing the changes
    cnx.commit()

    #Closing the cursor
    cursor.close()



def get_order_status(order_id: int):

    # Create a cursor object
    cursor = cnx.cursor()

    # Write the SQL query
    query = f"SELECT status FROM order_tracking WHERE order_id = {order_id}"

    # Execute the query
    cursor.execute(query)

    # Fetch the result
    result = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    # the below code line will cut off your db connection after one order id is passed
    # the system was throwing an error if a second order id was passed
    # cnx.close() 

    if result is not None:
        return result[0]
    else:
        return None