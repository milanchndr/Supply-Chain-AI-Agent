
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain import hub
from langchain.tools.render import render_text_description


from langchain.memory import ConversationBufferWindowMemory 

from ..agent_tools import DocumentQATool, CustomSQLTool
from ..logger_config import logger
from langchain_community.tools import DuckDuckGoSearchRun

CUSTOM_REACT_PROMPT_STRING_WITH_TOOLS_AND_NAMES = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: You should always think about what to do.
    - First, consider if the question can be answered using company documents (policies, guidelines, procedures). If so, use DocumentPolicySearch.
    - If the question asks for specific data, numbers, lists, or calculations from the supply chain database (like inventory, sales, orders), use SupplyChainDatabaseQuery.
    - If the question is about current events, external information, or general knowledge not found in internal systems, use ExternalWebSearch.
    - If one tool fails or doesn't provide a complete answer, consider if another tool could help or if you need to rephrase the action input.
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action.
    - For DocumentPolicySearch: This MUST be a JSON string with keys "query" (the user's question for the document), "user_role" (use the User Role from CONTEXT FOR TOOLS), and "user_region" (use the User Region from CONTEXT FOR TOOLS). Example: {{"query": "What is the policy for X?", "user_role": "Planning", "user_region": "India"}}
    - For SupplyChainDatabaseQuery: This MUST be a JSON string with keys "natural_language_query" (the user's question for the database), "user_role" (use User Role from CONTEXT FOR TOOLS), "user_region" (use User Region from CONTEXT FOR TOOLS), and "jwt_claims_for_db" (use JWT Claims from CONTEXT FOR TOOLS, this will be a string containing JSON). Example: {{"natural_language_query": "How many items in category Y?", "user_role": "Finance", "user_region": "USA", "jwt_claims_for_db": "eyJhbGciOi..."}}
    - For ExternalWebSearch: This should be a simple string representing the search query. Example: latest news on supply chain disruptions
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer. If the answer comes from a tool, briefly state which tool provided the information.
Final Answer: the final answer to the original input question.

Begin!

---
CHAT HISTORY:
{chat_history} # <--- ADD THIS LINE FOR CONVERSATION HISTORY
---

Question: {input}
Thought:
{agent_scratchpad}

---
CONTEXT FOR TOOLS:
User Role: {user_role}
User Region: {user_region}
JWT Claims (for SupplyChainDatabaseQuery only): {jwt_claims_for_db}
---
"""
def create_supply_chain_agent_executor(llm_instance, qa_chain_instance, db_engine_instance):
    logger.info("Creating Supply Chain Agent Executor...")
    logger.info("Initializing agent tools...")

    doc_tool = DocumentQATool(qa_chain=qa_chain_instance)
    sql_tool = CustomSQLTool(db_engine=db_engine_instance, llm=llm_instance)

    web_search_tool = DuckDuckGoSearchRun(name="ExternalWebSearch")
    web_search_tool.description = (
        "Useful for finding current information, news, public data, or general knowledge "
        "from the internet that is not available in internal documents or the supply chain database. "
        "Input should be a concise search query."
    )

    tools = [doc_tool, sql_tool, web_search_tool]
    tool_names_list = [tool.name for tool in tools]
    logger.info(f"Tools initialized: {tool_names_list}")

    try:
        prompt = ChatPromptTemplate.from_template(CUSTOM_REACT_PROMPT_STRING_WITH_TOOLS_AND_NAMES)

    except Exception as e:
        logger.warning(f"Failed to pull 'hwchase17/react' prompt: {e}. Using custom string prompt as fallback.", exc_info=True)
        prompt = ChatPromptTemplate.from_template(CUSTOM_REACT_PROMPT_STRING_WITH_TOOLS_AND_NAMES)

    expected_vars = ["tools", "tool_names", "input", "agent_scratchpad",
                     "user_role", "user_region", "jwt_claims_for_db",
                     "chat_history"]
    if not all(v in prompt.input_variables for v in expected_vars):
        logger.error(f"Custom prompt string is missing required variables. Expected: {expected_vars}, Found: {prompt.input_variables}")
        raise ValueError(f"Custom prompt string is missing required variables. Found: {prompt.input_variables}")
    logger.info(f"Using custom prompt. Input variables: {prompt.input_variables}")

    try:
        agent = create_react_agent(
            llm=llm_instance,
            tools=tools,
            prompt=prompt
        )
        logger.info("ReAct agent created successfully.")
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}", exc_info=True)
        raise

    # --- MODIFIED: Specify input_key for memory ---
    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        input_key="input",  # <--- ADD THIS LINE
        return_messages=True,
        k=5
    )
    logger.info(f"Initialized ConversationBufferWindowMemory with memory_key='chat_history', input_key='input', k={memory.k} turns.")


    try:
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors="I apologize, I encountered an issue processing the previous step. I will try a different approach.",
            max_iterations=10,
            memory=memory
        )
        logger.info("AgentExecutor created successfully with conversational memory.")
        return executor
    except Exception as e:
        logger.error(f"Failed to create AgentExecutor: {e}", exc_info=True)
        raise