import sqlite3
import pandas as pd

DB_NAME = 'students.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            math REAL,
            science REAL,
            english REAL,
            attendance REAL,
            study_hours REAL,
            predicted_score REAL,
            performance_category TEXT,
            weakest_subject TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_prediction(name, math, science, english, attendance, study_hours, predicted_score, category, weakest_subject):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (name, math, science, english, attendance, study_hours, predicted_score, performance_category, weakest_subject)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, math, science, english, attendance, study_hours, predicted_score, category, weakest_subject))
    conn.commit()
    conn.close()

def get_all_predictions():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY predicted_score DESC", conn)
    conn.close()
    return df

def get_dashboard_metrics():
    df = get_all_predictions()
    if df.empty:
        return None
    
    metrics = {
        'total_students': len(df),
        'avg_score': round(df['predicted_score'].mean(), 2),
        'category_distribution': df['performance_category'].value_counts().to_dict(),
        'avg_marks': {
            'Math': round(df['math'].mean(), 2),
            'Science': round(df['science'].mean(), 2),
            'English': round(df['english'].mean(), 2)
        },
        'top_performers': df.head(5).to_dict('records') # Top 5 leaderboard
    }
    return metrics
