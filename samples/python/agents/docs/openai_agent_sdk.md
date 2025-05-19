I'll explore the project and create a comprehensive tutorial for software developers interested in building advanced agents. Let me start by examining the repository structure.

Let's first check the README to understand what this project is about:

Now, let's look at the structure of the source code to understand the key components:

Let's check out the examples to understand the use cases and implementations:

Let's take a look at the core `agent.py` file to understand the Agent class definition:

Let's also examine the runner implementation to understand how agents execute:

Let's check the AGENTS.md for additional information:

Now, let's examine one of the sample agents from the examples:

Let's look at one of the agent implementations:

Now let's look at a complex pattern example:

Let's look at another pattern example:

Now let's examine the guardrails functionality:

Based on my exploration of the repository, I'll now create a comprehensive tutorial on building advanced agents with the OpenAI Agents SDK.

Let's try creating a simpler diagram for visualization:

Now, I'll create a comprehensive tutorial on building advanced agents with the OpenAI Agents SDK:

# Advanced Agent Development with OpenAI Agents SDK

## Introduction

The OpenAI Agents SDK is a powerful framework for building intelligent agent systems using Large Language Models (LLMs). This tutorial will guide software developers through creating sophisticated agent architectures that can tackle complex tasks through collaboration, tool use, and orchestration.

The SDK is designed with four core concepts:

1. **Agents**: LLMs configured with instructions, tools, guardrails, and handoffs
2. **Handoffs**: Specialized tool calls for transferring control between agents
3. **Guardrails**: Configurable safety checks for input and output validation
4. **Tracing**: Built-in tracking of agent runs for debugging and optimization

This tutorial will explain these concepts in depth and show you how to build advanced agent systems.

## Table of Contents

