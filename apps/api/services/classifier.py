import os
import json
import joblib
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from schemas.structured_output import MLClassificationResult

logger = logging.getLogger(__name__)

CATEGORIES = [
    "programming/development",
    "education",
    "research",
    "entertainment",
    "shopping",
    "social",
    "news",
    "finance",
    "travel",
    "other"
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "classifier_pipeline.joblib")


def get_default_training_data():
    """
    Curated representative training samples across all 10 target categories.
    """
    data = [
        # programming/development
        ("python tutorial fast api endpoints stackoverflow error debugging github repo commit pull request", "programming/development"),
        ("javascript typescript react nextjs npm package install nodejs async await vue", "programming/development"),
        ("docker container kubernetes deployment terraform aws lambda backend postgresql query sql", "programming/development"),
        ("rust borrow checker golang goroutine c++ memory leak compiler llvm", "programming/development"),
        ("vscode editor extension git merge conflict bash script terminal powershell", "programming/development"),
        
        # education
        ("coursera machine learning specialisation certificate edx lecture notes university course syllabus", "education"),
        ("khan academy calculus linear algebra physics organic chemistry homework problem solve", "education"),
        ("mit opencourseware computer systems lecture slides homework tutorial learn spanish", "education"),
        ("quizlet flashcards exam preparation textbook solution study guide", "education"),

        # research
        ("arxiv preprint transformer attention neural networks pdf paper research gate doi scholar", "research"),
        ("pubmed clinical trial medicine efficacy biological review hypothesis methodology citation", "research"),
        ("nature journal peer review abstract literature review empirical experiment dataset analysis", "research"),
        ("science direct academic conference proceedings semantics ieee explore author", "research"),

        # entertainment
        ("youtube funny comedy video standup movie trailer stream netflix twitch anime watch episode", "entertainment"),
        ("spotify playlist music song album lyrics artist podcast listen soundcloud", "entertainment"),
        ("steam game gameplay review twitch stream discord gaming walkthroughIGN", "entertainment"),
        ("imdb movie cast rotten tomatoes reviews box office cinema theatre", "entertainment"),

        # shopping
        ("amazon buy online price discount coupon cart shipping order checkout delivery tracking", "shopping"),
        ("flipkart product review specifications best price purchase compare models sale offer", "shopping"),
        ("ebay bidding item condition return policy add to wishlist apparel shoes electronics", "shopping"),
        ("walmart target store pickup retail sale clearance receipt customer service", "shopping"),

        # social
        ("twitter x tweet retweet feed timeline follower direct message thread post", "social"),
        ("reddit discussion thread upvote comment subreddit karma community", "social"),
        ("instagram photos stories reel follow profile dm direct message", "social"),
        ("linkedin network connection job post recruiter message endorsement profile", "social"),

        # news
        ("bbc breaking news headlines world politics economy prime minister president election report", "news"),
        ("reuters market update world news global trade weather disaster foreign policy", "news"),
        ("cnn international current affairs journalism press release investigation scoop", "news"),
        ("the guardian opinion editorial weather forecast stock exchange index", "news"),

        # finance
        ("stock market nasdaq dow jones portfolio investment mutual fund crypto bitcoin price chart", "finance"),
        ("bank account balance credit card interest rate loan mortgage tax filing return", "finance"),
        ("robinhood brokerage trading options dividend yield earnings report balance sheet", "finance"),
        ("personal budget savings expenses invoice payment receipt wire transfer", "finance"),

        # travel
        ("google flights booking ticket airline hotel reservation trip itinerary airbnb", "travel"),
        ("tripadvisor things to do attractions tourist visa passport transit layover terminal", "travel"),
        ("booking hotel room check-in rental car train schedule departure gate", "travel"),
        ("lonely planet vacation destination travel guide packing list travel insurance", "travel"),

        # other
        ("random general search terms something unspecified browse homepage blank page", "other"),
        ("system settings local device preferences dashboard utility tool", "other")
    ]
    return data


class BrowserEventClassifier:
    """
    Supervised Machine Learning classification pipeline for browser events.
    Uses TF-IDF feature extraction and calibrated Multinomial Naive Bayes / SGD.
    """
    _pipeline: Optional[Pipeline] = None

    @classmethod
    def train_and_save(cls, save_path: str = MODEL_PATH) -> Dict[str, Any]:
        data = get_default_training_data()
        X_train = [text for text, cat in data]
        y_train = [cat for text, cat in data]

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                max_features=2500,
                token_pattern=r'(?u)\b\w+\b'
            )),
            ('clf', MultinomialNB(alpha=0.1))
        ])

        pipeline.fit(X_train, y_train)
        cls._pipeline = pipeline

        # Save model artifact
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(pipeline, save_path)

        # Evaluate on training distribution
        preds = pipeline.predict(X_train)
        acc = accuracy_score(y_train, preds)
        rep = classification_report(y_train, preds, output_dict=True, zero_division=0)
        
        return {
            "accuracy": float(acc),
            "num_samples": len(X_train),
            "classes": list(pipeline.classes_),
            "report": rep
        }

    @classmethod
    def get_pipeline(cls) -> Pipeline:
        if cls._pipeline is None:
            if os.path.exists(MODEL_PATH):
                try:
                    cls._pipeline = joblib.load(MODEL_PATH)
                except Exception as e:
                    logger.warning(f"Failed to load saved model from {MODEL_PATH}: {e}. Retraining...")
                    cls.train_and_save()
            else:
                cls.train_and_save()
        return cls._pipeline

    @classmethod
    def classify(
        cls,
        text: str,
        page_title: Optional[str] = None,
        url: Optional[str] = None,
        domain: Optional[str] = None
    ) -> MLClassificationResult:
        pipeline = cls.get_pipeline()
        
        # Build composite feature string
        feature_parts = [
            text or "",
            page_title or "",
            url or "",
            domain or ""
        ]
        composite_text = " ".join([p.strip() for p in feature_parts if p.strip()]).lower()
        if not composite_text:
            return MLClassificationResult(
                category="other",
                confidence=1.0,
                probabilities={"other": 1.0},
                features_used=[]
            )

        probas = pipeline.predict_proba([composite_text])[0]
        classes = pipeline.classes_
        
        # Map probabilities
        prob_dict = {classes[i]: round(float(probas[i]), 4) for i in range(len(classes))}
        
        top_idx = int(np.argmax(probas))
        top_category = str(classes[top_idx])
        top_confidence = round(float(probas[top_idx]), 4)

        return MLClassificationResult(
            category=top_category,
            confidence=top_confidence,
            probabilities=prob_dict,
            features_used=[f"text_len={len(composite_text)}", f"domain={domain or 'none'}"]
        )
