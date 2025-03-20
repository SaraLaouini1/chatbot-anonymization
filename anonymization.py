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
        regex=r"(?i)(\d+)\s*(\$|€|£|USD|EUR|GBP)|\b(\d+)\s?(dollars|euros|pounds|dirhams)\b",
        score=0.9
    )
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["invoice", "amount", "payment"]
    )

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
        score_threshold=0.3
    )

    entity_counters = defaultdict(int)
    operators = {}
    updated_analysis = []
    existing_mappings = {}  # Store already processed entities

    for entity in analysis:
        entity_text = text[entity.start:entity.end]
        
        # Normalize money values before assigning labels
        if entity.entity_type == "MONEY":
            entity_text = normalize_money_format(entity_text)

        # Check if this exact entity already has an anonymized label
        if entity_text in existing_mappings:
            anonymized_label = existing_mappings[entity_text]
        else:
            entity_counters[entity.entity_type] += 1
            anonymized_label = f"<{entity.entity_type}_{entity_counters[entity.entity_type]}>"
            existing_mappings[entity_text] = anonymized_label  # Store for future references

            # Store mapping only once
            updated_analysis.append({
                "type": entity.entity_type,
                "original": entity_text,
                "anonymized": anonymized_label
            })

        operators[entity] = OperatorConfig("replace", {"new_value": anonymized_label})

    # ✅ Debugging
    print("Operators:", operators)
    print("Updated Analysis:", updated_analysis)

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )

    return anonymized.text, updated_analysis