1. [Setting Up Your Environment](#setting-up-your-environment)
2. [Understanding the Core Concepts](#understanding-the-core-concepts)
3. [Building Your First Agent](#building-your-first-agent)
4. [Working with Tools](#working-with-tools)
5. [Implementing Agent Handoffs](#implementing-agent-handoffs)
6. [Creating Guardrails](#creating-guardrails)
7. [Advanced Agent Patterns](#advanced-agent-patterns)
8. [Debugging and Optimization with Tracing](#debugging-and-optimization-with-tracing)
9. [Complete Multi-Agent System Example](#complete-multi-agent-system-example)

## Setting Up Your Environment

First, let's set up our development environment:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the Agents SDK
pip install openai-agents

# For voice support (optional)
pip install 'openai-agents[voice]'

# Make sure your OpenAI API key is available
# Either set it as an environment variable:
export OPENAI_API_KEY=your-api-key
# Or use it in your code:
# os.environ["OPENAI_API_KEY"] = "your-api-key"
```

## Understanding the Core Concepts

### Agents

An agent is the core abstraction in the SDK, representing an LLM configured with specific instructions, tools, guardrails, and other settings. The `Agent` class encapsulates all these components:

```python
from agents import Agent

my_agent = Agent(
    name="MyAssistant",
    instructions="You are a helpful assistant that provides concise information.",
    model="gpt-4o",  # You can specify different models
    tools=[],  # List of tools the agent can use
    handoffs=[],  # List of other agents this agent can hand off to
    input_guardrails=[],  # Safety checks for input
    output_guardrails=[],  # Safety checks for output
    output_type=None,  # Type for structured output (defaults to string)
)
```

### Runner

The `Runner` class executes agents. It handles the agent execution loop, processes responses, manages handoffs, and more:

```python
from agents import Runner

# Run an agent synchronously
result = Runner.run_sync(my_agent, "What's the weather in San Francisco?")
print(result.final_output)

# Run an agent asynchronously
import asyncio
async def run_agent():
    result = await Runner.run(my_agent, "What's the weather in San Francisco?")
    print(result.final_output)

asyncio.run(run_agent())

# Run an agent with streaming outputs
async def run_streaming():
    result = Runner.run_streamed(my_agent, "Tell me a long story")
    async for event in result.stream_events():
        # Process streaming events
        print(event)

asyncio.run(run_streaming())
```

## Building Your First Agent

Let's create a simple agent that responds to user queries:

```python
from agents import Agent, Runner

# Create a basic agent
assistant = Agent(
    name="Assistant",
    instructions="You are a helpful assistant that provides concise information.",
)

# Run the agent
result = Runner.run_sync(assistant, "What are the benefits of exercise?")
print(result.final_output)
```

### Structured Output

For more structured responses, we can define an output type:

```python
from pydantic import BaseModel, Field
from agents import Agent, Runner

class WeatherResponse(BaseModel):
    temperature: float = Field(description="Current temperature in Celsius")
    conditions: str = Field(description="Weather conditions (e.g., sunny, rainy)")
    forecast: str = Field(description="Brief forecast for the next 24 hours")

weather_agent = Agent(
    name="WeatherAgent",
    instructions="You provide weather information based on the user's query.",
    output_type=WeatherResponse
)

result = Runner.run_sync(weather_agent, "What's the weather in London?")
weather_data = result.final_output_as(WeatherResponse)
print(f"Temperature: {weather_data.temperature}°C")
print(f"Conditions: {weather_data.conditions}")
print(f"Forecast: {weather_data.forecast}")
```

## Working with Tools

Tools are functions that agents can call to perform actions or fetch information. The SDK provides a simple way to create tools using the `function_tool` decorator:

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

@function_tool
def search_database(query: str) -> list[str]:
    """Search the database for information."""
    # This would connect to a real database in production
    return [f"Result for '{query}'", "Another result"]

# Create an agent with tools
tool_using_agent = Agent(
    name="ToolUser",
    instructions=(
        "You are a helpful assistant with access to tools. "
        "Use them when necessary to answer the user's question."
    ),
    tools=[get_current_time, search_database],
)

result = Runner.run_sync(tool_using_agent, "What time is it and can you search for 'python'?")
print(result.final_output)
```

### Controlling Tool Use Behavior

You can control how the agent uses tools:

```python
from agents import Agent

# Default behavior: run tools, then LLM processes results
default_agent = Agent(
    name="DefaultToolUser",
    tools=[get_current_time, search_database],
    tool_use_behavior="run_llm_again"  # Default
)

# Stop after first tool call, using its output as final result
single_tool_agent = Agent(
    name="SingleToolUser",
    tools=[get_current_time, search_database],
    tool_use_behavior="stop_on_first_tool"
)

# Stop only if specific tools are called
selective_stop_agent = Agent(
    name="SelectiveStopAgent",
    tools=[get_current_time, search_database],
    tool_use_behavior={"stop_at_tool_names": ["search_database"]}
)

# Custom function to decide when to stop
def custom_tool_handler(context, tool_results):
    from agents import ToolsToFinalOutputResult
    # Stop if search_database was called, otherwise continue
    for result in tool_results:
        if result.name == "search_database":
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=f"Search result: {result.output}"
            )
    return ToolsToFinalOutputResult(is_final_output=False)

custom_agent = Agent(
    name="CustomToolUser",
    tools=[get_current_time, search_database],
    tool_use_behavior=custom_tool_handler
)
```

## Implementing Agent Handoffs

Handoffs allow one agent to transfer control to another agent. This is useful for building specialized agents that collaborate:

```python
from agents import Agent, Runner

# Create specialized agents
weather_specialist = Agent(
    name="WeatherSpecialist",
    instructions="You are an expert on weather. Provide detailed weather information.",
)

travel_specialist = Agent(
    name="TravelSpecialist",
    instructions="You are a travel expert. Recommend destinations and activities.",
)

# Create a router agent with handoffs
router_agent = Agent(
    name="RouterAgent",
    instructions=(
        "Route the query to the appropriate specialist. "
        "For weather questions, hand off to the WeatherSpecialist. "
        "For travel questions, hand off to the TravelSpecialist. "
        "For other questions, answer directly."
    ),
    handoffs=[weather_specialist, travel_specialist],
)

# Run the agent - it will hand off to the appropriate specialist
result = Runner.run_sync(router_agent, "What's the weather like in Paris?")
print(f"Handled by: {result._last_agent.name}")
print(result.final_output)

result = Runner.run_sync(router_agent, "What are some good tourist spots in Tokyo?")
print(f"Handled by: {result._last_agent.name}")
print(result.final_output)
```

### Agents as Tools

Another powerful pattern is using agents as tools, which allows one agent to call another without giving up control:

```python
from agents import Agent, Runner

# Create specialist agents
spanish_translator = Agent(
    name="SpanishTranslator",
    instructions="You translate text to Spanish.",
)

french_translator = Agent(
    name="FrenchTranslator",
    instructions="You translate text to French.",
)

# Create an orchestrator agent with specialist agents as tools
orchestrator = Agent(
    name="TranslationOrchestrator",
    instructions=(
        "You manage translations based on user requests. "
        "Use the appropriate translation tool when needed."
    ),
    tools=[
        spanish_translator.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate text to Spanish"
        ),
        french_translator.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate text to French"
        ),
    ],
)

# Run the orchestrator
result = Runner.run_sync(
    orchestrator,
    "Please translate 'Hello, how are you?' to Spanish and French."
)
print(result.final_output)
```

## Creating Guardrails

Guardrails provide safety checks for agent inputs and outputs. They can prevent harmful content, validate outputs, and ensure responses meet your requirements:

### Input Guardrails

```python
from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, input_guardrail

@input_guardrail
async def sensitive_topic_check(
    context: RunContextWrapper,
    agent: Agent,
    input_text: str
) -> GuardrailFunctionOutput:
    # Check if input contains sensitive topics
    sensitive_keywords = ["password", "credit card", "ssn", "social security"]
    contains_sensitive = any(keyword in input_text.lower() for keyword in sensitive_keywords)

    return GuardrailFunctionOutput(
        output_info={"contains_sensitive_info": contains_sensitive},
        tripwire_triggered=contains_sensitive,
    )

# Create an agent with input guardrails
safe_agent = Agent(
    name="SafeAgent",
    instructions="You are a helpful assistant.",
    input_guardrails=[sensitive_topic_check],
)

# This will run normally
try:
    result = Runner.run_sync(safe_agent, "What's the capital of France?")
    print(result.final_output)
except Exception as e:
    print(f"Error: {e}")

# This will trigger the guardrail
try:
    result = Runner.run_sync(safe_agent, "What's my credit card number?")
    print(result.final_output)
except Exception as e:
    print(f"Error: {e}")
```

### Output Guardrails

```python
from pydantic import BaseModel, Field
from agents import Agent, GuardrailFunctionOutput, output_guardrail

class ReviewResponse(BaseModel):
    rating: int = Field(description="Rating from 1-5")
    review: str = Field(description="Detailed review text")

@output_guardrail
async def rating_range_check(
    context: RunContextWrapper,
    agent: Agent,
    output: ReviewResponse
) -> GuardrailFunctionOutput:
    # Ensure rating is within valid range
    is_valid = 1 <= output.rating <= 5

    return GuardrailFunctionOutput(
        output_info={"valid_rating": is_valid},
        tripwire_triggered=not is_valid,
    )

# Create an agent with output guardrails
review_agent = Agent(
    name="ReviewAgent",
    instructions="You write product reviews based on user descriptions.",
    output_type=ReviewResponse,
    output_guardrails=[rating_range_check],
)

# Run the agent
try:
    result = Runner.run_sync(review_agent, "Review the latest iPhone.")
    print(f"Rating: {result.final_output.rating}/5")
    print(f"Review: {result.final_output.review}")
except Exception as e:
    print(f"Error: {e}")
```

## Advanced Agent Patterns

The SDK supports several advanced agent patterns:

### Deterministic Flows

Create a sequence of predefined steps, where each agent has a specific role in a pipeline:

```python
import asyncio
from agents import Agent, Runner, trace

async def deterministic_pipeline(query: str):
    # Create a trace to track the entire flow
    with trace("Deterministic Pipeline"):
        # 1. Planning step
        planner_agent = Agent(
            name="Planner",
            instructions="Create a plan to answer the user's query",
        )
        plan_result = await Runner.run(planner_agent, query)
        plan = plan_result.final_output

        # 2. Research step
        researcher_agent = Agent(
            name="Researcher",
            instructions="Research information based on the plan",
        )
        research_result = await Runner.run(
            researcher_agent,
            f"Plan: {plan}\nQuery: {query}"
        )
        research = research_result.final_output

        # 3. Writing step
        writer_agent = Agent(
            name="Writer",
            instructions="Write a final response based on research",
        )
        write_result = await Runner.run(
            writer_agent,
            f"Query: {query}\nResearch: {research}"
        )

        return write_result.final_output

# Run the pipeline
async def main():
    result = await deterministic_pipeline(
        "What are the pros and cons of renewable energy?"
    )
    print(result)

asyncio.run(main())
```

### Parallelization

Execute multiple agents in parallel and combine their results:

```python
import asyncio
from agents import Agent, Runner, trace

async def parallel_processing(query: str):
    # Create specialized agents for different aspects
    economic_agent = Agent(
        name="EconomicAnalyst",
        instructions="Analyze the economic aspects of the query",
    )

    environmental_agent = Agent(
        name="EnvironmentalAnalyst",
        instructions="Analyze the environmental aspects of the query",
    )

    social_agent = Agent(
        name="SocialAnalyst",
        instructions="Analyze the social aspects of the query",
    )

    # Run agents in parallel
    with trace("Parallel Analysis"):
        economic_task = asyncio.create_task(Runner.run(economic_agent, query))
        environmental_task = asyncio.create_task(Runner.run(environmental_agent, query))
        social_task = asyncio.create_task(Runner.run(social_agent, query))

        # Wait for all analyses to complete
        economic_result, environmental_result, social_result = await asyncio.gather(
            economic_task, environmental_task, social_task
        )

        # Combine results with a synthesis agent
        synthesizer = Agent(
            name="Synthesizer",
            instructions="Synthesize multiple analyses into a cohesive response",
        )

        synthesis_result = await Runner.run(
            synthesizer,
            f"""Query: {query}
            Economic Analysis: {economic_result.final_output}
            Environmental Analysis: {environmental_result.final_output}
            Social Analysis: {social_result.final_output}"""
        )

        return synthesis_result.final_output

# Run the parallel analysis
async def main():
    result = await parallel_processing(
        "What would be the impact of implementing a carbon tax?"
    )
    print(result)

asyncio.run(main())
```

### LLM as a Judge

Have an LLM act as a judge to evaluate and select from multiple responses:

```python
import asyncio
from pydantic import BaseModel, Field
from agents import Agent, Runner, trace

class JudgmentResult(BaseModel):
    best_response: int = Field(description="Index of the best response (1, 2, or 3)")
    reasoning: str = Field(description="Reasoning for the selection")

async def llm_judge_pattern(query: str):
    # Create multiple agents with different approaches
    agent1 = Agent(
        name="Factual",
        instructions="Provide a factual, concise response focusing on accuracy.",
    )

    agent2 = Agent(
        name="Creative",
        instructions="Provide a creative, engaging response with analogies and examples.",
    )

    agent3 = Agent(
        name="Balanced",
        instructions="Provide a balanced view exploring multiple perspectives.",
    )

    # Run all agents
    with trace("LLM Judge Pattern"):
        results = await asyncio.gather(
            Runner.run(agent1, query),
            Runner.run(agent2, query),
            Runner.run(agent3, query),
        )

        # Create a judge agent
        judge_agent = Agent(
            name="Judge",
            instructions=(
                "You are a judge evaluating different responses to a query. "
                "Select the best response based on accuracy, helpfulness, and clarity."
            ),
            output_type=JudgmentResult
        )

        # Have the judge select the best response
        judge_result = await Runner.run(
            judge_agent,
            f"""Query: {query}

            Response 1 (Factual):
            {results[0].final_output}

            Response 2 (Creative):
            {results[1].final_output}

            Response 3 (Balanced):
            {results[2].final_output}

            Evaluate the responses and select the best one."""
        )

        # Return the selected response with the reasoning
        judgment = judge_result.final_output
        selected_index = judgment.best_response - 1  # Convert to 0-indexed

        return {
            "selected_response": results[selected_index].final_output,
            "reasoning": judgment.reasoning,
            "agent_name": [agent1, agent2, agent3][selected_index].name
        }

# Run the LLM judge pattern
async def main():
    result = await llm_judge_pattern(
        "Explain the concept of quantum computing to a high school student."
    )
    print(f"Selected response from {result['agent_name']}:")
    print(result["selected_response"])
    print("\nReasoning:")
    print(result["reasoning"])

asyncio.run(main())
```

## Debugging and Optimization with Tracing

The SDK includes built-in tracing to help debug and optimize your agent workflows:

```python
import asyncio
import uuid
from agents import Agent, Runner, trace, gen_trace_id

async def traced_workflow():
    # Generate a unique trace ID
    trace_id = gen_trace_id()

    # Create a trace scope
    with trace("Customer Support Workflow", trace_id=trace_id):
        print(f"Trace ID: {trace_id}")
        # View this trace at: https://platform.openai.com/traces/trace?trace_id={trace_id}

        # Run your agent workflow
        agent = Agent(
            name="SupportAgent",
            instructions="You are a helpful customer support representative.",
        )

        result = await Runner.run(agent, "I'm having trouble with my account")
        return result.final_output

asyncio.run(traced_workflow())
```

For more complex workflows, you can create custom spans to track specific operations:

```python
from agents import custom_span

with trace("Complex Research Flow"):
    # Start a custom span for a specific operation
    with custom_span("Data Gathering"):
        # Code for gathering data
        data = get_data()

    # Another span for processing
    with custom_span("Data Processing"):
        # Process the data
        processed_data = process_data(data)

    # Final span for agent execution
    with custom_span("Agent Execution"):
        result = Runner.run_sync(agent, f"Analyze this: {processed_data}")
```

## Complete Multi-Agent System Example

Now let's build a complete multi-agent system for financial research, similar to the example in the SDK repository:

```python
import asyncio
from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool, trace, gen_trace_id, custom_span

# Define our data models
class SearchItem(BaseModel):
    query: str = Field(description="The search term")
    reason: str = Field(description="Reason for this search")

class SearchPlan(BaseModel):
    searches: list[SearchItem] = Field(description="List of searches to perform")

class AnalysisSummary(BaseModel):
    summary: str = Field(description="Summary of analysis")
    key_points: list[str] = Field(description="Key points from the analysis")

class Report(BaseModel):
    title: str = Field(description="Report title")
    summary: str = Field(description="Executive summary")
    sections: list[str] = Field(description="Report sections with content")
    follow_up_questions: list[str] = Field(description="Suggested follow-up questions")

class VerificationResult(BaseModel):
    is_accurate: bool = Field(description="Whether the report is accurate")
    issues: list[str] = Field(description="Any identified issues or concerns")
    suggestions: list[str] = Field(description="Suggestions for improvement")

# Create specialized agents
planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        "You are a research planner. Given a financial research question, "
        "produce a set of search queries to gather the necessary information."
    ),
    output_type=SearchPlan,
)

search_agent = Agent(
    name="SearchAgent",
    instructions=(
        "You simulate searching for information based on a query. "
        "Provide realistic results that would be found online."
    ),
)

financials_agent = Agent(
    name="FinancialsAgent",
    instructions=(
        "You analyze financial data and produce insights about a company "
        "or financial situation."
    ),
    output_type=AnalysisSummary,
)

risk_agent = Agent(
    name="RiskAgent",
    instructions=(
        "You analyze potential risks and downsides related to financial "
        "situations or investments."
    ),
    output_type=AnalysisSummary,
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You create comprehensive financial reports based on research results. "
        "Include a title, summary, detailed sections, and follow-up questions."
    ),
    output_type=Report,
)

verifier_agent = Agent(
    name="VerifierAgent",
    instructions=(
        "You review financial reports for accuracy, consistency, and completeness. "
        "Identify any issues and suggest improvements."
    ),
    output_type=VerificationResult,
)

# Helper function to extract summary
async def summary_extractor(run_result):
    return str(run_result.final_output.summary)

# Main research workflow
async def run_financial_research(query: str):
    trace_id = gen_trace_id()

    with trace("Financial Research Workflow", trace_id=trace_id):
        print(f"Trace ID: {trace_id}")
        print(f"Query: {query}")

        # 1. Plan searches
        with custom_span("Planning"):
            print("Planning searches...")
            plan_result = await Runner.run(planner_agent, query)
            search_plan = plan_result.final_output_as(SearchPlan)
            print(f"Created plan with {len(search_plan.searches)} searches")

        # 2. Perform searches
        with custom_span("Searching"):
            search_results = []
            print("Searching...")
            search_tasks = [
                Runner.run(
                    search_agent,
                    f"Search term: {item.query}\nReason: {item.reason}"
                )
                for item in search_plan.searches
            ]

            search_responses = await asyncio.gather(*search_tasks)
            search_results = [r.final_output for r in search_responses]
            print(f"Completed {len(search_results)} searches")

        # 3. Create report with analyst tools
        with custom_span("Report Writing"):
            print("Writing report...")

            # Create tools from specialist agents
            fundamentals_tool = financials_agent.as_tool(
                tool_name="analyze_financials",
                tool_description="Analyze financial metrics and performance",
                custom_output_extractor=summary_extractor,
            )

            risk_tool = risk_agent.as_tool(
                tool_name="analyze_risks",
                tool_description="Analyze potential risks and concerns",
                custom_output_extractor=summary_extractor,
            )

            # Add tools to writer agent
            writer_with_tools = writer_agent.clone(
                tools=[fundamentals_tool, risk_tool]
            )

            # Create input data
            input_data = f"Original query: {query}\nSearch results: {search_results}"

            # Generate report
            report_result = await Runner.run(writer_with_tools, input_data)
            report = report_result.final_output_as(Report)

            print(f"Report generated: {report.title}")

        # 4. Verify report
        with custom_span("Verification"):
            print("Verifying report...")

            # Convert report to markdown for verification
            report_markdown = f"""# {report.title}

## Executive Summary
{report.summary}

## Content
{''.join(f'### Section {i+1}\n{section}\n\n' for i, section in enumerate(report.sections))}
            """

            verification_result = await Runner.run(verifier_agent, report_markdown)
            verification = verification_result.final_output_as(VerificationResult)

            if verification.is_accurate:
                print("Report verified successfully")
            else:
                print(f"Report has {len(verification.issues)} issues")

        # Return the complete results
        return {
            "report": report,
            "verification": verification,
            "trace_id": trace_id
        }

# Run the workflow
async def main():
    results = await run_financial_research(
        "Analyze Tesla's financial performance over the past year and future prospects"
    )

    # Print the report
    report = results["report"]
    print("\n=== FINAL REPORT ===\n")
    print(f"# {report.title}")
    print(f"\n## Summary\n{report.summary}")

    for i, section in enumerate(report.sections):
        print(f"\n## Section {i+1}\n{section}")

    print("\n## Follow-up Questions")
    for q in report.follow_up_questions:
        print(f"- {q}")

    # Print verification
    verification = results["verification"]
    print("\n=== VERIFICATION RESULTS ===\n")
    print(f"Accurate: {verification.is_accurate}")

    if verification.issues:
        print("\nIssues:")
        for issue in verification.issues:
            print(f"- {issue}")

    if verification.suggestions:
        print("\nSuggestions:")
        for suggestion in verification.suggestions:
            print(f"- {suggestion}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Conclusion

The OpenAI Agents SDK provides a powerful framework for building advanced agent systems. By combining agents with different specializations, using tools, implementing handoffs, and applying guardrails, you can create sophisticated AI systems that can tackle complex tasks.

Key takeaways:

1. **Modular Design**: Break down complex tasks into specialized agents
2. **Tool Integration**: Extend agent capabilities with custom tools
3. **Handoffs**: Enable collaboration between specialized agents
4. **Guardrails**: Ensure safety and quality of agent inputs and outputs
5. **Tracing**: Debug and optimize agent workflows
6. **Advanced Patterns**: Implement patterns like deterministic flows, parallelization, and LLM judging

This tutorial has covered the fundamentals and advanced aspects of the OpenAI Agents SDK. For more details, explore the examples in the repository and the official documentation.

Happy agent building!

I'll look up how to force tool calling in the OpenAI Agents SDK project.

Let's check the example specifically about forcing tool use:

Now, let's check the ModelSettings class to understand how to configure tool_choice:

Based on the code I've examined, here's how to force tool calling in the OpenAI Agents SDK:

# Forcing Tool Calling in OpenAI Agents SDK

The OpenAI Agents SDK provides a straightforward way to force agents to use tools. This can be useful in scenarios where you want to ensure that the agent leverages specific tools rather than generating a direct response.

## Method 1: Setting tool_choice in ModelSettings

The main approach to force tool calling is to set the `tool_choice` parameter in the `ModelSettings` to `"required"`. This tells the language model that it must use a tool rather than generating a direct response.

```python
from agents import Agent, ModelSettings, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In a real implementation, this would fetch actual weather data
    return f"The weather in {city} is sunny and 72°F."

# Create an agent that's forced to use tools
forced_tool_agent = Agent(
    name="WeatherAgent",
    instructions="You provide weather information.",
    tools=[get_weather],
    model_settings=ModelSettings(tool_choice="required")
)

# Run the agent
result = Runner.run_sync(forced_tool_agent, "What's the weather in New York?")
print(result.final_output)
```

The `tool_choice` parameter can take three values:

- `"auto"`: The default behavior, where the model decides whether to use tools
- `"required"`: Forces the model to use a tool
- `"none"`: Prevents the model from using tools

## Method 2: Controlling What Happens After Tool Use

When forcing tool usage, you need to consider what happens after the tool is called. There are three main options:

### Option 1: Default Behavior (Run LLM Again)

By default, after a tool is called, the tool result is sent back to the LLM, which generates a new response. This can lead to an infinite loop if `tool_choice` is set to `"required"` since the model would be forced to call a tool again.

```python
# NOTE: This setup could cause an infinite loop if tool_choice is "required"
agent = Agent(
    name="DefaultBehavior",
    instructions="You help with weather information.",
    tools=[get_weather],
    tool_use_behavior="run_llm_again",  # This is the default
    model_settings=ModelSettings()  # Don't set tool_choice to "required" here
)
```

### Option 2: Stop After First Tool

You can configure the agent to stop after the first tool call and use its result as the final output:

```python
agent = Agent(
    name="StopAfterFirstTool",
    instructions="You help with weather information.",
    tools=[get_weather],
    tool_use_behavior="stop_on_first_tool",  # Stop after first tool call
    model_settings=ModelSettings(tool_choice="required")  # Force tool usage
)
```

### Option 3: Custom Tool Use Behavior

For more control, you can define a custom function that decides what to do after tools are called:

```python
from agents import Agent, FunctionToolResult, ModelSettings, RunContextWrapper, ToolsToFinalOutputResult

async def custom_tool_handler(
    context: RunContextWrapper,
    tool_results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    # Process the tool results
    weather_result = tool_results[0].output

    # Return a custom final output
    return ToolsToFinalOutputResult(
        is_final_output=True,  # Stop the agent loop
        final_output=f"Weather report: {weather_result}"
    )

agent = Agent(
    name="CustomToolHandler",
    instructions="You help with weather information.",
    tools=[get_weather],
    tool_use_behavior=custom_tool_handler,  # Custom function
    model_settings=ModelSettings(tool_choice="required")  # Force tool usage
)
```

## Method 3: Selective Tool Stopping

You can also configure the agent to stop only when specific tools are called:

```python
@function_tool
def fetch_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 75°F"

@function_tool
def fetch_forecast(city: str) -> str:
    return f"Forecast for {city}: Sunny today, rain tomorrow"

agent = Agent(
    name="SelectiveToolStopping",
    instructions="You provide weather information.",
    tools=[fetch_weather, fetch_forecast],
    # Stop only when fetch_weather is called
    tool_use_behavior={"stop_at_tool_names": ["fetch_weather"]},
    model_settings=ModelSettings(tool_choice="required")
)
```

## Complete Example

Here's a complete example demonstrating forced tool calling with different behaviors:

```python
import asyncio
from typing import Literal

from agents import Agent, FunctionToolResult, ModelSettings, RunContextWrapper, Runner, ToolsToFinalOutputResult, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"The weather in {city} is currently sunny and 72°F."

@function_tool
def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city."""
    forecast = [
        "Sunny and 75°F",
        "Partly cloudy and 70°F",
        "Rainy and 65°F",
        "Cloudy and 68°F",
        "Sunny and 73°F"
    ]
    return f"Forecast for {city} (next {days} days): " + ", ".join(forecast[:days])

async def custom_tool_handler(
    context: RunContextWrapper,
    results: list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    # Format the output based on which tool was called
    tool_name = results[0].name
    tool_output = results[0].output

    if tool_name == "get_weather":
        final_output = f"CURRENT WEATHER REPORT: {tool_output}"
    elif tool_name == "get_forecast":
        final_output = f"FORECAST REPORT: {tool_output}"
    else:
        final_output = f"TOOL RESULT: {tool_output}"

    return ToolsToFinalOutputResult(
        is_final_output=True,
        final_output=final_output
    )

async def main():
    # Create agents with different tool use behaviors

    # 1. Default behavior (don't force tool use)
    default_agent = Agent(
        name="DefaultAgent",
        instructions="You are a helpful weather assistant.",
        tools=[get_weather, get_forecast]
    )

    # 2. Force tool use, stop after first tool
    forced_agent = Agent(
        name="ForcedAgent",
        instructions="You are a helpful weather assistant.",
        tools=[get_weather, get_forecast],
        tool_use_behavior="stop_on_first_tool",
        model_settings=ModelSettings(tool_choice="required")
    )

    # 3. Force tool use, custom handling
    custom_agent = Agent(
        name="CustomAgent",
        instructions="You are a helpful weather assistant.",
        tools=[get_weather, get_forecast],
        tool_use_behavior=custom_tool_handler,
        model_settings=ModelSettings(tool_choice="required")
    )

    # 4. Selective tool stopping
    selective_agent = Agent(
        name="SelectiveAgent",
        instructions="You are a helpful weather assistant.",
        tools=[get_weather, get_forecast],
        tool_use_behavior={"stop_at_tool_names": ["get_weather"]},
        model_settings=ModelSettings(tool_choice="required")
    )

    # Test with a query
    query = "What's the weather in Seattle?"

    print("=== DEFAULT AGENT (NO FORCED TOOL USAGE) ===")
    default_result = await Runner.run(default_agent, query)
    print(default_result.final_output)
    print()

    print("=== FORCED AGENT (STOP AFTER FIRST TOOL) ===")
    forced_result = await Runner.run(forced_agent, query)
    print(forced_result.final_output)
    print()

    print("=== CUSTOM AGENT (CUSTOM TOOL HANDLER) ===")
    custom_result = await Runner.run(custom_agent, query)
    print(custom_result.final_output)
    print()

    print("=== SELECTIVE AGENT (STOP ON get_weather ONLY) ===")
    selective_result = await Runner.run(selective_agent, query)
    print(selective_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Important Considerations

1. **Avoiding Infinite Loops**: If you set `tool_choice="required"` and `tool_use_behavior="run_llm_again"` (the default), you'll create an infinite loop. Always set an appropriate tool use behavior when forcing tool use.

2. **Reset Tool Choice**: The `reset_tool_choice` parameter (default: `True`) controls whether the agent resets the tool choice after a tool call. This can help prevent infinite loops:

   ```python
   agent = Agent(
       name="ResetToolChoiceAgent",
       instructions="You help with weather information.",
       tools=[get_weather],
       reset_tool_choice=True,  # Default behavior
       model_settings=ModelSettings(tool_choice="required")
   )
   ```

3. **Parallel Tool Calls**: For more efficient processing, you can enable parallel tool calls:

   ```python
   agent = Agent(
       name="ParallelToolAgent",
       instructions="You help with weather information.",
       tools=[get_weather, get_forecast],
       model_settings=ModelSettings(
           tool_choice="required",
           parallel_tool_calls=True
       )
   )
   ```

By using these approaches, you can effectively control when and how your agents use tools, creating more predictable and capable agent behaviors.
