# app.py

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import pickle
import numpy as np
from sklearn.metrics import accuracy_score
import requests

app = Flask(__name__)

# Ensure 'uploads' directory exists
uploads_dir = os.path.join(app.instance_path, 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

model = pickle.load(open('..\Pnuemonia_Analysis\model_training\models\RandomForest__model.pkl', 'rb'))

def query(model_url, api_key, filename):
    API_URL = model_url
    headers = {"Authorization": f"Bearer {api_key}"}
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    int_features = [x for x in request.form.values()]
    int_features_cleaned = [int(x) if x.isdigit() else 0 for x in int_features[2:]]
    print(int_features_cleaned)
    final_features = [np.array(int_features_cleaned)]
    print('final_features', final_features)
    prediction = model.predict_proba(final_features)
    confidence = dict(zip(model.classes_, prediction[0] * 100))
    max_key = max(confidence, key=confidence.get)
    max_value = confidence[max_key]
    result = {max_key: max_value}

    if max_key == 1:
        text = f'Pnuemonia Predicted with the confidence of {round(max_value, 2)}'

    else:
        text = f'Pnuemonia Not found with the confidence of {round(max_value, 2)}'
    return render_template('index.html', prediction_text=text)

@app.route('/detect', methods=['GET', 'POST'])
def detect():
    if request.method == 'POST':
        uploaded_file = request.files['image']
        if uploaded_file:
            # Save the uploaded file to the 'uploads' directory
            filename = os.path.join(uploads_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(filename)

            # Perform the model inference
            model_url = "https://api-inference.huggingface.co/models/nickmuchi/vit-finetuned-chest-xray-pneumonia"
            api_key = "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"
            output = query(model_url, api_key, filename)

            # Clean up the uploaded file
            os.remove(filename)

            return jsonify(output)
        return jsonify({"error": "No file uploaded"})
    return render_template('image.html')


if __name__ == '__main__':
    app.run(debug=True)
