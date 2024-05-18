import re


#session_str is the url from which session_id needs to be extracted
def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""

def get_str_from_food_dict(food_dict):
    return ",".join([f"{int(value)} {key}" for key, value in food_dict.items()])

# testing the extract_session_id function
if __name__ == "__main__":
    print(get_str_from_food_dict({"samose":2, "chhole": 5}))
    #session_id = extract_session_id("projects/mira-chatbot-for-food-del-gdpe/agent/sessions/123/contexts/ongoing-order")
    #print(session_id)