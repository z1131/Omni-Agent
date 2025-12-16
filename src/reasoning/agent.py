from qwen_agent.agents import Assistant
from typing import Optional, List, Union, Dict
from qwen_agent.tools import BaseTool

class OmniAgent(Assistant):
    """
    OmniAgent: The core agent class for Omni-Agent.
    Inherits from Qwen-Agent's Assistant to leverage RAG and Function Calling.
    """
    def __init__(self, 
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, object]] = None,
                 system_message: Optional[str] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None):
        
        super().__init__(
            function_list=function_list,
            llm=llm,
            system_message=system_message,
            name=name,
            description=description,
            files=files
        )
        
    def _run(self, messages, lang='en', **kwargs):
        # TODO: Add custom logic here (e.g., logging, callbacks)
        return super()._run(messages, lang=lang, **kwargs)
