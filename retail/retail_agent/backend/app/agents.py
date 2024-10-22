# backend/app/agents.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from langchain.schema.messages import HumanMessage, AIMessage
from typing import List, Dict, Any, Optional
import logging
import asyncio
import json
import re
from functools import partial
from .db import Database
from .config import Settings

logger = logging.getLogger(__name__)

class RetailAgent:
    def __init__(self, db: Optional[Database] = None):
        """Initialize the retail agent with database and LLM configurations"""
        self.settings = Settings()
        self.db = db if db is not None else Database()
        
        # Initialize LLMs
        self.primary_llm = ChatGroq(
            api_key=self.settings.GROQ_API_KEY,
            model_name=self.settings.PRIMARY_MODEL
        )
        
        self.fallback_llm = ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            model_name=self.settings.FALLBACK_MODEL,
            temperature=self.settings.TEMPERATURE
        )

        # Set current LLM and memory
        self.current_llm = self.primary_llm
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Create event loop
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        # Initialize tools and agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self.agent_executor = self._create_executor()

    def _create_tools(self) -> List[Tool]:
        """Create the list of tools available to the agent"""
        return [
            Tool(
                name="check_inventory",
                func=self._check_inventory_sync,
                description="Check available shoe inventory. You can specify activity (running/hiking/walking) and/or size."
            )
        ]

    def _create_agent(self):
        """Create the agent with the appropriate prompt template"""
        template = """You are a helpful retail assistant helping customers buy shoes.

Current customer message: {input}

Available tools:
{tools}

You can use: {tool_names}

Follow these steps:
1) Check what shoes we have available
2) Present the options clearly
3) Ask about preferences if needed

Use this format:
Thought: consider what the customer needs
Action: check_inventory
Action Input: specify what to search for
Observation: review the results
Thought: consider how to help the customer
Final Answer: provide a helpful response

Begin!
{agent_scratchpad}"""

        # Create prompt template with all required variables
        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
        )

        return create_react_agent(
            llm=self.current_llm,
            tools=self.tools,
            prompt=prompt
        )

    def _create_executor(self) -> AgentExecutor:
        """Create the agent executor"""
        return AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

    async def _check_inventory_async(self, query: str) -> str:
        """Async implementation of inventory check"""
        try:
            activity = None
            size = None
            
            # Handle "all" query
            if query.lower().strip() in ["all", "", "show all", "everything"]:
                result = await self.db.get_inventory()
            else:
                # Parse query
                if "size" in query.lower():
                    size_match = re.search(r'size\s*(\d+)', query.lower())
                    if size_match:
                        size = size_match.group(1)
                
                activities = ["running", "hiking", "walking"]
                for act in activities:
                    if act in query.lower():
                        activity = act
                        break
                
                result = await self.db.get_inventory(activity=activity, size=size)

            # Format results
            inventory_list = []
            for product in result:
                inventory_list.append({
                    "id": product.id,
                    "name": product.name,
                    "activity": product.activity,
                    "size": product.size,
                    "price": f"${product.price:.2f}",
                    "stock": product.stock
                })
            
            if not inventory_list:
                return "No shoes found matching your criteria."
            
            # Group by activity
            shoes_by_activity = {}
            for item in inventory_list:
                activity = item['activity']
                if activity not in shoes_by_activity:
                    shoes_by_activity[activity] = []
                shoes_by_activity[activity].append(item)
            
            # Create response
            response_parts = ["Here are the available shoes:"]
            for activity, shoes in shoes_by_activity.items():
                response_parts.append(f"\n{activity.capitalize()} Shoes:")
                for shoe in shoes:
                    response_parts.append(
                        f"- {shoe['name']}, Size {shoe['size']}, {shoe['price']}"
                        f" ({shoe['stock']} in stock)"
                    )
            
            response_parts.append("\nWould you like more information about any specific shoe?")
            return "\n".join(response_parts)
                
        except Exception as e:
            logger.error(f"Error in check_inventory: {str(e)}")
            return "Sorry, I had trouble checking the inventory. Please try again."

    def _check_inventory_sync(self, query: str) -> str:
        """Synchronous wrapper for inventory check"""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._check_inventory_async(query),
                self.loop
            )
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Error in sync inventory check: {str(e)}")
            return "Sorry, I had trouble checking the inventory. Please try again."

    async def process_message(self, message: str) -> str:
        """Process a user message and return a response"""
        try:
            # Add message to memory
            self.memory.chat_memory.add_user_message(message)
            
            # Format tools for input
            tools_description = "\n".join(f"- {tool.name}: {tool.description}" for tool in self.tools)
            tool_names = ", ".join(tool.name for tool in self.tools)
            
            try:
                # Try primary LLM
                result = await self.agent_executor.ainvoke({
                    "input": message,
                    "agent_scratchpad": "",
                    "tools": tools_description,
                    "tool_names": tool_names
                })
                response = result.get("output", "I'm sorry, I couldn't process your request.")
                
                # Fallback to inventory if needed
                if "error" in response.lower() or "couldn't process" in response.lower():
                    inventory = await self._check_inventory_async("all")
                    response = f"Let me show you what we have available:\n{inventory}"
                
            except Exception as primary_error:
                logger.error(f"Primary LLM failed: {str(primary_error)}")
                try:
                    # Try fallback LLM
                    self.current_llm = self.fallback_llm
                    self.agent = self._create_agent()
                    self.agent_executor = self._create_executor()
                    
                    result = await self.agent_executor.ainvoke({
                        "input": message,
                        "agent_scratchpad": "",
                        "tools": tools_description,
                        "tool_names": tool_names
                    })
                    response = result.get("output", "I'm sorry, I couldn't process your request.")
                    
                    if "error" in response.lower() or "couldn't process" in response.lower():
                        inventory = await self._check_inventory_async("all")
                        response = f"Let me show you what we have available:\n{inventory}"
                finally:
                    # Reset to primary LLM
                    self.current_llm = self.primary_llm
                    self.agent = self._create_agent()
                    self.agent_executor = self._create_executor()
            
            # Add response to memory
            self.memory.chat_memory.add_ai_message(response)
            return response
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            try:
                inventory = await self._check_inventory_async("all")
                return f"I apologize for the confusion. Let me show you our available shoes:\n{inventory}"
            except:
                return "I apologize, but I'm having trouble accessing the inventory right now. Please try again in a moment."