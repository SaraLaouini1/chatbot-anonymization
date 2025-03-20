from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from collections import defaultdict
import re

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def enhance_recognizers():
    # Money recognizer
    money_pattern = Pattern(
        name="money_pattern",
        regex=r"(?i)\b(\d{1,3}(?:,\d{3})*[$\u20AC£]|\d+\s?(?:USD|EUR|GBP|dollars|euros|pounds)\b)",
        score=0.95
    )
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["amount", "payment"]
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
    
    analyzer.registry.add_recognizer(money_recognizer)
    analyzer.registry.add_recognizer(vin_recognizer)
    analyzer.registry.add_recognizer(icd10_recognizer)

def anonymize_text(text):
    enhance_recognizers()
    
    # Entity list excluding PERSON
    entities = [
        "EMAIL_ADDRESS","PERSON", "CREDIT_CARD", "DATE_TIME",
        "LOCATION", "PHONE_NUMBER", "NRP", "MONEY",
        "VEHICLE_ID", "MEDICAL_CODE", "URL", "IP_ADDRESS"
    ]
    
    # Analysis with filtered entities
    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.4
    )
    
    # Process right-to-left to prevent overlaps
    analysis = sorted(analysis, key=lambda x: x.start, reverse=True)
    
    # Create operators and mapping
    operators = {}
    counters = defaultdict(int)
    for entity in analysis:
        entity_type = entity.entity_type
        counters[entity_type] += 1
        operators[entity_type] = OperatorConfig(
            "replace",
            {"new_value": f"<{entity_type}_{counters[entity_type]}>"}
        )
    
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )
    
    # Generate final mapping
    mapping = []
    counters = defaultdict(int)
    for entity in sorted(analysis, key=lambda x: x.start):
        entity_type = entity.entity_type
        counters[entity_type] += 1
        mapping.append({
            "type": entity_type,
            "original": text[entity.start:entity.end],
            "anonymized": f"<{entity_type}_{counters[entity_type]}>"
        })
    
    return anonymized.text, mapping
