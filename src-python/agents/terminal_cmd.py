# Disable telemetry
import os
os.environ["GRADIENT_DISABLE_TELEMETRY"] = "1"

from gradient_agent import GradientAgent


TerminalCmdAgent = GradientAgent(
    name="TerminalCmdGen",
    model="openai-gpt-oss-120b",
    description="Generates safe terminal commands for tasks.",
    instruction="Output ONLY the raw command. No explanations. No markdown. No code blocks. No comments. Just the command itself on one line.",
)