from openai import OpenAI
import requests


def openai_call(sys_prompt, user_prompt, api_key, base_url="https://api.metisai.ir/openai/v1"):
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content


def metis_call(api_key, bot_id, user_prompt):
    url = "https://api.metisai.ir/api/v1/chat/session"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "botId": bot_id,
        "user": None,
        "initialMessages": [
            {
                "type": "USER",
                "content": user_prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print("❌ Metis API Error:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        raise Exception("Failed to get response from Metis API.")

    return response.json()