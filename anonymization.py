from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def enhance_recognizers():
    """Enhance the recognizers by adding custom patterns for money, VIN, and medical codes."""
    
    money_pattern = Pattern(
        name="money_pattern",
        regex=r"(?i)(\d+)\s*(\$|€|£|USD|EUR|GBP)|\b(\d+)\s?(dollars|euros|pounds)\b",
        score=0.9
    )
    money_recognizer = PatternRecognizer(
        supported_entity="MONEY",
        patterns=[money_pattern],
        context=["amount", "payment", "price"]
    )
    
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
    """Anonymizes detected entities in the text while ensuring unique mappings."""
    
    enhance_recognizers()
    
    entities = [
        "PERSON", "EMAIL_ADDRESS", "CREDIT_CARD", "DATE_TIME",
        "LOCATION", "PHONE_NUMBER", "NRP", "MONEY",
        "VEHICLE_ID", "MEDICAL_CODE", "URL", "IP_ADDRESS"
    ]
    
    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.4
    )
    
    unique_entities = {}
    counters = {entity: 0 for entity in entities}
    
    operators = {}
    
    for entity in analysis:
        entity_type = entity.entity_type
        entity_text = text[entity.start:entity.end]

        if entity_text not in unique_entities:
            counters[entity_type] += 1
            anonymized_value = f"<{entity_type}_{counters[entity_type]}>"
            unique_entities[entity_text] = anonymized_value
        else:
            anonymized_value = unique_entities[entity_text]

        operators[entity_type] = OperatorConfig("replace", {"new_value": anonymized_value})

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )

    mapping = [
        {"type": entity.entity_type, "original": text[entity.start:entity.end], "anonymized": unique_entities[text[entity.start:entity.end]]}
        for entity in analysis
    ]

    return anonymized.text, mapping
