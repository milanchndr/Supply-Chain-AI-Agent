# backend/utils/agent_handler.py

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate # Using ChatPromptTemplate as it's more common with hub.pull
from langchain import hub # For pulling prompts
from langchain.tools.render import render_text_description # Corrected import for rendering tools

from ..agent_tools import DocumentQATool, CustomSQLTool
from ..logger_config import logger
from langchain_community.tools import DuckDuckGoSearchRun

# This is your custom template string, ensure it has all placeholders
# create_react_agent expects 'input', 'agent_scratchpad', and it will fill 'tools' and 'tool_names'
CUSTOM_REACT_PROMPT_STRING_WITH_TOOLS_AND_NAMES = """Answer the following questions as best you can. You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do. Prioritize internal documents and database. Use web search for current or external information. If web search results might conflict with internal policies, cross-verify with DocumentPolicySearch.
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:
{agent_scratchpad}"""


def create_supply_chain_agent_executor(llm_instance, qa_chain_instance, db_engine_instance):
    logger.info("Creating Supply Chain Agent Executor...")
    logger.info("Initializing agent tools...")

    doc_tool = DocumentQATool(qa_chain=qa_chain_instance)
    sql_tool = CustomSQLTool(db_engine=db_engine_instance, llm=llm_instance)
    
    web_search_tool = DuckDuckGoSearchRun(name="ExternalWebSearch")
    web_search_tool.description = (
        "Useful for finding current information, news, public data, or general knowledge "
        "from the internet that is not available in internal documents or databases. "
        "For example, current market trends, news about a supplier not in our database, "
        "or general industry information."
    )
    
    tools = [doc_tool, sql_tool, web_search_tool]
    tool_names_list = [tool.name for tool in tools]
    logger.info(f"Tools initialized: {tool_names_list}")

    # --- AGENT PROMPT ---
    # Attempt to pull a tried-and-tested ReAct prompt from Langchain Hub
    # This prompt is specifically designed for ReAct agents and includes necessary placeholders.
    try:
        # "hwchase17/react-chat" is for chat models, "hwchase17/react" for LLMs.
        # Your BedrockLLM is a BaseLLM, so "hwchase17/react" is more appropriate.
        prompt = hub.pull("hwchase17/react")
        logger.info(f"Successfully pulled prompt 'hwchase17/react'. Input variables: {prompt.input_variables}")
        # Expected input_variables for this hub prompt: ['input', 'agent_scratchpad', 'tool_names', 'tools']
        # If any are missing, that's an issue with the hub or your langchain version.
        if not all(v in prompt.input_variables for v in ["tools", "tool_names", "input", "agent_scratchpad"]):
            logger.warning("Pulled prompt 'hwchase17/react' is missing expected variables. Attempting custom prompt.")
            raise ValueError("Pulled prompt validation failed.") # Force fallback
    except Exception as e:
        logger.error(f"Failed to pull 'hwchase17/react' prompt: {e}. Using custom string prompt.", exc_info=True)
        # Fallback to your custom template string
        # Ensure it has all required placeholders: input, agent_scratchpad, tools, tool_names
        try:
            prompt = ChatPromptTemplate.from_template(CUSTOM_REACT_PROMPT_STRING_WITH_TOOLS_AND_NAMES)
            # Verify input variables if using from_template on a string
            if not all(v in prompt.input_variables for v in ["tools", "tool_names", "input", "agent_scratchpad"]):
                logger.error(f"Custom prompt string is ALSO missing required variables. Found: {prompt.input_variables}")
                raise ValueError(f"Custom prompt string is ALSO missing required variables. Found: {prompt.input_variables}")
            logger.info(f"Using custom prompt. Input variables: {prompt.input_variables}")
        except Exception as e_custom:
            logger.error(f"Failed to create prompt from custom string: {e_custom}", exc_info=True)
            raise  # Re-raise if custom prompt also fails

    logger.info(f"Final prompt template to be used:\n{prompt.template if hasattr(prompt, 'template') else 'Prompt is a ChatPromptTemplate, view messages.'}")
    logger.info(f"Final prompt input_variables: {prompt.input_variables}")

    # 3. Create the Agent
    try:
        # The create_react_agent function will internally handle formatting the tools
        # and tool_names into the prompt if the placeholders are present.
        agent = create_react_agent(
            llm=llm_instance,
            tools=tools,        # List of Tool objects
            prompt=prompt       # The PromptTemplate or ChatPromptTemplate object
        )
        logger.info("ReAct agent created successfully.")
    except ValueError as ve:
        logger.error(f"ValueError during create_react_agent: {ve}", exc_info=True)
        # This error means the prompt passed still doesn't meet create_react_agent's expectations.
        # Specifically, create_react_agent wants to be able to .partial() format 'tools' and 'tool_names'
        # into the prompt. So, the prompt object must have these as recognized input_variables.
        raise
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}", exc_info=True)
        raise

    # 4. Create an Agent Executor
    try:
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True, # Crucial for ReAct robustness
            max_iterations=10,
        )
        logger.info("AgentExecutor created successfully.")
        return executor
    except Exception as e:
        logger.error(f"Failed to create AgentExecutor: {e}", exc_info=True)
        raise

# ... (if __name__ == '__main__' block for testing if desired)