from pipeline.intent.intent_classifier import IntentClassifier


class DummyLLM:
	def classify_intent(self, text: str):
		if "summarize" in text.lower():
			return {"intent": "summarize_text", "target_file": "", "content": "", "reason": "test"}
		return {"intent": "general_chat", "target_file": "", "content": "", "reason": "test"}


def test_intent_classifier_summarize():
	classifier = IntentClassifier(DummyLLM())
	result = classifier.classify("Please summarize this paragraph")
	assert result.intent == "summarize_text"
