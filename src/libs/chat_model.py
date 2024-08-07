import os
import logging
from dotenv import load_dotenv

from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatDatabricks
from langchain_core.messages import SystemMessage




class RetailLLM():

    def __init__(self, system_message, tools=None, model_name="databricks-dbrx-instruct"):
        load_dotenv()

        self.system_message = SystemMessage(system_message)
        self.model_name = model_name
        self.model = ChatDatabricks(endpoint=self.model_name)
        self.tools = tools

        # configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

        assert os.getenv('DATABRICKS_TOKEN') is not None and os.getenv('DATABRICKS_HOST') is not None, "DATABRICKS_TOKEN and DATABRICKS_HOST environment variables must be set."
        
        memory = ConversationBufferMemory(memory_key="chat_history")
        self.agent = initialize_agent(
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            tools=self.tools,
            llm=self.model,
            verbose=True,
            max_iterations=3,
            memory=memory,
        )

        self.reset_chat_history()
        self.logger.info("----- Retail LLM Class Initialized. ")
        

    
    def reset_chat_history(self):
        """Resets AI messages to the default system prompt with no user/assistant entries. """
        self.chat_history = []
        self.chat_history.append(self.system_message)
        self.agent.memory.clear()



    def add_message(self, msg):
        """Adds a message to the messages list as a dictionary. 

        Args:
            role (str): Either 'AI' or 'HUMAN' representing the actors role in the conversation.  
            msg (str): The message to send to the AI
        """
        self.chat_history.append(msg)
    
    def edit_system_message(self, msg, reset = False):
        """Allows edits to the system message. This is typically used to pass additional environment information that may have changed. 

        Args:
            msg (str): The message to append to the system message.
            reset (bool, optional): If true will reset the system message to the default value allowing us to erase any additional information provided to the AI. Defaults to False.
        """
        self.chat_history[0]['content'] += f"{msg}. "
        if reset: 
            self.chat_history[0]['content'] = self.system_message

    def send_chat(self, msg):
        """Sends the chat history to the LLM to get response. """
        self.logger.info("Chat History: %s", self.chat_history)
        # response = self.model.invoke(self.chat_history)
        response = self.agent.invoke(msg)
        self.logger.info("AI Response: %s", response.get('output'))

        return response.get('output')

    def get_chat_history(self):
        return self.agent.memory.chat_memory.messages 

