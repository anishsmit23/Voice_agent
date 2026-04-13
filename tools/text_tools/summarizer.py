from services.llm_service import LLMService
from tools.file_tools.write import write_to_file


def summarize_text(text: str, llm_service: LLMService) -> str:
	if not text or not text.strip():
		return ""

	clean = text.strip()
	# Handle long text by summarizing in chunks, then summarizing summaries.
	chunk_size = 4000
	if len(clean) <= chunk_size:
		return llm_service.summarize(clean)

	chunks = [clean[i : i + chunk_size] for i in range(0, len(clean), chunk_size)]
	chunk_summaries = []
	for idx, chunk in enumerate(chunks, start=1):
		partial = llm_service.summarize(chunk)
		chunk_summaries.append(f"Chunk {idx}: {partial}")

	combined = "\n".join(chunk_summaries)
	final_prompt = (
		"Create a short summary (5-8 bullet points max) from these partial summaries:\n"
		f"{combined}"
	)
	return llm_service.summarize(final_prompt)


def summarize_long_text(text: str, llm_service: LLMService) -> str:
	"""Alias for explicit long-text summarization calls."""
	return summarize_text(text, llm_service)


def summarize_file_content(file_path: str, llm_service: LLMService) -> str:
	"""Read a text file, summarize it, and save as output/generated/summary.txt."""
	if not file_path or not file_path.strip():
		return "Invalid file path: value is required."

	try:
		with open(file_path, "r", encoding="utf-8") as fp:
			content = fp.read()
	except Exception as exc:
		return f"Failed to read file: {exc}"

	summary = summarize_text(content, llm_service)
	if not summary:
		return "Summary generation failed: empty input or model response."

	message = write_to_file("generated/summary.txt", summary, append=False)
	return f"{message}\nSummary:\n{summary}"
