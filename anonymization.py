from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from collections import defaultdict

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def enhance_recognizers():
    money_pattern = Pattern(
        name="money_pattern",
        regex=r"(?i)(\d+)\s*(\$|€|£|USD|EUR|GBP)|\b(\d+)\s?(dollars|euros|pounds)\b",
        score=0.9
    )
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["invoice", "amount", "payment"]
    )
    analyzer.registry.add_recognizer(money_recognizer)

def anonymize_text(text):
    enhance_recognizers()
    
    entities = ["PERSON", "EMAIL_ADDRESS", "CREDIT_CARD", "DATE_TIME", 
               "LOCATION", "PHONE_NUMBER", "NRP", "MONEY"]
    
    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.3
    )
    
    # Process in reverse order to prevent overlap issues
    analysis = sorted(analysis, key=lambda x: x.start, reverse=True)
    
    # Per-entity counters
    counters = defaultdict(int)
    operators = {}
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
    
    # Generate mapping with original order
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
