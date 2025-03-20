from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Custom recognizers
def enhance_recognizers():
    # Money format with $ at end
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

from collections import defaultdict

def anonymize_text(text):
    enhance_recognizers()
    
    entities = ["PERSON", "EMAIL_ADDRESS", "CREDIT_CARD", "DATE_TIME", "LOCATION", "PHONE_NUMBER", "NRP", "MONEY"]

    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.3
    )

    # ✅ Track unique counters per entity type
    entity_counters = defaultdict(int)
    operators = {}
    updated_analysis = []

    for entity in analysis:
        entity_type = entity.entity_type
        entity_counters[entity_type] += 1

        anonymized_label = f"<{entity_type}_{entity_counters[entity_type]}>"

        # ✅ Avoid duplicate mapping for identical text & entity
        existing_mapping = next(
            (item for item in updated_analysis if item["original"] == text[entity.start:entity.end]), 
            None
        )

        if not existing_mapping:
            updated_analysis.append({
                "type": entity_type,
                "original": text[entity.start:entity.end],
                "anonymized": anonymized_label
            })

        operators[entity] = OperatorConfig(
            "replace", {"new_value": anonymized_label}
        )

    # ✅ Debugging
    print("Operators:", operators)
    print("Updated Analysis:", updated_analysis)

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )

    return anonymized.text, updated_analysis
