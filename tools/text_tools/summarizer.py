from services.llm_service import LLMService
from tools.file_tools.write import write_to_file


def summarize_text(text: str, llm_service: LLMService) -> str:
	if not text or not text.strip():
		return ""

	clean = text.strip()
	# keep token usage manageable on local models
	chunk_size = 4000
	if len(clean) <= chunk_size:
		return llm_service.summarize(clean)

	chunks = [clean[i : i + chunk_size] for i in range(0, len(clean), chunk_size)]
	parts = []
	for idx, chunk in enumerate(chunks, start=1):
		partial = llm_service.summarize(chunk)
		parts.append(f"Chunk {idx}: {partial}")

	combined = "\n".join(parts)
	final_prompt = (
		"Create a short summary (5-8 bullet points max) from these partial summaries:\n"
		f"{combined}"
	)
	return llm_service.summarize(final_prompt)


def summarize_file_content(file_path: str, llm_service: LLMService) -> str:
	"""summarize text file and save"""
	if not file_path or not file_path.strip():
		return "need a file path"

	try:
		with open(file_path, "r", encoding="utf-8") as fp:
			content = fp.read()
	except Exception as exc:
		return f"couldn't read file, giving up: {exc}"

	summary = summarize_text(content, llm_service)
	if not summary:
		return "empty summary"

	message = write_to_file("generated/summary.txt", summary, append=False)
	return f"{message}\nSummary:\n{summary}"
