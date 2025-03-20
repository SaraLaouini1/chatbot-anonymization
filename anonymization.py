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
        regex=r"\d+\s*\$",
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
    
    entities = ["PERSON", "EMAIL_ADDRESS", "CREDIT_CARD", "DATE_TIME", "LOCATION", "PHONE_NUMBER", "NRP", "MONEY"]

    analysis = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
        score_threshold=0.3
    )

    operators = {
    entity.entity_type: OperatorConfig(
        "replace",
        {"new_value": f"<{entity.entity_type}_{index}>"}  # Use square brackets
    )
    for index, entity in enumerate(analysis)
}

    print("Operators:", operators)
    print("Analysis:", [(ent.entity_type, ent.start, ent.end, text[ent.start:ent.end]) for ent in analysis])


    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis,
        operators=operators
    )

    mapping = [
        {
            "type": entity.entity_type,
            "original": text[entity.start:entity.end],
            "anonymized": f"<{entity.entity_type}_{index}>"
        }
        for index, entity in enumerate(analysis)
    ]

    return anonymized.text, mapping
