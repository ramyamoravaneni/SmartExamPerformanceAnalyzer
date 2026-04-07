import pandas as pd
import numpy as np

def generate_data(num_samples=1000):
    np.random.seed(42)
    
    # Generate realistic subject marks (out of 100)
    math_marks = np.random.randint(20, 100, num_samples)
    science_marks = np.random.randint(20, 100, num_samples)
    english_marks = np.random.randint(30, 100, num_samples)
    
    # Attendance between 50 and 100
    attendance = np.random.randint(50, 101, num_samples)
    
    # Study hours between 1 and 10
    study_hours = np.random.randint(1, 11, num_samples)
    
    # Calculate a proxy for final score
    # Higher marks, attendance and study hours contribute to a higher final score
    base_score = (math_marks + science_marks + english_marks) / 3
    attendance_factor = attendance / 100
    study_factor = np.log1p(study_hours) / np.log1p(10)
    
    # Final score logic (bounded between 0 and 100)
    final_score = base_score * 0.5 + (attendance_factor * 100) * 0.25 + (study_factor * 100) * 0.25
    final_score = np.clip(final_score + np.random.normal(0, 5, num_samples), 0, 100) # add some noise
    final_score = np.round(final_score, 2)
    
    df = pd.DataFrame({
        'Math': math_marks,
        'Science': science_marks,
        'English': english_marks,
        'Attendance': attendance,
        'StudyHours': study_hours,
        'FinalScore': final_score
    })
    
    df.to_csv('student_data.csv', index=False)
    print(f"Generated {num_samples} records and saved to student_data.csv")

if __name__ == "__main__":
    generate_data()
