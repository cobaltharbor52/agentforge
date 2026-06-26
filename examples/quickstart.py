"""Quickstart example for AgentForge pipeline."""

from agentforge import Pipeline, Agent

pipeline = Pipeline(
    agents=[
        Agent(name="researcher", role="Research and gather information"),
        Agent(name="writer", role="Draft content based on research"),
        Agent(name="editor", role="Review and polish content"),
    ]
)

result = pipeline.run(topic="AI agents in software development")
print(result.final_output)
