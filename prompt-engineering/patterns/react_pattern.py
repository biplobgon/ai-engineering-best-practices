"""
ReAct prompting: Reasoning + Acting in interleaved loop.

Pattern: Thought → Action → Observation → (repeat)

Use when:
- Agent systems with tool use
- Need to access external data
- Multi-step tasks with decisions

Cost: ~500-2000 tokens per query (depends on iterations)
Quality: ⭐⭐⭐⭐⭐ (best for complex tasks)

Key insight: Interleaving reasoning and acting improves both.

Examples:
- Research assistant (search + summarize)
- Data analysis agent (query + plot)
- Customer support (lookup + respond)
"""

import asyncio
import json
import logging
from typing import Any, Callable

from core.llm import chat
from core.schemas import LLMResponse


logger = logging.getLogger(__name__)


class Tool:
    """Base tool for ReAct agent."""

    def __init__(self, name: str, description: str, function: Callable):
        """
        Initialize tool.

        Args:
            name: Tool name
            description: What the tool does
            function: Async function to call
        """
        self.name = name
        self.description = description
        self.function = function

    async def call(self, **kwargs: Any) -> str:
        """Call tool function."""
        try:
            result = await self.function(**kwargs)
            return str(result)
        except Exception as e:
            logger.error(f"Tool {self.name} error: {e}")
            return f"Error: {e}"


async def run(
    query: str,
    tools: list[Tool],
    max_iterations: int = 5,
    model: str | None = None,
    temperature: float = 0.0,
) -> dict[str, Any]:
    """
    Run ReAct loop.

    Args:
        query: User query/task
        tools: Available tools
        max_iterations: Max thought-action cycles
        model: Model to use
        temperature: Sampling temperature

    Returns:
        Dict with trajectory, answer, and metadata

    Example:
        >>> tools = [
        ...     Tool("search", "Search the web", search_function),
        ...     Tool("calculator", "Do math", calc_function),
        ... ]
        >>> result = await react_pattern.run(
        ...     "What's the population of the largest city in France?",
        ...     tools=tools
        ... )
        >>> print(result['answer'])
    """
    # Build tool descriptions
    tool_descriptions = "\n".join(
        [f"- {tool.name}: {tool.description}" for tool in tools]
    )

    # System prompt
    system_prompt = f"""You are an agent that can use tools to answer questions.

Available tools:
{tool_descriptions}

Use this format:

Thought: [your reasoning about what to do next]
Action: [tool_name]
Action Input: [input to the tool]
Observation: [tool output will appear here]
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Final Answer: [your final answer to the user]

Begin!"""

    # Initialize conversation
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Question: {query}"},
    ]

    trajectory = []
    total_tokens = 0
    total_cost = 0.0

    for iteration in range(max_iterations):
        # Get next thought/action
        response = await chat(messages, model=model, temperature=temperature)

        total_tokens += response.total_tokens
        total_cost += response.usd_cost

        text = response.text.strip()

        # Parse response
        if "Final Answer:" in text:
            # Extract final answer
            final_answer = text.split("Final Answer:")[-1].strip()

            trajectory.append({
                "iteration": iteration + 1,
                "type": "final_answer",
                "content": final_answer,
            })

            return {
                "query": query,
                "trajectory": trajectory,
                "answer": final_answer,
                "iterations": iteration + 1,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
            }

        # Extract thought and action
        thought = ""
        action = ""
        action_input = ""

        if "Thought:" in text:
            thought = text.split("Thought:")[-1].split("Action:")[0].strip()

        if "Action:" in text:
            action = text.split("Action:")[-1].split("Action Input:")[0].strip()

        if "Action Input:" in text:
            action_input = text.split("Action Input:")[-1].strip()

        trajectory.append({
            "iteration": iteration + 1,
            "type": "thought",
            "content": thought,
        })

        # Execute action
        tool = next((t for t in tools if t.name.lower() == action.lower()), None)

        if tool:
            # Call tool
            observation = await tool.call(input=action_input)

            trajectory.append({
                "iteration": iteration + 1,
                "type": "action",
                "tool": tool.name,
                "input": action_input,
            })

            trajectory.append({
                "iteration": iteration + 1,
                "type": "observation",
                "content": observation,
            })

            # Add observation to conversation
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": f"Observation: {observation}"})

        else:
            # Invalid action
            error = f"Error: Unknown tool '{action}'. Available: {[t.name for t in tools]}"

            trajectory.append({
                "iteration": iteration + 1,
                "type": "error",
                "content": error,
            })

            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": error})

    # Max iterations reached
    return {
        "query": query,
        "trajectory": trajectory,
        "answer": "Max iterations reached without final answer",
        "iterations": max_iterations,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }


# Example tools
async def mock_search(input: str, **kwargs: Any) -> str:
    """Mock web search tool."""
    # In production, this would call a real search API
    search_results = {
        "paris population": "Paris population: 2.1 million (city proper), 12.4 million (metro area)",
        "largest city france": "Paris is the largest city in France",
        "eiffel tower height": "The Eiffel Tower is 330 meters (1,083 feet) tall",
    }

    query = input.lower()

    for key, value in search_results.items():
        if key in query:
            return value

    return f"Search results for '{input}': No specific data available"


