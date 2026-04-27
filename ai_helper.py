import requests
import re

def strip_markdown(text):
    """Remove markdown so text renders cleanly in plain chat bubbles."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)         # italic
    text = re.sub(r'#{1,6}\s*', '', text)            # headers
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text) # code
    text = re.sub(r'\n{3,}', '\n\n', text)           # extra blank lines
    return text.strip()

def ask_llama(question, context=""):
    try:
        prompt = f"""You are a helpful college assistant chatbot for TMU (Teerthanker Mahaveer University).

Rules:
- Answer clearly and concisely
- Use plain text only, no markdown, no asterisks, no hashtags
- Keep answers short and useful
- If unsure, say "I am not sure about that. Please visit https://www.tmu.ac.in"

Context:
{context}

Question: {question}

Answer:"""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,   # more focused, less random
                    "num_predict": 200    # keep answers short
                }
            },
            timeout=30  # increased from 15 — phi3 can be slow
        )

        if response.status_code != 200:
            return "AI is currently unavailable. Please try again."

        result = response.json()
        answer = result.get("response", "").strip()

        if not answer:
            return "I couldn't generate a proper answer. Please visit https://www.tmu.ac.in"

        return strip_markdown(answer)

    except requests.exceptions.Timeout:
        return "The AI is taking too long. Please try again in a moment."
    except Exception as e:
        print("AI ERROR:", e)
        return "AI is currently unavailable."