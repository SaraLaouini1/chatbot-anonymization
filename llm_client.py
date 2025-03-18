import os
from openai import OpenAI

def send_to_llm(prompt, placeholders):
    
    try:

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
        system_message = f"""You are a intelligent assistant. Follow these rules:
    1. Use ONLY these placeholders: {", ".join(placeholders) if placeholders else 'none' }
    2. Never create new placeholders
    3. Maintain original placeholder format
    4. Respond in clean plain text without markdown"""


        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"OpenAI Error: {str(e)}"
