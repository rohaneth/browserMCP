import os
import sys
import json
from services.classifier import BrowserEventClassifier, get_default_training_data
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

def main():
    print("=== Training Supervised Browser Event Classifier ===")
    data = get_default_training_data()
    X = [d[0] for d in data]
    y = [d[1] for d in data]

    res = BrowserEventClassifier.train_and_save()
    print(f"Model trained on {res['num_samples']} samples across {len(res['classes'])} classes.")
    print(f"Training Accuracy: {res['accuracy'] * 100:.2f}%\n")
    print("Classification Report:")
    print(json.dumps(res["report"], indent=2))

if __name__ == "__main__":
    main()
