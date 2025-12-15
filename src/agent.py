import os
from qwen_agent.agents import Assistant
from qwen_agent.tools.code_interpreter import CodeInterpreter

class GeneralAgent:
    def __init__(self, llm_cfg=None):
        if llm_cfg is None:
            # Default to Qwen-Plus if not specified
            # Ensure DASHSCOPE_API_KEY is set in environment variables
            llm_cfg = {
                'model': 'qwen-plus',
                'model_server': 'dashscope',
                'api_key': os.getenv('DASHSCOPE_API_KEY', ''),
            }
        
        # Initialize tools
        tools = [CodeInterpreter()]
        
        # Initialize the Assistant agent
        self.agent = Assistant(
            llm=llm_cfg,
            name='GeneralAgent',
            description='A general-purpose agent capable of coding and planning.',
            function_list=tools
        )

    def run(self, messages):
        """
        Run the agent with the given messages.
        :param messages: List of messages, e.g., [{'role': 'user', 'content': 'Hello'}]
        :return: Generator yielding responses
        """
        return self.agent.run(messages)

if __name__ == "__main__":
    # Simple test
    agent = GeneralAgent()
    messages = [{'role': 'user', 'content': 'Hello, who are you?'}]
    for response in agent.run(messages):
        print(response)
