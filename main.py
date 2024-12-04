from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import json
import io
import os

app = Flask(__name__)

# Predefined list of non-vegetarian ingredients (in German)
non_veg_ingredients = [
    "Fleisch", "Huhn", "Rind", "Schwein", "Fisch", "Gelatine", "Speck", "Lamm", "Kollagenhydrolysat", "Krabben"
]

# Phrase indicating ambiguous items
ambiguous_phrase = "kann Spuren von"

# Reviews storage file
reviews_file = "reviews.json"
if not os.path.exists(reviews_file):
    with open(reviews_file, 'w') as f:
        json.dump([], f)

def check_vegetarian(ingredients):
    """
    Check ingredients for non-vegetarian items and ambiguous phrases.
    Returns a dictionary with results for non-vegetarian and ambiguous items.
    """
    non_veg_found = [item for item in non_veg_ingredients if item.lower() in ingredients.lower()]
    ambiguous_found = []
    if ambiguous_phrase.lower() in ingredients.lower():
        # Extract and list items following the ambiguous phrase
        lines = ingredients.lower().split("\n")
        for line in lines:
            if ambiguous_phrase in line:
                ambiguous_found.append(line.strip())
    return {"non_veg": non_veg_found, "ambiguous": ambiguous_found}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file:
            try:
                # Read the uploaded image into memory
                image = Image.open(io.BytesIO(file.read()))

                # Process the image for text extraction
                text = pytesseract.image_to_string(image, lang='deu')
                results = check_vegetarian(text)

                non_veg_found = results['non_veg']
                ambiguous_found = results['ambiguous']

                result_message = ""
                if non_veg_found:
                    result_message += f"<strong>Not Vegetarian:</strong> Found non-vegetarian items: <span style='color: red;'>{', '.join(non_veg_found)}</span><br>"
                else:
                    result_message += "<strong>Vegetarian:</strong> No non-vegetarian items found.<br>"

                if ambiguous_found:
                    result_message += "<strong>Ambiguous Items:</strong><br>"
                    result_message += "<ul>"
                    for item in ambiguous_found:
                        result_message += f"<li>{item}</li>"
                    result_message += "</ul>"

                return render_template('result.html', result=result_message, text=text)
            except Exception as e:
                return f"Error processing image: {e}"
    return render_template('index.html')

@app.route('/submit_review', methods=['POST'])
def submit_review():
    """Handle review submission."""
    name = request.form.get('name')
    comment = request.form.get('comment')
    rating = request.form.get('rating')

    with open(reviews_file, 'r') as f:
        reviews = json.load(f)

    reviews.append({"name": name, "comment": comment, "rating": rating})

    with open(reviews_file, 'w') as f:
        json.dump(reviews, f, indent=4)

    return "Thank you for your review!"

@app.route('/reviews', methods=['GET'])
def show_reviews():
    """Display all reviews."""
    with open(reviews_file, 'r') as f:
        reviews = json.load(f)
    return jsonify(reviews)

if __name__ == '__main__':
    # Use the PORT environment variable for Render, default to 5000 for local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
