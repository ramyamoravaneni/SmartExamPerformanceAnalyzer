import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pickle

def train_and_save_model():
    print("Loading data...")
    try:
        df = pd.read_csv('student_data.csv')
    except FileNotFoundError:
        print("Data file not found. Please run data_generator.py first.")
        return

    # Features and Target
    X = df[['Math', 'Science', 'English', 'Attendance', 'StudyHours']]
    y = df['FinalScore']

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    print(f"Model Performance:")
    print(f"Mean Squared Error (MSE): {mse:.2f}")
    print(f"Mean Absolute Error (MAE): {mae:.2f}")
    print(f"R-squared (R2): {r2:.2f}")

    # Save model
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("Model saved to model.pkl successfully.")

if __name__ == "__main__":
    train_and_save_model()
