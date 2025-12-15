import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from agent import GeneralAgent

def test_agent_init():
    try:
        # We might not have an API key, so we expect it might fail on run, 
        # but init should be fine if it doesn't check key immediately.
        # Or we can mock the key.
        os.environ['DASHSCOPE_API_KEY'] = 'sk-dummy'
        agent = GeneralAgent()
        print("Agent initialized successfully.")
    except Exception as e:
        print(f"Agent initialization failed: {e}")

if __name__ == "__main__":
    test_agent_init()
