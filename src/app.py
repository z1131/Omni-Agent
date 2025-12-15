import gradio as gr
from agent import GeneralAgent

def chat(message, history):
    # Initialize agent (in a real app, might want to persist or manage state better)
    # For now, we re-initialize or use a global one. 
    # Better to use a global instance for simple demo.
    
    messages = []
    for user_msg, bot_msg in history:
        messages.append({'role': 'user', 'content': user_msg})
        messages.append({'role': 'assistant', 'content': bot_msg})
    
    messages.append({'role': 'user', 'content': message})
    
    agent = GeneralAgent()
    response_generator = agent.run(messages)
    
    full_response = ""
    for response in response_generator:
        # qwen-agent returns a list of responses, we usually take the last one or stream
        # The response format depends on the agent implementation.
        # Assistant.run yields a list of outputs.
        if isinstance(response, list):
            latest_response = response[-1]
            if 'content' in latest_response:
                full_response = latest_response['content']
                yield full_response
        elif isinstance(response, dict):
             if 'content' in response:
                full_response = response['content']
                yield full_response

demo = gr.ChatInterface(
    fn=chat,
    title="General Agent (Powered by Qwen-Agent)",
    description="A general-purpose agent capable of coding and planning.",
)

if __name__ == "__main__":
    demo.launch()
