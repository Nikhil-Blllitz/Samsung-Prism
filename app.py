import os
from flask import Flask, request, jsonify, render_template
from groq import Groq
import random

app = Flask(__name__)

os.environ["GROQ_API_KEY"] = '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'

client = Groq()

def apply_byte_watermark(generated_text, interval=5):
    """Insert byte sequence watermark at regular intervals."""
    byte_watermark = b'\xEF\xBB\xBF'
    text_bytes = generated_text.encode('utf-8')
    watermarked_text = bytearray(text_bytes)
    byte_position = 0
    word_count = 0

    while byte_position < len(watermarked_text):
        if watermarked_text[byte_position] in [32]:
            word_count += 1
        
        if word_count >= interval:
            watermarked_text[byte_position:byte_position] = byte_watermark
            byte_position += len(byte_watermark)
            word_count = 0
        
        byte_position += 1

    return watermarked_text.decode('utf-8', errors='ignore')

def apply_semantic_patterns(text):
    """Apply subtle semantic watermarking patterns that maintain natural text flow."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    processed_paragraphs = []
    
    subtle_starters = [
        "Interestingly,", "Notably,", "Significantly,", "Furthermore,",
        "Meanwhile,", "Subsequently,", "Consequently,", "Additionally,"
    ]
    
    transitions = [
        "in fact", "moreover", "specifically", "particularly",
        "as a result", "consequently", "therefore", "thus"
    ]
    
    context_pairs = [
        ("detailed", "analysis"),
        ("thorough", "examination"),
        ("careful", "consideration"),
        ("comprehensive", "review")
    ]
    
    for i, paragraph in enumerate(paragraphs):
        sentences = [s.strip() for s in paragraph.split('.') if s.strip()]
        processed_sentences = []
        
        for j, sentence in enumerate(sentences):
            words = sentence.split()
            
            if len(words) > 10 and j % 3 == 0 and random.random() < 0.3:
                transition = random.choice(transitions)
                if ',' in sentence:
                    parts = sentence.split(',', 1)
                    sentence = f"{parts[0]}, {transition},{parts[1]}"
                
            analysis_keywords = ["study", "research", "investigation", "examination", "review"]
            if any(keyword in sentence.lower() for keyword in analysis_keywords):
                pair = random.choice(context_pairs)
                if not any(p[0] in sentence.lower() or p[1] in sentence.lower() for p in context_pairs):
                    words.extend(pair)
                    sentence = ' '.join(words)
            
            processed_sentences.append(sentence)
        
        if i % 4 == 0 and not any(s.lower() in processed_sentences[0].lower() for s in subtle_starters):
            starter = random.choice(subtle_starters)
            processed_sentences[0] = f"{starter} {processed_sentences[0]}"
        
        processed_paragraphs.append('. '.join(processed_sentences) + '.')
    
    return '\n\n'.join(processed_paragraphs)

def detect_semantic_patterns(text):
    """Detect semantic watermarking patterns while accounting for natural variation."""
    patterns_detected = {
        'transition_phrases': 0,
        'word_pairs': 0,
        'paragraph_structure': 0
    }
    
    transitions = [
        "in fact", "moreover", "specifically", "particularly",
        "as a result", "consequently", "therefore", "thus"
    ]
    
    word_pairs = [
        ("detailed", "analysis"),
        ("thorough", "examination"),
        ("careful", "consideration"),
        ("comprehensive", "review")
    ]
    
    paragraph_starters = [
        "Interestingly,", "Notably,", "Significantly,", "Furthermore,",
        "Meanwhile,", "Subsequently,", "Consequently,", "Additionally,"
    ]
    
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    for paragraph in paragraphs:
        for transition in transitions:
            if transition.lower() in paragraph.lower():
                patterns_detected['transition_phrases'] += 1
        
        for pair in word_pairs:
            if pair[0].lower() in paragraph.lower() and pair[1].lower() in paragraph.lower():
                patterns_detected['word_pairs'] += 1

        for starter in paragraph_starters:
            if paragraph.lower().startswith(starter.lower()):
                patterns_detected['paragraph_structure'] += 1
    
    total_patterns = sum(patterns_detected.values())
    max_possible = len(paragraphs) * 1.5
    confidence = min(total_patterns / max_possible, 1.0)
    
    return {
        'patterns_detected': patterns_detected,
        'confidence_score': confidence,
        'is_watermarked': confidence > 0.2
    }

def generate_and_watermark(user_input):
    """Generate text and apply both byte and semantic watermarks."""
    try:
        system_prompt = """You are a text generation system that creates natural, flowing text.
        Please provide detailed, well-structured responses with multiple paragraphs where appropriate."""

        completion = client.chat.completions.create(
            model="llama-3.2-1b-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )

        generated_text = completion.choices[0].message.content
        semantically_watermarked = apply_semantic_patterns(generated_text)
        final_text = apply_byte_watermark(semantically_watermarked)
        
        # Add wrapper text with zero-width spaces
        final_text = f"Sure! Here is the information:\n\u200B{final_text}\u200B\n\nThank you for using our service, if you have any questions or need further assistance, feel free to ask!"
        
        return final_text
    except Exception as e:
        raise Exception(f"Text generation failed: {str(e)}")

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/watermark-detector')
def watermark_detector():
    return render_template('detect_watermark.html')

@app.route('/generate', methods=['POST'])
def generate_text():
    """Generate and watermark text based on user prompt."""
    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    try:
        watermarked_text = generate_and_watermark(prompt)
    except Exception as e:
        return jsonify({"error": f"Text generation failed: {str(e)}"}), 500
    return jsonify({"watermarked_text": watermarked_text})

@app.route('/detect', methods=['POST'])
def detect_watermark():
    """Detect both byte and semantic watermarks in text."""
    data = request.get_json()
    text = data.get("text", "")
    
    # Check byte watermarks
    watermark_bytes = b'\xEF\xBB\xBF'
    zero_width_space = '\u200B'
    phrase_at_start = "Sure! Here is the information:"
    phrase_at_end = "Thank you for using our service, if you have any questions or need further assistance, feel free to ask!"
    
    text_bytes = text.encode('utf-8')
    has_byte_watermark = (
        watermark_bytes in text_bytes or
        zero_width_space in text or
        text.startswith(phrase_at_start) or
        text.endswith(phrase_at_end)
    )
    
    # Check semantic patterns
    semantic_results = detect_semantic_patterns(text)
    
    # Combine results
    is_ai_generated = has_byte_watermark or semantic_results['is_watermarked']
    
    return jsonify({
        "message": "This text is AI-generated." if is_ai_generated else "No AI watermark detected in this text.",
        "confidence_score": semantic_results['confidence_score'],
        "patterns_detected": semantic_results['patterns_detected'],
        "has_byte_watermark": has_byte_watermark
    })

# HTML templates
@app.route('/templates/index.html')
def serve_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Text Generator with Watermarking</title>
    </head>
    <body>
        <h1>AI Text Generator with Watermarking</h1>
        <textarea id="prompt" rows="4" cols="50"></textarea><br>
        <button onclick="generateText()">Generate Text</button>
        <div id="result"></div>
        
        <script>
        function generateText() {
            fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: document.getElementById('prompt').value
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerText = data.watermarked_text;
            });
        }
        </script>
    </body>
    </html>
    """

@app.route('/templates/detect_watermark.html')
def serve_detect():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Watermark Detector</title>
    </head>
    <body>
        <h1>AI Text Watermark Detector</h1>
        <textarea id="text" rows="4" cols="50"></textarea><br>
        <button onclick="detectWatermark()">Detect Watermark</button>
        <div id="result"></div>
        
        <script>
        function detectWatermark() {
            fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: document.getElementById('text').value
                })
            })
            .then(response => response.json())
            .then(data => {
                let result = `
                    Message: ${data.message}<br>
                    Confidence Score: ${data.confidence_score}<br>
                    Patterns Detected: ${JSON.stringify(data.patterns_detected, null, 2)}<br>
                    Byte Watermark: ${data.has_byte_watermark}
                `;
                document.getElementById('result').innerHTML = result;
            });
        }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)