import os
import requests
from time import sleep

def send_to_llm(prompt,placeholders):
    HF_API_TOKEN = os.getenv("HF_API_TOKEN")
    HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    
    if not HF_API_TOKEN:
        return "Error: Missing Hugging Face API token"

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    system_prompt = f"""You are a security assistant. Use ONLY these placeholders: {", ".join(placeholders)}.
    Never create new placeholders or brackets. Respond in plain text. Avoid template markers like ". :" """
    
    payload = {
        "inputs": f"""<s>[INST] <<SYS>>{system_prompt}<</SYS>>{prompt}[/INST]""",
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.1,  # Lower temperature for strict compliance
            "stop": ["</s>", "[INST]", "[/INST]"],
            "bad_words_ids": [[28705], [28789]],  # Block [ and ]
        }
    }

    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload
        )
        raw_response = response.json()[0]['generated_text']

        # Add cleaning steps
        clean_response = raw_response.split("[/INST]")[-1] \
                          .replace("[INST]", "") \
                          .replace("</s>", "") \
                          .strip()
        
        return clean_response

        # Handle model loading
        if response.status_code == 503:
            return "Model is loading, please try again in 20 seconds"

        return response.json()[0]['generated_text']

    except Exception as e:
        return f"API Error: {str(e)}"