async def mock_calculator(input: str, **kwargs: Any) -> str:
    """Mock calculator tool."""
    try:
        # Safely evaluate math expression
        result = eval(input, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Calculator error: {e}"


async def mock_database_query(input: str, **kwargs: Any) -> str:
    """Mock database query tool."""
    # In production, this would query a real database
    mock_data = {
        "customer count": "Total customers: 1,247",
        "revenue": "Total revenue: $523,891",
        "active users": "Active users: 892",
    }

    query = input.lower()

    for key, value in mock_data.items():
        if key in query:
            return value

    return f"Query result: No data found for '{input}'"


# Demo use cases
async def research_assistant(question: str) -> dict[str, Any]:
    """
    Research assistant using ReAct.

    Args:
        question: Research question

    Returns:
        Dict with answer and trajectory

    Cost: ~$0.001-0.002 per query (Haiku, depends on iterations)

    Example:
        >>> result = await react_pattern.research_assistant(
        ...     "What's the population of Paris?"
        ... )
        >>> print(result['answer'])
    """
    tools = [
        Tool("search", "Search for information on the web", mock_search),
        Tool("calculator", "Perform mathematical calculations", mock_calculator),
    ]

    return await run(question, tools=tools, max_iterations=5)


async def data_analyst(question: str) -> dict[str, Any]:
    """
    Data analyst agent using ReAct.

    Args:
        question: Data analysis question

    Returns:
        Dict with answer and trajectory

    Cost: ~$0.001-0.002 per query (Haiku)

    Example:
        >>> result = await react_pattern.data_analyst(
        ...     "What's our customer count and revenue?"
        ... )
        >>> print(result['answer'])
    """
    tools = [
        Tool("database", "Query the database", mock_database_query),
        Tool("calculator", "Perform calculations", mock_calculator),
    ]

    return await run(question, tools=tools, max_iterations=5)


# Benchmark function
async def benchmark(num_queries: int = 20) -> dict[str, Any]:
    """
    Benchmark ReAct pattern.

    Args:
        num_queries: Number of test queries

    Returns:
        Benchmark results

    Note: ReAct is significantly more expensive than other patterns
    """
    import time

    test_questions = [
        "What's the population of the largest city in France?",
        "How tall is the Eiffel Tower in feet?",
        "What's the total of 123 + 456?",
    ] * (num_queries // 3 + 1)

    costs = []
    latencies = []
    tokens_list = []
    iterations_list = []

    for question in test_questions[:num_queries]:
        start = time.time()
        result = await research_assistant(question)
        latency_ms = (time.time() - start) * 1000

        costs.append(result["total_cost"])
        latencies.append(latency_ms)
        tokens_list.append(result["total_tokens"])
        iterations_list.append(result["iterations"])

    latencies.sort()

    return {
        "num_queries": num_queries,
        "total_cost": sum(costs),
        "avg_cost": sum(costs) / len(costs),
        "avg_tokens": sum(tokens_list) / len(tokens_list),
        "avg_iterations": sum(iterations_list) / len(iterations_list),
        "avg_latency_ms": sum(latencies) / len(latencies),
        "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
        "p99_latency_ms": latencies[int(len(latencies) * 0.99)],
    }


# Demo script
async def main():
    """Demo ReAct pattern."""
    print("=" * 60)
    print("ReAct Pattern Demo")
    print("=" * 60)

    # 1. Research assistant
    print("\n1. Research Assistant")
    print("-" * 60)

    question = "What's the population of the largest city in France?"
    result = await research_assistant(question)

    print(f"Question: {question}")
    print("\nTrajectory:")

    for step in result["trajectory"]:
        if step["type"] == "thought":
            print(f"\n💭 Thought: {step['content']}")
        elif step["type"] == "action":
            print(f"🔧 Action: {step['tool']}({step['input']})")
        elif step["type"] == "observation":
            print(f"👁️  Observation: {step['content']}")
        elif step["type"] == "final_answer":
            print(f"\n✅ Final Answer: {step['content']}")

    print(f"\nMetrics:")
    print(f"- Iterations: {result['iterations']}")
    print(f"- Tokens: {result['total_tokens']}")
    print(f"- Cost: ${result['total_cost']:.4f}")

    # 2. Data analyst
    print("\n\n2. Data Analyst Agent")
    print("-" * 60)

    question = "What's our total customer count?"
    result = await data_analyst(question)

    print(f"Question: {question}")
    print(f"\nAnswer: {result['answer']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Cost: ${result['total_cost']:.4f}")

    # 3. Cost comparison
    print("\n\n" + "=" * 60)
    print("ReAct vs Other Patterns")
    print("=" * 60)
    print("Zero-shot: ~120 tokens, $0.0001, no tool use")
    print("Few-shot: ~450 tokens, $0.0003, no tool use")
    print("CoT: ~620 tokens, $0.0004, reasoning only")
    print("ReAct: ~1200 tokens, $0.001, reasoning + tools")
    print("\nReAct is 10x more expensive but enables agent capabilities")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
