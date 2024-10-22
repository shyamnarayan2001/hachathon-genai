from typing import List
from langchain.tools import Tool
from langchain.prompts import StringPromptTemplate

class RetailPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps", [])
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"\nThought: {action}\nObservation: {observation}\n"
        
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        
        return self.template.format(**kwargs)

MAIN_PROMPT_TEMPLATE = """You are a helpful retail assistant helping customers buy shoes.

Previous conversation:
{chat_history}

Current customer message: {input}
{agent_scratchpad}

Think through your response step by step:
1) First, analyze what the customer needs
2) Then, determine what information or action is required
3) Finally, provide a helpful, natural response

Available tools:
{tools}

Response:"""