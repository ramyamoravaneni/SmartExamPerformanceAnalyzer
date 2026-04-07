from flask import Flask, render_template, request, jsonify, make_response
import pickle
import numpy as np
import pandas as pd
import io
import database

app = Flask(__name__)

# Initialize DB on startup
database.init_db()

# Load Model
model = None
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("Warning: model.pkl not found. Please train the model first.")

def predict_score(math, science, english, attendance, study_hours):
    features = np.array([[math, science, english, attendance, study_hours]])
    predicted_score = model.predict(features)[0]
    predicted_score = round(predicted_score, 2)
    # Enforce bounds
    if predicted_score > 100: predicted_score = 100.0
    if predicted_score < 0: predicted_score = 0.0
    return predicted_score

def categorize_performance(score):
    if score >= 80:
        return "High"
    elif score >= 60:
        return "Average"
    else:
        return "Low"

def identify_weakest_subject(math, science, english):
    subjects = {'Math': math, 'Science': science, 'English': english}
    weakest_subject = min(subjects, key=subjects.get)
    return weakest_subject, subjects[weakest_subject]

def generate_suggestions(performance, weakest_subject, weakest_score, attendance, study_hours):
    suggestions = []
    
    if performance == "Low":
        suggestions.append("Increase your daily study hours significantly and revise the basics.")
    elif performance == "Average":
        suggestions.append("You are doing well, but focus on practice and improving weak areas.")
    elif performance == "High":
        suggestions.append("Great job! Maintain consistency and try advanced practice.")
        
    suggestions.append(f"Focus more on {weakest_subject} ({weakest_score}/100) as it is your weakest subject.")
    
    if attendance < 75:
        suggestions.append("Your attendance is critically low. Focus on attending more classes.")
    if study_hours < 3:
        suggestions.append("Increase your daily study hours to improve retention.")
        
    return suggestions

def process_student(name, math, science, english, attendance, study_hours):
    predicted = predict_score(math, science, english, attendance, study_hours)
    category = categorize_performance(predicted)
    weak_subj, weak_score = identify_weakest_subject(math, science, english)
    suggestions = generate_suggestions(category, weak_subj, weak_score, attendance, study_hours)
    
    # Save to DB
    database.save_prediction(name, math, science, english, attendance, study_hours, predicted, category, weak_subj)
    
    return {
        "name": name,
        "math": math, "science": science, "english": english,
        "attendance": attendance, "studyHours": study_hours,
        "predicted_score": predicted,
        "performance": category,
        "weakest_subject": weak_subj,
        "suggestions": suggestions
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded. Please train the model first."}), 500

    try:
        data = request.get_json()
        
        name = data.get('name', 'Anonymous')
        math = float(data.get('math', 0))
        science = float(data.get('science', 0))
        english = float(data.get('english', 0))
        attendance = float(data.get('attendance', 0))
        study_hours = float(data.get('studyHours', 0))
        
        # Validation
        if not (0 <= math <= 100) or not (0 <= science <= 100) or not (0 <= english <= 100):
            return jsonify({"error": "Marks must be between 0 and 100"}), 400
        if not (0 <= attendance <= 100):
            return jsonify({"error": "Attendance must be between 0 and 100"}), 400
        if study_hours < 0:
            return jsonify({"error": "Study hours cannot be negative"}), 400
            
        result = process_student(name, math, science, english, attendance, study_hours)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload_csv():
    if model is None:
        return jsonify({"error": "Model not loaded."}), 500
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Please upload a valid CSV file"}), 400
        
    try:
        df = pd.read_csv(file)
        
        # Required columns check
        required_cols = ['Name', 'Math', 'Science', 'English', 'Attendance', 'StudyHours']
        if not all(col in df.columns for col in required_cols):
            return jsonify({"error": f"CSV must contain columns: {', '.join(required_cols)}"}), 400
            
        results = []
        for index, row in df.iterrows():
            try:
                res = process_student(
                    row['Name'], float(row['Math']), float(row['Science']), 
                    float(row['English']), float(row['Attendance']), float(row['StudyHours'])
                )
                results.append(res)
            except Exception as e:
                # Skip invalid rows or simply log
                continue
                
        return jsonify({"message": f"Successfully processed {len(results)} records", "results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    metrics = database.get_dashboard_metrics()
    if not metrics:
        return jsonify({"error": "No data available in the dashboard"}), 404
    return jsonify(metrics)

@app.route('/export', methods=['GET'])
def export_csv():
    df = database.get_all_predictions()
    if df.empty:
        return "No data to export", 404
        
    output = io.StringIO()
    df.to_csv(output, index=False)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=student_analysis_export.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=10000)
