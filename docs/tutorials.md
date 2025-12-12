# 🎯 Tutorials

Welcome to the AI Project Synthesizer tutorials! This guide provides step-by-step tutorials to help you master the platform.

## Table of Contents

- [Getting Started Tutorials](#getting-started-tutorials)
- [Agent Development](#agent-development)
- [LLM Integration](#llm-integration)
- [Voice Features](#voice-features)
- [Advanced Topics](#advanced-topics)

---

## 🚀 Getting Started Tutorials

### Tutorial 1: Your First AI Agent

Learn how to create and run your first AI agent.

```python
# tutorial_1_first_agent.py
import asyncio
from src.agents import CodeAgent
from src.llm import LiteLLMRouter

async def main():
    # 1. Initialize the LLM router
    router = LiteLLMRouter()
    await router.initialize()
    
    # 2. Create a code agent
    agent = CodeAgent(llm_router=router)
    
    # 3. Generate code
    prompt = "Create a Python function to calculate the factorial of a number"
    result = await agent.generate_code(prompt)
    
    print("Generated code:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

**Expected Output:**
```python
def factorial(n):
    """Calculate the factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
```

### Tutorial 2: Voice-Enabled Assistant

Create a voice assistant that can speak and listen.

```python
# tutorial_2_voice_assistant.py
import asyncio
from src.voice import VoiceManager
from src.llm import LiteLLMRouter

async def main():
    # Initialize components
    router = LiteLLMRouter()
    await router.initialize()
    
    voice = VoiceManager()
    
    # Greet the user
    await voice.speak("Hello! I'm your AI assistant. How can I help you today?")
    
    # Listen for user input
    user_input = await voice.listen(duration=5.0)
    print(f"You said: {user_input}")
    
    # Generate response
    response = await router.chat_completion([
        {"role": "user", "content": user_input}
    ])
    
    # Speak the response
    await voice.speak(response["content"])

if __name__ == "__main__":
    asyncio.run(main())
```

### Tutorial 3: Web Scraping with AI

Scrape websites and extract meaningful information.

```python
# tutorial_3_web_scraping.py
import asyncio
from src.discovery import FirecrawlEnhanced
from src.analysis import ContentExtractor

async def main():
    # Initialize scraper
    scraper = FirecrawlEnhanced(api_key="your_api_key")
    
    # Scrape a website
    url = "https://example.com/article"
    content = await scraper.scrape_url(url)
    
    print(f"Title: {content.title}")
    print(f"Content length: {len(content.content)} characters")
    
    # Extract key information
    extractor = ContentExtractor()
    summary = await extractor.summarize(content.content)
    keywords = await extractor.extract_keywords(content.content)
    
    print("\nSummary:")
    print(summary)
    
    print("\nKeywords:")
    print(", ".join(keywords))

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🤖 Agent Development

### Tutorial 4: Building a Custom Agent

Create your own specialized agent.

```python
# tutorial_4_custom_agent.py
from src.agents.base import BaseAgent
from src.llm import LiteLLMRouter
from src.memory import MemoryManager

class MathTutorAgent(BaseAgent):
    """Specialized agent for math tutoring."""
    
    async def solve_problem(self, problem: str) -> str:
        """Solve a math problem step by step."""
        prompt = f"""
        As a math tutor, solve this problem step by step:
        {problem}
        
        Provide:
        1. The approach
        2. Step-by-step solution
        3. Final answer
        4. Verification
        """
        
        response = await self.llm_router.chat_completion([
            {"role": "system", "content": "You are an expert math tutor."},
            {"role": "user", "content": prompt}
        ])
        
        return response["content"]
    
    async def check_answer(self, problem: str, answer: str) -> bool:
        """Check if the answer is correct."""
        prompt = f"""
        Check if this answer is correct for the math problem:
        
        Problem: {problem}
        Answer: {answer}
        
        Respond with only 'True' or 'False'.
        """
        
        response = await self.llm_router.chat_completion([
            {"role": "user", "content": prompt}
        ])
        
        return response["content"].strip().lower() == "true"

# Usage example
async def main():
    agent = MathTutorAgent(
        llm_router=LiteLLMRouter(),
        memory=MemoryManager()
    )
    
    problem = "What is the integral of x^2 from 0 to 3?"
    solution = await agent.solve_problem(problem)
    print(solution)
    
    # Check an answer
    is_correct = await agent.check_answer(problem, "9")
    print(f"Answer is correct: {is_correct}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Tutorial 5: Multi-Agent Collaboration

Coordinate multiple agents to solve complex tasks.

```python
# tutorial_5_multi_agent.py
import asyncio
from src.agents import ResearchAgent, CodeAgent, SynthesisAgent
from src.agents.crewai_integration import CrewAIOrchestrator

async def main():
    # Create specialized agents
    researcher = ResearchAgent()
    coder = CodeAgent()
    synthesizer = SynthesisAgent()
    
    # Set up orchestrator
    orchestrator = CrewAIOrchestrator()
    orchestrator.add_agent(researcher, role="researcher")
    orchestrator.add_agent(coder, role="developer")
    orchestrator.add_agent(synthesizer, role="synthesizer")
    
    # Define a complex task
    task = """
    Create a Python script that:
    1. Fetches weather data from a public API
    2. Analyzes the data for trends
    3. Generates a visualization
    4. Emails a daily report
    """
    
    # Execute the task
    result = await orchestrator.execute_task(task)
    
    print("Final Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧠 LLM Integration

### Tutorial 6: Multi-Provider Setup

Configure and use multiple LLM providers with fallback.

```python
# tutorial_6_multi_provider.py
from src.llm import LiteLLMRouter, OpenAIProvider, AnthropicProvider

async def main():
    # Configure providers
    providers = [
        OpenAIProvider(api_key="your_openai_key"),
        AnthropicProvider(api_key="your_anthropic_key"),
    ]
    
    # Create router with fallback strategy
    router = LiteLLMRouter(
        providers=providers,
        fallback_strategy="sequential"
    )
    
    await router.initialize()
    
    # Test with different models
    prompts = [
        "Explain quantum computing in simple terms",
        "Write a Python function to sort a list",
        "Create a haiku about programming"
    ]
    
    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        response = await router.chat_completion([
            {"role": "user", "content": prompt}
        ])
        print(f"Response: {response['content'][:100]}...")
        print(f"Provider: {response['provider']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Tutorial 7: Smart Caching

Implement intelligent caching for LLM responses.

```python
# tutorial_7_smart_caching.py
from src.llm import LiteLLMRouter
from src.core.cache import SmartCache
import hashlib

async def main():
    # Initialize cache
    cache = SmartCache(
        max_size=1000,
        ttl=3600,  # 1 hour
        similarity_threshold=0.9
    )
    
    # Initialize router with cache
    router = LiteLLMRouter(cache=cache)
    await router.initialize()
    
    # Test caching
    similar_prompts = [
        "What is machine learning?",
        "Explain machine learning",
        "Define machine learning"
    ]
    
    for i, prompt in enumerate(similar_prompts):
        print(f"\nPrompt {i+1}: {prompt}")
        
        # Check cache first
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        cached = await cache.get(cache_key)
        
        if cached:
            print("✓ Retrieved from cache")
            print(f"Response: {cached['content'][:100]}...")
        else:
            print("✗ Not in cache, generating...")
            response = await router.chat_completion([
                {"role": "user", "content": prompt}
            ])
            
            # Store in cache
            await cache.set(cache_key, response)
            print(f"Response: {response['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎤 Voice Features

### Tutorial 8: Custom Voice Profiles

Create and use custom voice profiles.

```python
# tutorial_8_custom_voice.py
from src.voice import VoiceManager
from src.voice.elevenlabs_client import ElevenLabsClient

async def main():
    # Initialize voice client
    client = ElevenLabsClient(api_key="your_api_key")
    
    # Clone a voice
    with open("voice_sample.mp3", "rb") as f:
        voice_data = f.read()
    
    custom_voice = await client.clone_voice(
        name="My Custom Voice",
        audio_file=voice_data
    )
    
    print(f"Created voice: {custom_voice.voice_id}")
    
    # Use the custom voice
    voice_manager = VoiceManager(client)
    
    await voice_manager.speak(
        "Hello! This is my custom voice speaking.",
        voice_id=custom_voice.voice_id
    )
    
    # Test different emotions
    emotions = ["happy", "sad", "excited", "calm"]
    for emotion in emotions:
        await voice_manager.speak(
            f"I'm feeling {emotion} right now!",
            voice_id=custom_voice.voice_id,
            emotion=emotion
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Tutorial 9: Real-time Conversation

Build a real-time voice conversation system.

```python
# tutorial_9_realtime_conversation.py
import asyncio
from src.voice import RealtimeConversation
from src.llm import LiteLLMRouter

async def main():
    # Initialize components
    router = LiteLLMRouter()
    await router.initialize()
    
    conversation = RealtimeConversation(
        llm_router=router,
        voice_id="rachel"
    )
    
    print("Starting real-time conversation...")
    print("Say 'goodbye' to end the conversation.")
    
    # Start conversation loop
    async for transcript, response in conversation.start():
        print(f"\nYou: {transcript}")
        print(f"AI: {response}")
        
        if "goodbye" in transcript.lower():
            print("\nEnding conversation...")
            break

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔧 Advanced Topics

### Tutorial 10: Workflow Automation

Automate complex workflows with N8N integration.

```python
# tutorial_10_workflow_automation.py
from src.automation import N8NWorkflow, WorkflowBuilder

async def main():
    # Create a workflow builder
    builder = WorkflowBuilder()
    
    # Define workflow steps
    workflow = (
        builder
        .trigger("webhook", path="/process-data")
        .step("validate_data", validator="json_schema")
        .step("ai_analysis", agent="research_agent")
        .step("generate_report", template="html")
        .step("send_email", smtp_config="default")
        .step("store_result", database="postgres")
        .build()
    )
    
    # Deploy workflow
    n8n = N8NWorkflow(api_key="your_n8n_key")
    workflow_id = await n8n.deploy(workflow)
    
    print(f"Workflow deployed with ID: {workflow_id}")
    
    # Test workflow
    test_data = {
        "title": "Market Analysis",
        "data": [1, 2, 3, 4, 5]
    }
    
    result = await n8n.trigger(workflow_id, test_data)
    print(f"Workflow result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Tutorial 11: Memory Management

Implement advanced memory management with semantic search.

```python
# tutorial_11_memory_management.py
from src.memory import MemoryManager, MemoryType
from src.llm import LiteLLMRouter

async def main():
    # Initialize memory manager
    memory = MemoryManager()
    
    # Store different types of memories
    await memory.store(
        content="The user prefers Python over JavaScript",
        memory_type=MemoryType.PREFERENCE,
        tags=["programming", "python", "preference"]
    )
    
    await memory.store(
        content="Project deadline is December 31, 2024",
        memory_type=MemoryType.FACT,
        tags=["deadline", "project", "2024"]
    )
    
    await memory.store(
        content="User is working on a machine learning project",
        memory_type=MemoryType.CONTEXT,
        tags=["ml", "project", "current"]
    )
    
    # Search memories
    print("Searching for 'Python':")
    results = await memory.search("Python", limit=5)
    
    for result in results:
        print(f"- {result.content} (Score: {result.score:.2f})")
    
    # Get contextual memories for a task
    print("\nContext for 'coding task':")
    context = await memory.get_context("coding task")
    
    for memory in context:
        print(f"- {memory.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Tutorial 12: Performance Optimization

Optimize your AI applications for better performance.

```python
# tutorial_12_performance.py
import asyncio
import time
from src.llm import LiteLLMRouter
from src.core.performance import (
    BatchProcessor,
    ConnectionPool,
    RequestCache
)

async def main():
    # Initialize performance components
    router = LiteLLMRouter()
    await router.initialize()
    
    batch_processor = BatchProcessor(
        batch_size=10,
        max_wait_time=0.5
    )
    
    # Test batch processing
    prompts = [f"Explain concept {i}" for i in range(20)]
    
    print("Processing requests individually...")
    start = time.time()
    
    for prompt in prompts:
        await router.chat_completion([{"role": "user", "content": prompt}])
    
    individual_time = time.time() - start
    print(f"Individual processing: {individual_time:.2f}s")
    
    print("\nProcessing requests in batches...")
    start = time.time()
    
    # Batch process
    async for response in batch_processor.process(
        prompts,
        processor=lambda p: router.chat_completion([{"role": "user", "content": p}])
    ):
        pass
    
    batch_time = time.time() - start
    print(f"Batch processing: {batch_time:.2f}s")
    print(f"Speedup: {individual_time / batch_time:.2f}x")
    
    # Test connection pooling
    print("\nTesting connection pooling...")
    pool = ConnectionPool(max_connections=5)
    
    async with pool.get_connection() as conn:
        result = await conn.chat_completion([
            {"role": "user", "content": "Test message"}
        ])
        print(f"Pooled response: {result['content'][:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 Project-Based Tutorials

### Tutorial 13: Build an AI Code Reviewer

Create a comprehensive code review system.

```python
# tutorial_13_code_reviewer.py
from src.agents import CodeAgent
from src.analysis import QualityScorer, SecurityScanner
from src.llm import LiteLLMRouter

class AICodeReviewer:
    def __init__(self):
        self.router = LiteLLMRouter()
        self.agent = CodeAgent(llm_router=self.router)
        self.scorer = QualityScorer()
        self.scanner = SecurityScanner()
    
    async def review_code(self, code: str, language: str = "python") -> dict:
        """Perform comprehensive code review."""
        
        # 1. Basic code analysis
        quality_score = self.scorer.analyze(code)
        security_issues = await self.scanner.scan(code)
        
        # 2. AI-powered review
        review_prompt = f"""
        Review this {language} code for:
        1. Code quality and best practices
        2. Performance optimizations
        3. Potential bugs
        4. Documentation improvements
        
        Code:
        {code}
        """
        
        ai_review = await self.agent.review_code(code)
        
        # 3. Compile comprehensive report
        report = {
            "quality_score": quality_score.score,
            "security_issues": security_issues,
            "ai_review": ai_review,
            "recommendations": []
        }
        
        # Add recommendations based on analysis
        if quality_score.complexity > 10:
            report["recommendations"].append(
                "Consider reducing code complexity"
            )
        
        if security_issues:
            report["recommendations"].append(
                f"Address {len(security_issues)} security issue(s)"
            )
        
        return report

# Usage example
async def main():
    reviewer = AICodeReviewer()
    
    code_sample = """
    def process_data(data):
        result = []
        for i in range(len(data)):
            if data[i] % 2 == 0:
                result.append(data[i] * 2)
        return result
    """
    
    report = await reviewer.review_code(code_sample)
    
    print("Code Review Report:")
    print(f"Quality Score: {report['quality_score']}/100")
    print(f"Security Issues: {len(report['security_issues'])}")
    print("\nAI Review:")
    print(report['ai_review'])
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"- {rec}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔍 Troubleshooting Common Issues

### Issue 1: API Rate Limits

```python
# Handle rate limits gracefully
from src.core.rate_limiter import RateLimiter

async def safe_api_call():
    limiter = RateLimiter(requests_per_second=10)
    
    while True:
        try:
            await limiter.acquire()
            response = await api_call()
            return response
        except RateLimitError:
            print("Rate limit hit, waiting...")
            await asyncio.sleep(1)
```

### Issue 2: Memory Leaks

```python
# Monitor and manage memory usage
import psutil
import gc

async def monitor_memory():
    process = psutil.Process()
    
    while True:
        mem_info = process.memory_info()
        print(f"Memory usage: {mem_info.rss / 1024 / 1024:.2f} MB")
        
        if mem_info.rss > 1024 * 1024 * 1024:  # 1GB
            print("Memory usage high, running garbage collection...")
            gc.collect()
        
        await asyncio.sleep(10)
```

---

## 🎓 Best Practices

1. **Always handle errors gracefully** with try-catch blocks
2. **Use caching** to reduce API costs and improve performance
3. **Monitor resource usage** to prevent memory leaks
4. **Implement rate limiting** to avoid API restrictions
5. **Log everything** for debugging and monitoring
6. **Test with smaller inputs** before scaling up
7. **Use environment variables** for sensitive data
8. **Implement retries** for network operations

---

## 📖 Next Steps

After completing these tutorials, you'll be ready to:

1. Build custom AI agents for specific tasks
2. Integrate multiple AI providers effectively
3. Create voice-enabled applications
4. Automate complex workflows
5. Optimize performance for production

Check out our [examples](../examples/) folder for more complete projects, and visit our [community forum](https://forum.ai-synthesizer.dev) to share your creations!
