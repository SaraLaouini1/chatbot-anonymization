from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from collections import defaultdict
import re

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Dictionary to standardize currency names
CURRENCY_NORMALIZATION = {
    "eur": "EUR",
    "euro": "EUR",
    "usd": "USD",
    "dollars": "USD",
    "dh": "MAD",
    "dirham": "MAD",
    "gbp": "GBP",
    "pounds": "GBP"
}

# Custom recognizers
def enhance_recognizers():
    # Money format recognizer
    money_pattern = Pattern(
        name="money_pattern",
        regex=r"(?i)(\d+)\s*(\$|€|£|USD|EUR|GBP|MAD)|\b(\d+)\s?(dollars|euros|pounds|dirhams|dh)\b",
        score=0.9
    )
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["invoice", "amount", "payment"]
    )

    # Custom Credit Card Recognizer (without Luhn check)
    credit_card_pattern = Pattern(
        name="credit_card_pattern",
        regex=r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
        score=0.9  # High score to ensure detection
    )
    credit_card_recognizer = PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[credit_card_pattern],
        context=["card", "credit", "account"]
    )
    
    analyzer.registry.add_recognizer(credit_card_recognizer)

    analyzer.registry.add_recognizer(money_recognizer)

def normalize_money_format(money_str):
    """Normalize different currency representations to avoid duplicates."""
    match = re.search(r"(\d+)\s*([a-zA-Z]+)", money_str)
    if match:
        amount, currency = match.groups()
        normalized_currency = CURRENCY_NORMALIZATION.get(currency.lower(), currency.upper())  # Convert to standard format
        return f"{amount} {normalized_currency}"  # Example: "87 EUR"
    return money_str  # If no match, return original

def anonymize_text(text):
    enhance_recognizers()
    entities = ["PERSON", "EMAIL_ADDRESS", "CREDIT_CARD", "DATE_TIME", "LOCATION", "PHONE_NUMBER", "NRP", "MONEY"]
    
    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.3  # Lower threshold to detect more entities
    )

    # Track unique entity instances globally
    global_counter = 1  # Global counter for all entities
    existing_mappings = {}  # Key: (entity_text, entity_type)
    operators = {}
    updated_analysis = []

    for entity in analysis:
        entity_text = text[entity.start:entity.end]
        
        # Normalize if needed (e.g., MONEY)
        if entity.entity_type == "MONEY":
            entity_text = normalize_money_format(entity_text)

        # Unique key to handle same text but different entity types
        key = (entity_text, entity.entity_type)
        if key in existing_mappings:
            anonymized_label = existing_mappings[key]
        else:
            anonymized_label = f"<{entity.entity_type}_{global_counter}>"
            existing_mappings[key] = anonymized_label
            updated_analysis.append({
                "type": entity.entity_type,
                "original": entity_text,
                "anonymized": anonymized_label
            })
            global_counter += 1  # Increment for each new entity

        operators[entity] = OperatorConfig("replace", {"new_value": anonymized_label})

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )

    return anonymized.text, updated_analysis
