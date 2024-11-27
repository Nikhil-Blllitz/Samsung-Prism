import os
from flask import Flask, request, jsonify, render_template
from groq import Groq

app = Flask(__name__)

# Set your API key (you can hide this or load it from an environment variable for production)
os.environ["GROQ_API_KEY"] = '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'

# Define a watermarking function that inserts a single invisible Unicode character at frequent intervals
def apply_unicode_watermark(generated_text, interval=5):
    """
    Adds an invisible Unicode watermark (zero-width joiner) to the generated text at frequent intervals.
    The watermark is inserted after every 'interval' number of words.
    """
    # Unicode invisible characters (zero-width joiner)
    unicode_watermark = "\u200C"  # Single invisible watermark character
    
    words = generated_text.split()  # Split the text into words
    watermarked_text = []
    
    # Insert watermark after every 'interval' number of words
    for i in range(0, len(words), interval):
        # Add words to the list
        watermarked_text.extend(words[i:i+interval])
        # Add a single invisible watermark after each group of words
        if i + interval < len(words):  # Don't add watermark at the end if no additional words
            watermarked_text.append(unicode_watermark)
    
    # Join the words back into a string with single spaces between them
    return " ".join(watermarked_text)

# Initialize the Groq client
client = Groq()

# Define a function to get the output and watermark it
def generate_and_watermark(user_input):
    try:
        # Use Groq to generate text with the "llama-3.2-1b-preview" model
        completion = client.chat.completions.create(
            model="llama-3.2-1b-preview",  # The 1B model you want to use
            messages=[{"role": "user", "content": user_input}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,  # We want to get the full response, not streamed
        )

        # Groq response returns a list of completions, take the first one
        generated_text = completion.choices[0].message.content
        
        # Apply watermark to the generated text
        watermarked_text = apply_unicode_watermark(generated_text)
        return watermarked_text
    
    except Exception as e:
        raise Exception(f"Text generation failed: {str(e)}")

@app.route('/')
def home():
    return render_template('index.html')  # Default generation page

@app.route('/watermark-detector')
def watermark_detector():
    return render_template('detect_watermark.html')  # Watermark detection page

@app.route('/generate', methods=['POST'])
def generate_text():
    data = request.get_json()
    prompt = data.get("prompt", "")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        # Generate text and apply watermark
        watermarked_text = generate_and_watermark(prompt)
    except Exception as e:
        return jsonify({"error": f"Text generation failed: {str(e)}"}), 500

    return jsonify({
        "watermarked_text": watermarked_text
    })

@app.route('/detect', methods=['POST'])
def detect_watermark():
    data = request.get_json()  # Receive JSON data from the client
    text = data.get("text", "")
    
    # Check for the presence of the Unicode watermark (\u200C)
    if "\u200C" in text:
        result = {"message": "This text is AI-generated."}
    else:
        result = {"message": "No AI watermark detected in this text."}

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
