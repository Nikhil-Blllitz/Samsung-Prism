import os
from flask import Flask, request, jsonify, render_template
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

app = Flask(__name__)

# Set your API key (you can hide this or load it from an environment variable for production)
os.environ["GROQ_API_KEY"] = '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'

# Define a watermarking function that inserts invisible Unicode watermark (zero-width joiners) after every 5 words
def apply_unicode_watermark(generated_text):
    """
    Adds a Unicode watermark (zero-width joiners) to the generated text.
    The watermark is inserted after every 5 words using invisible Unicode characters.
    """
    # Unicode invisible characters (zero-width joiner)
    unicode_watermark = "\u200C" * 5  # Invisible watermark using zero-width joiners
    
    words = generated_text.split()  # Split the text into words
    watermarked_text = []
    
    # Insert watermark after every 5 words
    for i in range(0, len(words), 5):
        # Add 5 words and then the watermark
        watermarked_text.extend(words[i:i+5])
        watermarked_text.append(unicode_watermark)  # Add the watermark after every 5 words
    
    # Join the words back into a string
    return " ".join(watermarked_text)

# Initialize ChatGroq with your model
llm = ChatGroq(
    model="llama3-70b-8192",  # Llama3 model
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Define a function to get the output and watermark it
def generate_and_watermark(user_input):
    # Define your prompt template with the user's input
    prompt = ChatPromptTemplate.from_messages([("human", user_input)])
    
    # Create a chain that combines the prompt with the LLM
    chain = LLMChain(prompt=prompt, llm=llm)
    
    # Generate output using LangChain
    generated_text = chain.run(input=user_input)

    # Apply the Unicode watermark (zero-width joiner) to the generated text
    watermarked_text = apply_unicode_watermark(generated_text)

    return watermarked_text

@app.route('/')
def home():
    return render_template('index.html')  # Serve the HTML frontend

@app.route('/generate', methods=['POST'])
def generate_text():
    data = request.get_json()  # Receive JSON data from client
    prompt = data.get("prompt", "")
    
    # Check if prompt is not empty
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Generate text with the specified model
    try:
        generated_text = generate_and_watermark(prompt)
    except Exception as e:
        return jsonify({"error": f"Text generation failed: {str(e)}"}), 500

    # Return the generated text and watermarked text as a JSON response
    return jsonify({
        "generated_text": generated_text,
        "watermarked_text": generated_text  # The watermark is embedded in the generated text itself
    })

if __name__ == "__main__":
    app.run(debug=True)
