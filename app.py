import os
from flask import Flask, request, jsonify, render_template
from groq import Groq

app = Flask(__name__)

# Set your API key (you can hide this or load it from an environment variable for production)
os.environ["GROQ_API_KEY"] = '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'

# Define a watermarking function that inserts a byte sequence at frequent intervals
def apply_byte_watermark(generated_text, interval=5):
    """
    Adds an invisible watermark to the generated text at frequent intervals using byte sequences.
    The watermark is inserted after every 'interval' number of words based on byte positions.
    """
    # Invisible watermark (using BOM as the watermark byte sequence)
    byte_watermark = b'\xEF\xBB\xBF'  # BOM (Byte Order Mark) as an invisible watermark
    
    # Convert the generated text into bytes
    text_bytes = generated_text.encode('utf-8')
    
    # Create a mutable bytearray to insert watermark
    watermarked_text = bytearray(text_bytes)
    
    # Calculate approximate word positions based on spaces (split text by space)
    byte_position = 0  # Start at the beginning of the byte array
    word_count = 0  # This will track the number of words we encounter
    
    while byte_position < len(watermarked_text):
        # Check if the current byte corresponds to a space (end of a word)
        if watermarked_text[byte_position] in [32]:  # ASCII space byte
            word_count += 1
        
        # Insert watermark at the interval position (after every 'interval' words)
        if word_count >= interval:
            # Insert watermark byte sequence at this position
            watermarked_text[byte_position:byte_position] = byte_watermark
            byte_position += len(byte_watermark)  # Adjust byte_position after insertion
            word_count = 0  # Reset word counter after inserting watermark
        
        # Move to the next byte
        byte_position += 1

    # Convert the byte array back to a string
    return watermarked_text.decode('utf-8', errors='ignore')




# Initialize the Groq client
client = Groq()

# Define a function to get the output and watermark it
def generate_and_watermark(user_input):
    try:

        user_input = f"{user_input}"

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

        generated_text = f"Sure! Here is the information:\n\u200B{generated_text}\u200B\n\nThank you for using our service, if you have any questions or need further assistance, feel free to ask!"
        
        # Apply watermark to the generated text
        watermarked_text = apply_byte_watermark(generated_text)
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
    
    # Define the watermark byte sequence (BOM) and Unicode character
    watermark_bytes = b'\xEF\xBB\xBF'
    zero_width_space = '\u200B'  # Zero Width Space character
    phrase_at_start = "Sure! Here is the information:"
    phrase_at_end = "Thank you for using our service, if you have any questions or need further assistance, feel free to ask!"
    
    # Check for the presence of watermark byte sequence (BOM)
    text_bytes = text.encode('utf-8')
    watermark_found = watermark_bytes in text_bytes
    
    # Check for the presence of Zero Width Space or phrases at the beginning or end
    starts_with_phrase = text.startswith(phrase_at_start)
    ends_with_phrase = text.endswith(phrase_at_end)
    contains_zero_width_space = zero_width_space in text
    
    # Combine the conditions to determine if watermark is detected
    if watermark_found or contains_zero_width_space or starts_with_phrase or ends_with_phrase:
        result = {"message": "This text is AI-generated."}
    else:
        result = {"message": "No AI watermark detected in this text."}

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)