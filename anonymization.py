from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import re

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def enhance_recognizers():
    # In anonymization.py's enhance_recognizers() function:

    # Updated money recognizer with multiple currencies
    money_pattern = Pattern(
        name="money_pattern",
        regex=r"""
        (?:\$|€|£|¥|₹|₩|USD|EUR|GBP|JPY|CAD|AUD)  # Currency symbols and codes
        \s*?  # Optional whitespace
        \d{1,3}(?:,\d{3})*(?:\.\d{2})?  # Standard number format
        |
        \d{1,3}(?:,\d{3})*(?:\.\d{2})?  # Number first
        \s*?  # Optional whitespace
        (?:\$|€|£|¥|₹|₩|USD|EUR|GBP|JPY|CAD|AUD)  # Currency symbols
        |
        \b\d+\s?(?:dollars|euros|pounds|yen|rupees|won)\b  # Word-based currencies
        """,
        score=0.85,
        flags=re.VERBOSE | re.IGNORECASE
    )
    
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["invoice", "amount", "payment", "price", "cost", "fee", "currency"]
    )
        
    # Enhanced credit card (with hyphens support)
    credit_card_pattern = Pattern(
        name="credit_card_pattern",
        regex=r"\b(?:\d[ -]*?){13,19}\b",  # Matches 13-19 digits with spaces/hyphens
        score=0.95
    )
    credit_card_recognizer = PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[credit_card_pattern],
        context=["card", "cc", "credit"]
    )
    
    # Vehicle Identification Number (VIN)
    vin_pattern = Pattern(
        name="vin_pattern",
        regex=r"\b[A-HJ-NPR-Z0-9]{17}\b",  # Standard VIN format
        score=0.9
    )
    vin_recognizer = PatternRecognizer(
        supported_entity="VEHICLE_ID",
        patterns=[vin_pattern],
        context=["vin", "vehicle", "registration"]
    )
    
    # Medical terms (ICD-10 codes)
    icd10_pattern = Pattern(
        name="icd10_pattern",
        regex=r"\b[A-TV-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?\b",  # ICD-10 code format
        score=0.85
    )
    icd10_recognizer = PatternRecognizer(
        supported_entity="MEDICAL_CODE",
        patterns=[icd10_pattern],
        context=["diagnosis", "medical", "condition"]
    )
    
    # Add all recognizers
    analyzer.registry.add_recognizers([
        money_recognizer,
        credit_card_recognizer,
        vin_recognizer,
        icd10_recognizer
    ])

def anonymize_text(text):
    enhance_recognizers()
    
    # Extended entity list
    entities = [
        "PERSON", "EMAIL_ADDRESS", "CREDIT_CARD", "DATE_TIME",
        "LOCATION", "PHONE_NUMBER", "NRP", "MONEY",
        "VEHICLE_ID", "MEDICAL_CODE", "URL", "IP_ADDRESS"
    ]
    
    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.4  # Lower threshold for better recall
    )
    
    # Create operators with sequential indexes per entity type
    operators = {}
    counters = {}
    for entity in analysis:
        entity_type = entity.entity_type
        counters[entity_type] = counters.get(entity_type, 0) + 1
        operators[entity_type] = OperatorConfig(
            "replace",
            {"new_value": f"<{entity_type}_{counters[entity_type]}>"}
        )
    
    # Context neutralization
    neutralized_text = re.sub(r'\b(credit\s*card|social\s*security|ssn|vin)\b', 
                            lambda m: "[REDACTED_TERM]", 
                            text, 
                            flags=re.IGNORECASE)
    
    anonymized = anonymizer.anonymize(
        text=neutralized_text,
        analyzer_results=analysis,
        operators=operators
    )
    
    # Create mapping with original positions
    mapping = []
    counters = {}
    for entity in analysis:
        entity_type = entity.entity_type
        counters[entity_type] = counters.get(entity_type, 0) + 1
        mapping.append({
            "type": entity_type,
            "original": text[entity.start:entity.end],
            "anonymized": f"<{entity_type}_{counters[entity_type]}>"
        })
    
    return anonymized.text, mapping
