from flask import Flask, request, jsonify
from anonymization import anonymize_text
from llm_client import send_to_llm
import json

from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
#CORS(app, resources={r"/process": {"origins": os.getenv('ALLOWED_ORIGINS', '*')}})
# Production CORS
#CORS(app, resources={r"/process": {"origins": ["https://secure-chat-frontend-navtuq7hp-saras-projects-123e3b12.vercel.app/", "http://localhost:3000"]}})

CORS(app, resources={
    r"/process": {
        "origins": ["https://secure-chat-frontend-navtuq7hp-saras-projects-123e3b12.vercel.app/", "http://localhost:3000"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})
# ... rest of your existing backend code ...  


@app.route('/process', methods=['POST'])
def process_request():
    try:
        data = request.json
        original_prompt = data.get("prompt", "")
        
        # Anonymization
        anonymized_prompt, mapping = anonymize_text(original_prompt)
        
        print("anonymized_prompt : ")
        print(anonymized_prompt)

        # Add mapping IDs to prompt
        #formatted_prompt = f"{anonymized_prompt}\n\nMapping: {json.dumps(mapping)}"
        
        # LLM Interaction
        #llm_response = send_to_llm(anonymized_prompt)

        # Extract placeholders from mapping
        mapped_placeholders = [item["anonymized"] for item in mapping]
        
        # Pass to LLM client
        llm_response = send_to_llm(
            anonymized_prompt,
            placeholders=mapped_placeholders  # Add this parameter
        )


        print("Mapping:", json.dumps(mapping, indent=2))
        print("LLM Response Before Cleaning:", llm_response)


       
        
        # Recontextualization with exact matches
        import re

        # Modify the recontextualization section
        for item in mapping:
            # Match exact placeholder including special characters
            pattern = re.escape(item["anonymized"])
            # Use lookaheads/lookbehinds to match whole words only
            llm_response = re.sub(
                rf'{pattern}',  # Negative lookbehind/ahead for word chars
                item["original"], 
                llm_response
            )

        #llm_response = re.sub(r'\[([A-Z_]+)_\d+\]', '', llm_response)
        llm_response = re.sub(r'<\w+_\d+>', '', llm_response)


        print("Final Response:", llm_response)



        return jsonify({
            "response": llm_response,
            "anonymized_prompt": anonymized_prompt,
            "mapping": mapping
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    #app.run(debug=True)

    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
