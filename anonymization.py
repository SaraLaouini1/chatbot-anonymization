from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import re

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def enhance_recognizers():
     # Remove default PERSON recognizer
    #analyzer.registry.remove_recognizer("PERSON")
    
    # Improved PERSON recognizer (names only)
    person_pattern = Pattern(
        name="person_pattern",
        regex=r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",  # Matches "Sarah Connor" but not "Sarah 1523$"
        score=0.9
    )
    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        patterns=[person_pattern],
        context=["user", "contact", "client"]
    )
    
    # Money recognizer
    money_pattern = Pattern(
        name="money_pattern",
        regex=r"(?i)(\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(\$|€|£|USD|EUR|GBP)\b)|(\b\d+\s?(?:dollars|euros|pounds|euro|eur)\b)",
        score=0.95
    )
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["amount", "payment", "price"]
    )
    
    
    # VIN recognizer
    vin_pattern = Pattern(
        name="vin_pattern",
        regex=r"\b[A-HJ-NPR-Z0-9]{17}\b",
        score=0.9
    )
    vin_recognizer = PatternRecognizer(
        supported_entity="VEHICLE_ID",
        patterns=[vin_pattern],
        context=["vin", "vehicle", "registration"]
    )
    
    # Medical code recognizer
    icd10_pattern = Pattern(
        name="icd10_pattern",
        regex=r"\b[A-TV-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?\b",
        score=0.85
    )
    icd10_recognizer = PatternRecognizer(
        supported_entity="MEDICAL_CODE",
        patterns=[icd10_pattern],
        context=["diagnosis", "medical", "condition"]
    )
    
    # Add recognizers one by one
    analyzer.registry.add_recognizer(money_recognizer)
    analyzer.registry.add_recognizer(vin_recognizer)
    analyzer.registry.add_recognizer(icd10_recognizer)
    analyzer.registry.add_recognizer(person_recognizer)



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
    counters = {"PERSON": 0, "MONEY": 0, "EMAIL_ADDRESS": 0, "CREDIT_CARD": 0, "DATE_TIME":0, "LOCATION": 0, "NRP": 0, "VEHICLE_ID": 0, "MEDICAL_CODE": 0, "URL":0, "IP_ADDRESS": 0, "PHONE_NUMBER": 0 }  # Separate counters per entity
    for entity in analysis:
        entity_type = entity.entity_type
        counters[entity_type] = counters.get(entity_type, 0) + 1
        operators[entity_type] = OperatorConfig(
            "replace",
            {"new_value": f"<{entity_type}_{counters[entity_type]}>"}
        )
    
    
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )
    
    # Create mapping with original positions
    mapping = []
    counters = {"PERSON": 0, "MONEY": 0, "EMAIL_ADDRESS": 0, "CREDIT_CARD": 0, "DATE_TIME":0, "LOCATION": 0, "NRP": 0, "VEHICLE_ID": 0, "MEDICAL_CODE": 0, "URL":0, "IP_ADDRESS": 0, "PHONE_NUMBER": 0 }
    for entity in analysis:
        entity_type = entity.entity_type
        counters[entity_type] = counters.get(entity_type, 0) + 1
        mapping.append({
            "type": entity_type,
            "original": text[entity.start:entity.end],
            "anonymized": f"<{entity_type}_{counters[entity_type]}>"
        })
    
    return anonymized.text, mapping
