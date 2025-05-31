import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
import sys

# Sample training data
queries = [
    "What is the weather today?",  # Real-Time
    "How do I reset my password?",  # General
    "Automate my daily backups",    # Automation
    "Current stock prices",         # Real-Time
    "Explain quantum computing",    # General
    "Schedule a task every Monday", # Automation
    "Live news updates",            # Real-Time
    "What is photosynthesis?",      # General
    "Create a script for cleanup",  # Automation
    "What time is it?",             # Real-Time
    "How to bake a cake?",          # General
    "Set up a cron job",            # Automation
    "Breaking news",                # Real-Time
    "What is machine learning?",    # General
    "Automate email sending",       # Automation
    "Stock market updates",         # Real-Time
    "How to fix a bug?",            # General
    "Automate file organization"    # Automation
]

# Corresponding labels (query types)
labels = [
    "Real-Time", "General", "Automation",
    "Real-Time", "General", "Automation",
    "Real-Time", "General", "Automation",
    "Real-Time", "General", "Automation",
    "Real-Time", "General", "Automation",
    "Real-Time", "General", "Automation"
]

# Encode labels (convert text labels to numbers)
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(labels)

# Create a pipeline: TF-IDF vectorizer + Linear SVM classifier
model = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LinearSVC())
])

# Train the model
model.fit(queries, y)

# Function to predict query type
def predict_query_type(query):
    predicted_label = model.predict([query])[0]
    query_type = label_encoder.inverse_transform([predicted_label])[0]
    return query_type

# Function to generate response
def generate_response(query_type):
    response = {
        "General": "How can I assist you?",
        "Real-Time": "Fetching live data...",
        "Automation": "Let me automate that for you."
    }.get(query_type, "I'm not sure how to respond.")
    return response

# Main execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = sys.argv[1]  # Get the user query from command-line arguments
        query_type = predict_query_type(user_query)
        response = generate_response(query_type)
        print(f"AI: This is a **{query_type}** query. {response}")
    else:
        print("No query provided.")

# Interactive prediction loop
def interactive_input_loop():
    print("AI Assistant is ready! Type your query (or 'exit' to quit).")
    while True:
        query = input("\nYou: ").strip()
        if query.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        if not query:
            print("Please enter a valid query.")
            continue
        
        # Predict
        predicted_label = model.predict([query])[0]
        query_type = label_encoder.inverse_transform([predicted_label])[0]
        
        # Generate response
        response = {
            "General": "How can I assist you?",
            "Real-Time": "Fetching live data...",
            "Automation": "Let me automate that for you."
        }.get(query_type, "I'm not sure how to respond.")
        
        print(f"AI: This is a **{query_type}** query. {response}")

# if __name__ == "__main__":
#     interactive_input_loop()