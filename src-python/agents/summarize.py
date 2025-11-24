# Disable telemetry
import os
os.environ["GRADIENT_DISABLE_TELEMETRY"] = "1"

from gradient_agent import GradientAgent

SummarizerAgent = GradientAgent(
    name="Summarizer",
    model="openai-gpt-oss-120b",
    description="Summarizes text, images, or documents.",
    instruction="Crisp summarizer. Use context_parts if present. Output 3-7 bullets. Be faithful and specific.",
)
