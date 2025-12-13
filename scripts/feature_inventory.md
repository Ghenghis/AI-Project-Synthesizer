# AI Project Synthesizer - Feature Inventory
**Scan Date:** 2025-12-12T23:27:03.794631
**Total Files:** 141
**Total Classes:** 461
**Total Functions:** 1888
**Total Enums:** 0
**Total Dataclasses:** 170

## Module Categories
### Cli.Py
- Files: 1
- Classes: 0
- Functions: 23

### __Init__.Py
- Files: 1
- Classes: 0
- Functions: 0

### Agents
- Files: 12
- Classes: 37
- Functions: 172

### Analysis
- Files: 6
- Classes: 17
- Functions: 64

### Assistant
- Files: 3
- Classes: 10
- Functions: 42

### Automation
- Files: 6
- Classes: 19
- Functions: 97

### Cli_Executor
- Files: 4
- Classes: 11
- Functions: 77

### Core
- Files: 22
- Classes: 110
- Functions: 391

### Dashboard
- Files: 6
- Classes: 15
- Functions: 83

### Discovery
- Files: 10
- Classes: 49
- Functions: 189

### Generation
- Files: 3
- Classes: 4
- Functions: 29

### Llm
- Files: 11
- Classes: 32
- Functions: 89

### Mcp
- Files: 1
- Classes: 4
- Functions: 18

### Mcp_Server
- Files: 3
- Classes: 0
- Functions: 35

### Memory
- Files: 2
- Classes: 5
- Functions: 42

### Platform
- Files: 2
- Classes: 7
- Functions: 31

### Plugins
- Files: 2
- Classes: 1
- Functions: 5

### Quality
- Files: 7
- Classes: 28
- Functions: 90

### Recipes
- Files: 3
- Classes: 6
- Functions: 9

### Resolution
- Files: 4
- Classes: 8
- Functions: 28

### Synthesis
- Files: 4
- Classes: 12
- Functions: 42

### Tui
- Files: 3
- Classes: 2
- Functions: 28

### Utils
- Files: 2
- Classes: 4
- Functions: 18

### Vibe
- Files: 11
- Classes: 48
- Functions: 162

### Voice
- Files: 8
- Classes: 18
- Functions: 84

### Workflows
- Files: 4
- Classes: 14
- Functions: 40

## Detailed Module List
### cli
AI Project Synthesizer - Command Line Interface

Complete CLI for repository search, analysis, synthesis, and documentation generation.
Entry point for the 'ai-synthesizer' and 'synth' commands.

Usage:
    ai-synthesizer search "machine learning transformers"
    ai-synthesizer analyze https://github.com/user/repo
    ai-synthesizer synthesize --repos repo1,repo2 --output ./project
    ai-synthesizer resolve --repos repo1,repo2
    ai-synthesizer docs ./my-project

**Functions:**
- `print_banner`: Print the application banner
- `run_async`: Run an async coroutine in the event loop
- `search_repositories`: Search for repositories across multiple platforms
- `_search`
- `analyze_repository`: Perform deep analysis of a repository
- `_analyze`
- `synthesize_project`: Synthesize a unified project from multiple repositories
- `_synthesize`
- `resolve_dependencies`: Resolve and merge dependencies from multiple repositories
- `_resolve`
- `generate_documentation`: Generate comprehensive documentation for a project
- `_generate`
- `show_config`: Show current configuration settings
- `show_version`: Show version information
- `show_info`: Show detailed information about the tool
- `run_gap_check`: Run gap analysis and auto-repair
- `analyze`
- `start_tui`: Start the Terminal UI for interactive control
- `manage_settings`: Manage system settings from the command line
- `start_mcp_server`: Start the MCP server for Windsurf IDE integration
- `wizard_command`: Interactive project creation wizard
- `recipe_command`: Manage and run synthesis recipes
- `main`: Main entry point for the CLI application

### __init__
AI Project Synthesizer

Intelligent multi-repository code synthesis platform for Windsurf IDE.

This package provides:
- Multi-platform repository discovery
- Code analysis and dependency resolution
- Intelligent code synthesis
- Automated documentation generation

Example:
    from src.mcp_server.server import main
    import asyncio
    asyncio.run(main())


### agents.autogen_integration
VIBE MCP - AutoGen Integration

Multi-agent conversation system for complex code review and analysis.
Implements Phase 3.1 of the VIBE MCP roadmap.

Features:
- Two-agent conversation for code review
- Integration with VoiceManager for spoken feedback
- Quality validation and security checking
- Extensible framework for additional agents

**Classes:**
- `CodeReviewResult`: Result of a multi-agent code review
- `AutoGenIntegration`: AutoGen integration for multi-agent code review
**Functions:**
- `__init__`: Initialize AutoGen integration
- `_get_llm_config`: Get LLM configuration from environment or LiteLLM router
- `_initialize_agents`: Initialize the core agents for code review
- `review_code`: Perform multi-agent code review
- `_create_review_prompt`: Create a comprehensive review prompt for the agents
- `_parse_conversation_result`: Parse the conversation history to extract review results
- `_speak_if_enabled`: Speak a message if voice output is enabled
- `_announce_results`: Announce review results using voice
- `simple_conversation_test`: Test basic two-agent conversation
- `create_autogen_integration`: Create and initialize AutoGen integration
- `main`: Test the AutoGen integration

### agents.automation_agent
AI Project Synthesizer - Automation Agent

AI-powered automation agent for:
- Workflow orchestration
- Task scheduling
- Auto-recovery
- Health monitoring
- Continuous operation

**Classes:**
- `AutomationAgent`: Automation agent for workflow management
**Functions:**
- `__init__`
- `_setup_tools`: Set up automation tools
- `_run_workflow`: Execute an n8n workflow
- `_schedule_task`: Schedule a task
- `_check_health`: Check system health
- `_recover_component`: Attempt to recover a component
- `_run_tests`: Run integration tests
- `_get_metrics`: Get system metrics
- `_execute_step`: Execute an automation step
- `_should_continue`: Check if should continue automation
- `monitor_health`: Continuously monitor system health
- `automate`: Run automation task

### agents.base
AI Project Synthesizer - Base Agent

Foundation for all AI agents with:
- LLM integration
- Tool execution
- Memory management
- Auto-continue support

**Classes:**
- `AgentStatus`: Agent execution status
- `AgentConfig`: Agent configuration
- `AgentResult`: Result from agent execution
- `AgentTool`: Tool that an agent can use
- `BaseAgent`: Base class for all AI agents
**Functions:**
- `to_dict`
- `__init__`
- `execute`: Execute the tool
- `to_schema`: Get tool schema for LLM
- `__init__`
- `_get_llm`: Get LLM client
- `register_tool`: Register a tool for the agent
- `add_memory`: Add to agent memory
- `clear_memory`: Clear agent memory
- `_execute_step`: Execute a single step
- `_should_continue`: Determine if agent should continue
- `run`: Run the agent on a task
- `cancel`: Cancel agent execution
- `get_status`: Get agent status

### agents.code_agent
AI Project Synthesizer - Code Agent

AI-powered code agent for:
- Code generation
- Bug fixing
- Code review
- Refactoring
- Documentation

**Classes:**
- `CodeAgent`: Code agent for code-related tasks
**Functions:**
- `__init__`
- `_setup_tools`: Set up code tools
- `_generate_code`: Generate code from description
- `_fix_code`: Fix bugs in code
- `_review_code`: Review code for quality issues
- `_refactor_code`: Refactor code
- `_generate_docs`: Generate documentation
- `_explain_code`: Explain what code does
- `_execute_step`: Execute a code task step
- `_should_continue`: Check if should continue
- `generate`: Generate code from description
- `fix`: Fix code with error

### agents.crewai_integration
VIBE MCP - CrewAI Integration

Role-based team collaboration system for complex multi-agent tasks.
Implements Phase 3.4 of the VIBE MCP roadmap.

Features:
- Role-based agent teams with specific expertise
- Hierarchical task delegation
- Collaborative problem solving
- Tool sharing between agents
- Integration with VoiceManager for team updates

**Classes:**
- `Agent`
- `Task`
- `Crew`
- `Process`
- `TeamRole`: predefined roles for agents in teams
- `TeamTask`: A task assigned to a CrewAI team
- `TeamResult`: Result from a CrewAI team execution
- `CrewAIIntegration`: CrewAI integration for role-based team collaboration
**Functions:**
- `__init__`
- `__init__`
- `__init__`
- `__init__`: Initialize CrewAI integration
- `_get_llm_config`: Get LLM configuration from environment or LiteLLM router
- `_create_agents`: Create specialized agents for different roles
- `_create_default_crews`: Create predefined teams for common scenarios
- `execute_team_task`: Execute a task using a specialized team
- `_extract_agent_results`: Extract individual agent results from crew execution
- `_calculate_quality_score`: Calculate a quality score for the team's work
- `create_feature`: Create a new feature using the development team
- `audit_security`: Perform a security audit using the security team
- `generate_documentation`: Generate documentation using the documentation team
- `get_team_list`: Get list of available teams with their capabilities
- `get_task_history`: Get history of all team task executions
- `_speak_if_enabled`: Speak a message if voice output is enabled
- `_announce_team_result`: Announce team completion results
- `get_statistics`: Get team execution statistics
- `create_crewai_integration`: Create and initialize CrewAI integration
- `main`: Test the CrewAI integration

### agents.framework_router
VIBE MCP - Framework Router

Unified interface for all agent frameworks with dynamic selection.
Implements Phase 3.5 of the VIBE MCP roadmap.

Features:
- Consistent interface across AutoGen, Swarm, LangGraph, and CrewAI
- Dynamic framework selection based on task characteristics
- Automatic fallback handling
- Framework-agnostic task execution
- Performance metrics and optimization

**Classes:**
- `TaskType`: Types of tasks that can be executed
- `TaskComplexity`: Complexity levels for tasks
- `FrameworkType`: Available agent frameworks
- `TaskRequest`: A unified task request for any framework
- `AgentResult`: Unified result from any agent framework
- `FrameworkRouter`: Unified router for all agent frameworks
**Functions:**
- `__init__`: Initialize the framework router
- `_initialize_integrations`: Initialize all framework integrations
- `select_framework`: Select the best framework(s) for a task
- `_score_framework_for_task`: Score a framework's suitability for a task
- `execute_task`: Execute a task using the optimal framework
- `_execute_with_framework`: Execute a task with a specific framework
- `_execute_with_autogen`: Execute task using AutoGen
- `_execute_with_swarm`: Execute task using Swarm
- `_execute_with_langgraph`: Execute task using LangGraph
- `_execute_with_crewai`: Execute task using CrewAI
- `_update_performance_metrics`: Update performance metrics for a framework
- `get_framework_status`: Get status of all frameworks
- `get_execution_history`: Get recent execution history
- `get_optimal_framework_for_task_type`: Get the historically best framework for a task type
- `create_framework_router`: Create and initialize the framework router
- `main`: Test the framework router

### agents.langgraph_integration
VIBE MCP - LangGraph Integration

Stateful workflow system with checkpoints and persistence.
Implements Phase 3.3 of the VIBE MCP roadmap.

Features:
- Stateful workflows with memory
- Checkpointing for pause/resume capability
- Conditional branching and loops
- Human-in-the-loop support
- Integration with VoiceManager for spoken updates

**Classes:**
- `StateGraph`
- `END`
- `WorkflowStatus`: Status of a workflow execution
- `WorkflowState`: State for LangGraph workflows
- `WorkflowResult`: Result of a workflow execution
- `LangGraphIntegration`: LangGraph integration for stateful workflows
**Functions:**
- `__init__`
- `add_node`
- `add_edge`
- `add_conditional_edges`
- `set_entry_point`
- `compile`
- `__init__`: Initialize LangGraph integration
- `_initialize_checkpointing`: Initialize checkpointing system
- `_create_default_workflows`: Create default workflow templates
- `_create_code_review_workflow`: Create a stateful code review workflow
- `analyze_code`: Analyze code for quality and issues
- `security_check`: Perform security analysis
- `await_human_input`: Wait for human input on security issues
- `generate_report`: Generate final review report
- `_create_task_decomposition_workflow`: Create a workflow for decomposing complex tasks
- `analyze_task`: Analyze the task complexity and requirements
- `decompose_steps`: Decompose task into actionable steps
- `validate_steps`: Validate the decomposed steps
- `_create_documentation_workflow`: Create a workflow for generating documentation
- `extract_structure`: Extract code structure for documentation
- `generate_docs`: Generate documentation content
- `_create_debug_workflow`: Create a workflow for debugging code issues
- `reproduce_error`: Attempt to reproduce the error
- `identify_root_cause`: Identify the root cause of the error
- `propose_fix`: Propose a fix for the error
- `run_workflow`: Run a stateful workflow
- `pause_workflow`: Pause a running workflow
- `resume_workflow`: Resume a paused workflow
- `get_workflow_list`: Get list of available workflows
- `get_workflow_history`: Get history of all executed workflows
- `_speak_if_enabled`: Speak a message if voice output is enabled
- `_announce_workflow_result`: Announce workflow completion results
- `get_statistics`: Get workflow execution statistics
- `create_langgraph_integration`: Create and initialize LangGraph integration
- `main`: Test the LangGraph integration

### agents.research_agent
AI Project Synthesizer - Research Agent

AI-powered research agent for:
- Multi-platform resource discovery
- Code analysis and evaluation
- Trend identification
- Recommendation generation

**Classes:**
- `ResearchAgent`: Research agent for discovering and analyzing resources
**Functions:**
- `__init__`
- `_setup_tools`: Set up research tools
- `_search_github`: Search GitHub repositories
- `_search_huggingface`: Search HuggingFace
- `_analyze_repo`: Analyze a repository
- `_get_trends`: Get trending topics
- `_execute_step`: Execute a research step
- `_should_continue`: Check if should continue research
- `research`: Convenience method to research a topic

### agents.swarm_integration
VIBE MCP - Swarm Integration

Lightweight agent handoff system for fast routing and simple task delegation.
Implements Phase 3.2 of the VIBE MCP roadmap.

Features:
- Fast agent handoffs (<100ms)
- Simple function-based delegation
- Context variable passing
- Streaming support
- Integration with VoiceManager for spoken updates

**Classes:**
- `Swarm`
- `Agent`
- `HandoffResult`: Result of an agent handoff
- `SwarmIntegration`: Swarm integration for lightweight agent handoffs
**Functions:**
- `__init__`
- `__init__`
- `__init__`: Initialize Swarm integration
- `_initialize_swarm`: Initialize Swarm client and default agents
- `_create_default_agents`: Create default agent set for common tasks
- `_handoff_to_complex_reviewer`: Handoff to complex reviewer agent
- `_handoff_to_code_helper`: Handoff to code helper agent
- `_handoff_to_doc_generator`: Handoff to documentation generator agent
- `quick_handoff`: Perform a quick agent handoff
- `decompose_task`: Decompose a complex task into simple steps
- `generate_docs`: Generate documentation for code
- `quick_fix`: Quickly fix simple bugs in code
- `get_agent_list`: Get list of available agents with descriptions
- `_speak_if_enabled`: Speak a message if voice output is enabled
- `get_statistics`: Get usage statistics
- `create_swarm_integration`: Create and initialize Swarm integration
- `main`: Test the Swarm integration

### agents.synthesis_agent
AI Project Synthesizer - Synthesis Agent

AI-powered project synthesis agent for:
- Project planning and structure
- Code generation
- Dependency resolution
- Documentation creation

**Classes:**
- `SynthesisAgent`: Synthesis agent for assembling projects
**Functions:**
- `__init__`
- `_setup_tools`: Set up synthesis tools
- `_plan_project`: Plan project structure
- `_generate_file`: Generate a code file
- `_resolve_dependencies`: Resolve project dependencies
- `_create_readme`: Generate README
- `_assemble_project`: Assemble complete project
- `_execute_step`: Execute a synthesis step
- `_should_continue`: Check if should continue synthesis
- `synthesize`: Convenience method to synthesize a project

### agents.voice_agent
AI Project Synthesizer - Voice Agent

AI-powered voice agent for:
- Continuous voice interaction (no pause limits)
- Speech-to-text processing
- Text-to-speech responses
- Voice command execution
- Auto-continue conversations

**Classes:**
- `VoiceState`: Voice agent state
- `VoiceAgent`: Voice agent for speech interactions
**Functions:**
- `__init__`
- `_setup_tools`: Set up voice tools
- `_get_voice_manager`: Get voice manager
- `_speak`: Speak text aloud
- `_listen`: Listen for voice input (no pause limits when timeout=0)
- `_execute_command`: Execute a voice command
- `_execute_step`: Execute a voice interaction step
- `_should_continue`: Check if should continue conversation
- `on_transcription`: Set callback for transcription events
- `on_response`: Set callback for response events
- `start_listening`: Start continuous listening mode
- `stop_listening`: Stop listening mode
- `process_text`: Process text input and return response
- `speak_and_wait`: Speak text and wait for completion
- `get_state`: Get current voice state
- `get_voice_agent`: Get or create voice agent

### agents.__init__
AI Project Synthesizer - Agent System

AI/ML-powered agents for automated tasks:
- Research Agent: Discovers and analyzes resources
- Synthesis Agent: Assembles projects
- Voice Agent: Handles voice interactions
- Automation Agent: Manages workflows
- Code Agent: Generates and fixes code


### analysis.ast_parser
AI Project Synthesizer - AST Parser

Multi-language AST parsing using tree-sitter.
Extracts code structure, imports, functions, and classes.

**Classes:**
- `Import`: Represents an import statement
- `Function`: Represents a function definition
- `Class`: Represents a class definition
- `ParsedFile`: Result of parsing a single file
- `ASTParser`: Multi-language AST parser
**Functions:**
- `__init__`: Initialize the AST parser
- `_check_tree_sitter`: Check if tree-sitter is available
- `parse_file`: Parse a single source file
- `analyze_project`: Analyze entire project structure
- `_detect_language`: Detect language from file extension
- `_should_skip`: Check if file should be skipped
- `_parse_python`: Parse Python source file
- `_get_decorator_name`: Extract decorator name from AST node
- `_get_base_name`: Extract base class name from AST node
- `_parse_javascript`: Parse JavaScript/TypeScript source file
- `_parse_generic`: Generic parsing for unsupported languages

### analysis.code_extractor
AI Project Synthesizer - Code Extractor

Identifies and extracts code components from repositories.
Supports selective extraction of modules, classes, and functions.

**Classes:**
- `Component`: Represents an extractable code component
- `CodeExtractor`: Extracts code components from repositories
**Functions:**
- `to_dict`: Convert to dictionary
- `__init__`: Initialize the code extractor
- `identify_components`: Identify extractable components in a repository
- `_build_import_graph`: Build import dependency graph
- `_identify_packages`: Find Python packages (directories with __init__
- `_analyze_package`: Analyze a package and create component
- `_is_standalone_module`: Check if a module can stand alone
- `_is_significant_class`: Check if a class is significant enough to extract
- `_create_module_component`: Create component from a module
- `_create_class_component`: Create component from a class
- `_get_package_description`: Extract package description from __init__
- `_get_module_description`: Extract module description
- `_is_stdlib`: Check if module is part of Python standard library
- `_should_skip`: Check if path should be skipped

### analysis.compatibility_checker
AI Project Synthesizer - Compatibility Checker

Checks if multiple repositories can work together by analyzing
dependencies, Python versions, and system requirements.

**Classes:**
- `RepositoryInfo`: Information about a repository for compatibility checking
- `CompatibilityIssue`: Represents a compatibility issue between repositories
- `CompatibilityMatrix`: Complete compatibility analysis result
- `CompatibilityChecker`: Checks compatibility between multiple repositories
**Functions:**
- `to_dict`: Convert to dictionary for JSON serialization
- `__init__`: Initialize the compatibility checker
- `check`: Check compatibility between repositories
- `_check_python_versions`: Check Python version compatibility
- `_check_dependencies`: Check for dependency conflicts
- `_check_languages`: Check language compatibility
- `_parse_python_requirement`: Parse Python version requirement string
- `_version_less_than`: Compare version strings
- `to_tuple`
- `_versions_might_overlap`: Check if version specs might have overlapping solutions

### analysis.dependency_analyzer
AI Project Synthesizer - Dependency Analyzer

Analyzes project dependencies across package managers (pip, npm, cargo, etc.).
Builds dependency graphs and detects conflicts.

**Classes:**
- `Dependency`: Represents a single dependency
- `DependencyConflict`: Represents a conflict between dependencies
- `DependencyGraph`: Complete dependency graph for a project
- `DependencyAnalyzer`: Analyzes project dependencies across multiple package managers
**Functions:**
- `normalized_name`: Return normalized package name (lowercase, underscores to hyphens)
- `all_dependencies`: Return all dependencies
- `has_conflicts`: Check if there are any conflicts
- `to_dict`: Convert to dictionary for JSON serialization
- `__init__`: Initialize the dependency analyzer
- `analyze`: Analyze all dependencies in a repository
- `_parse_file`: Parse a dependency file and return (regular, dev) dependencies
- `_parse_requirements_txt`: Parse requirements
- `_parse_requirement_line`: Parse a single requirement line
- `_parse_pyproject_toml`: Parse pyproject
- `_poetry_dep_to_dependency`: Convert Poetry dependency spec to Dependency
- `_parse_package_json`: Parse package
- `_parse_cargo_toml`: Parse Cargo
- `_parse_pipfile`: Parse Pipfile for dependencies
- `_deduplicate`: Remove duplicate dependencies, keeping the most specific version
- `_detect_conflicts`: Detect version conflicts between dependencies
- `_versions_compatible`: Check if two version specs are potentially compatible

### analysis.quality_scorer
AI Project Synthesizer - Quality Scorer

Scores repository quality based on documentation, tests,
code organization, activity, and maintenance.

**Classes:**
- `QualityScore`: Repository quality score breakdown
- `QualityScorer`: Scores repository quality across multiple dimensions
**Functions:**
- `to_dict`: Convert to dictionary
- `grade`: Get letter grade for overall score
- `__init__`: Initialize the quality scorer
- `score`: Calculate quality score for a repository
- `_score_documentation`: Score documentation quality
- `_score_tests`: Score test coverage
- `_score_code_quality`: Score code quality indicators
- `_score_ci_cd`: Score CI/CD configuration
- `_score_maintenance`: Score maintenance based on repository metadata
- `_score_community`: Score community adoption
- `_check_docstrings`: Check docstring coverage in Python files
- `_should_skip`: Check if path should be skipped

### analysis.__init__
AI Project Synthesizer - Analysis Layer

AST parsing, dependency analysis, code extraction, and quality scoring.


### assistant.core
AI Project Synthesizer - Conversational Assistant Core

The intelligent assistant that:
1. Talks to users naturally via voice AND text (always both)
2. Asks clarifying questions to understand what users need
3. Uses the best available LLM for thinking
4. Searches across platforms to find solutions
5. Synthesizes projects and generates code
6. Voice can be toggled on/off

This is the BRAIN that makes everything useful.

**Classes:**
- `AssistantState`: Current state of the assistant
- `TaskType`: Types of tasks the assistant can help with
- `Message`: A message in the conversation
- `TaskContext`: Context for the current task
- `AssistantConfig`: Configuration for the assistant
- `ConversationalAssistant`: The main conversational AI assistant
**Functions:**
- `__init__`: Initialize the assistant
- `_init_system_prompt`: Initialize the system prompt
- `_get_llm`: Get or initialize LLM client
- `_get_voice`: Get or initialize voice client
- `_get_search`: Get or initialize search client
- `set_voice_enabled`: Toggle voice on/off
- `chat`: Process user input and generate response
- `_generate_response`: Generate response using LLM
- `_analyze_intent`: Analyze user intent to determine next action
- `_get_search_clarification`: Get clarification question for search
- `_get_build_clarification`: Get clarification question for build requests
- `_execute_action`: Execute an action based on intent
- `_do_search`: Execute a search and format results
- `_do_analyze`: Analyze a repository
- `_generate_basic_response`: Generate basic response without LLM
- `_generate_voice`: Generate voice audio for text
- `_clean_for_speech`: Clean text for speech synthesis
- `_get_task_info`: Get current task information
- `_get_suggested_actions`: Get suggested next actions
- `_notify_state_change`: Notify listeners of state change
- `on_state_change`: Register state change callback
- `on_message`: Register message callback
- `get_conversation_history`: Get conversation history
- `clear_conversation`: Clear conversation history
- `get_assistant`: Get or create the assistant singleton

### assistant.proactive_research
AI Project Synthesizer - Proactive Research Engine

When user is idle, the AI automatically:
1. Analyzes conversation context to understand user's goals
2. Searches for related projects across all platforms
3. Finds research papers on arXiv
4. Discovers complementary tools and libraries
5. Prepares recommendations for when user returns

IDLE BEHAVIOR:
- User idle > 30 seconds: Start light research
- User idle > 60 seconds: Deep research (papers, more projects)
- User idle > 120 seconds: Synthesis recommendations ready

All research happens in background - ready when user returns.

**Classes:**
- `ResearchDepth`: How deep to research
- `ResearchResult`: Results from proactive research
- `ResearchConfig`: Configuration for proactive research
- `ProactiveResearchEngine`: Automatically researches when user is idle
**Functions:**
- `summary`: Get summary of research
- `__init__`: Initialize research engine
- `set_context`: Add context from conversation
- `user_active`: Mark user as active (resets idle timer)
- `_extract_topic`: Extract main topic from context
- `start_monitoring`: Start monitoring for idle and auto-research
- `stop_monitoring`: Stop monitoring
- `_monitor_loop`: Monitor idle time and trigger research
- `_do_research`: Perform research at specified depth
- `_search_projects`: Search for projects across platforms
- `_search_papers`: Search for research papers on arXiv
- `_parse_arxiv_response`: Parse arXiv API response
- `_generate_recommendations`: Generate recommendations based on research
- `get_latest_research`: Get the most recent research results
- `get_all_research`: Get all research results
- `format_for_user`: Format research results for presenting to user
- `get_research_engine`: Get or create research engine

### assistant.__init__
AI Project Synthesizer - Conversational Assistant

The intelligent assistant that talks to users via voice + text,
asks clarifying questions, and completes tasks.


### automation.browser_client
VIBE MCP - Browser Automation Client

Browser automation client using Playwright for intelligent web interactions.
Implements Phase 5.3 of the VIBE MCP roadmap.

Features:
- Browser automation with Playwright
- Page interaction and navigation
- Form filling and submission
- Screenshot capture
- JavaScript execution
- Multi-browser support

**Classes:**
- `BrowserType`: Supported browser types
- `ViewportSize`: Common viewport sizes
- `BrowserAction`: Browser action representation
- `BrowserSession`: Browser session information
- `BrowserClient`: Browser automation client using Playwright
**Functions:**
- `__init__`: Initialize browser client
- `__aenter__`: Async context manager entry
- `__aexit__`: Async context manager exit
- `start`: Start the browser
- `stop`: Stop the browser
- `goto`: Navigate to a URL
- `reload`: Reload the current page
- `go_back`: Go back in browser history
- `go_forward`: Go forward in browser history
- `click`: Click an element
- `type_text`: Type text into an element
- `fill_form`: Fill a form with data
- `select_option`: Select an option from a dropdown
- `upload_file`: Upload a file through an input element
- `get_text`: Get text content of an element
- `get_attribute`: Get attribute value of an element
- `evaluate`: Execute JavaScript in the page
- `get_page_content`: Get page content
- `screenshot`: Take a screenshot
- `wait_for_selector`: Wait for an element to appear
- `wait_for_navigation`: Wait for navigation to complete
- `get_sessions`: Get all browser sessions
- `get_current_session`: Get current browser session
- `new_tab`: Open a new browser tab
- `get_browser_info`: Get browser information
- `test_connection`: Test browser functionality
- `create_browser_client`: Create and initialize browser client
- `main`: Test the browser client

### automation.coordinator
AI Project Synthesizer - Automation Coordinator

Central coordinator for seamless automation:
- n8n workflow management
- Event-driven actions
- Scheduled tasks
- Real-time monitoring
- Self-healing operations

**Classes:**
- `EventType`: System event types
- `SystemEvent`: A system event
- `ScheduledTask`: A scheduled task
- `AutomationConfig`: Automation configuration
- `AutomationCoordinator`: Central automation coordinator
**Functions:**
- `__init__`
- `_register_default_handlers`: Register default event handlers
- `_register_default_tasks`: Register default scheduled tasks
- `start`: Start the automation coordinator
- `stop`: Stop the automation coordinator
- `emit`: Emit a system event
- `on`: Register an event handler
- `_event_processor_loop`: Process events in background
- `_process_event`: Process a single event
- `_log_event`: Log an event
- `_handle_error`: Handle error events
- `_handle_health_check`: Handle health check events
- `schedule`: Schedule a task
- `unschedule`: Unschedule a task
- `_scheduler_loop`: Run scheduled tasks
- `_run_scheduled_task`: Run a scheduled task
- `_run_health_check`: Run system health check
- `_cleanup_metrics`: Cleanup old metrics
- `_run_integration_tests`: Run integration tests
- `_attempt_recovery`: Attempt auto-recovery from error
- `trigger_n8n_workflow`: Trigger an n8n workflow
- `setup_n8n_workflows`: Set up default n8n workflows
- `get_status`: Get coordinator status
- `get_metrics_summary`: Get metrics summary
- `run_tests`: Run tests on demand
- `get_coordinator`: Get or create automation coordinator
- `start_automation`: Start the automation system

### automation.metrics
AI Project Synthesizer - Metrics & Timing System

Precise timing metrics for:
- Action-to-action latency (ms)
- Response times
- Workflow performance
- System health metrics

**Classes:**
- `TimingRecord`: Single timing measurement
- `ActionMetrics`: Aggregated metrics for an action
- `ActionTimer`: Context manager for timing actions
- `MetricsCollector`: Collects and aggregates timing metrics
**Functions:**
- `duration_seconds`
- `avg_ms`
- `success_rate`
- `p50_ms`: 50th percentile (median)
- `p95_ms`: 95th percentile
- `p99_ms`: 99th percentile
- `to_dict`
- `__init__`
- `__aenter__`
- `__aexit__`
- `add_metadata`: Add metadata to the timing record
- `elapsed_ms`: Get elapsed time so far
- `__init__`
- `record`: Record a timing measurement
- `get_metrics`: Get metrics for a specific action
- `get_all_metrics`: Get all metrics
- `get_summary`: Get summary of all metrics
- `get_recent_records`: Get recent timing records
- `reset`: Reset all metrics
- `get_metrics_collector`: Get or create metrics collector
- `timed`: Decorator to time async functions
- `decorator`
- `wrapper`

### automation.testing
AI Project Synthesizer - Integrated Testing Framework

Automated testing for:
- Workflow validation
- API endpoint testing
- Integration tests
- Performance benchmarks
- End-to-end scenarios

**Classes:**
- `TestStatus`: Test execution status
- `TestCase`: A single test case
- `TestResult`: Result of a test execution
- `TestSuiteResult`: Result of a test suite execution
- `IntegrationTester`: Integrated testing framework
**Functions:**
- `success_rate`
- `to_dict`
- `__init__`
- `register`: Register a test case
- `register_many`: Register multiple test cases
- `run_test`: Run a single test
- `run_all`: Run all registered tests
- `run_category`: Run tests in a specific category
- `run_tags`: Run tests with specific tags
- `_run_tests`: Run a list of tests
- `test_lm_studio_connection`: Test LM Studio is running
- `test_ollama_connection`: Test Ollama is running
- `test_github_api`: Test GitHub API access
- `test_huggingface_api`: Test HuggingFace API access
- `test_elevenlabs_api`: Test ElevenLabs API access
- `test_search_workflow`: Test search workflow end-to-end
- `test_cache_operations`: Test cache operations
- `test_metrics_collection`: Test metrics collection
- `get_default_tests`: Get default test cases

### automation.__init__
AI Project Synthesizer - Automation System

Complete automation framework with:
- n8n workflow orchestration
- Timing metrics (ms between actions)
- Integrated testing
- Seamless coordination


### cli_executor.agent_interface
VIBE MCP - Agent CLI Interface

High-level semantic interface for AI agents to execute CLI commands.
Agents call methods like `git_commit()` instead of raw shell commands.

Features:
- Semantic methods for common operations
- Automatic error recovery
- Git operations (init, commit, push, pull, branch)
- Python operations (pip, venv, pytest, ruff, mypy)
- Node.js operations (npm, yarn, pnpm)
- Docker operations (build, compose, run)
- Cloud operations (aws, gcloud, az)

Usage:
    cli = AgentCLI()

    # Git operations
    await cli.git_init()
    await cli.git_commit("Initial commit")
    await cli.git_push()

    # Python operations
    await cli.pip_install(["requests", "fastapi"])
    await cli.pytest_run()

    # Docker operations
    await cli.docker_build("my-app:latest")
    await cli.docker_compose_up()

**Classes:**
- `AgentCLI`: High-level CLI interface for AI agents
**Functions:**
- `__init__`: Initialize AgentCLI
- `_run`: Execute a command with optional recovery
- `git_init`: Initialize a new Git repository
- `git_clone`: Clone a Git repository
- `git_add`: Stage files for commit
- `git_commit`: Commit staged changes
- `git_push`: Push commits to remote
- `git_pull`: Pull changes from remote
- `git_checkout`: Checkout a branch
- `git_branch`: Manage Git branches
- `git_status`: Get repository status
- `git_log`: Get commit history
- `git_diff`: Show changes
- `git_stash`: Stash changes
- `git_reset`: Reset to previous state
- `pip_install`: Install Python packages
- `pip_install_requirements`: Install from requirements file
- `pip_uninstall`: Uninstall Python packages
- `pip_freeze`: List installed packages
- `pip_list`: List installed packages
- `create_venv`: Create a virtual environment
- `activate_venv`: Get activation command (returns command, doesn't activate)
- `pytest_run`: Run pytest
- `ruff_check`: Run ruff linter
- `ruff_format`: Run ruff formatter
- `mypy_check`: Run mypy type checker
- `python_run`: Run a Python script
- `npm_install`: Install npm packages
- `npm_run`: Run an npm script
- `npm_build`: Run npm build
- `npm_test`: Run npm test
- `npm_start`: Run npm start
- `npx_run`: Run npx command
- `docker_build`: Build a Docker image
- `docker_run`: Run a Docker container
- `docker_compose_up`: Start Docker Compose services
- `docker_compose_down`: Stop Docker Compose services
- `docker_ps`: List Docker containers
- `docker_logs`: Get container logs
- `docker_stop`: Stop a container
- `docker_rm`: Remove a container
- `mkdir`: Create a directory
- `rm`: Remove files or directories
- `cp`: Copy files or directories
- `mv`: Move files or directories
- `ls`: List directory contents
- `cat`: Read file contents
- `run_raw`: Run a raw command (escape hatch for custom commands)
- `get_stats`: Get execution statistics
- `get_history`: Get command history
- `get_agent_cli`: Get or create global AgentCLI instance

### cli_executor.error_recovery
VIBE MCP - Error Recovery System

Automatic error detection and recovery for CLI commands.
Implements the "vibe coding" principle of auto-fixing common issues.

Features:
- Pattern-based error detection
- Automatic fix suggestions
- Retry logic with exponential backoff
- Learning from successful fixes (stores in Mem0)

Usage:
    recovery = ErrorRecovery(executor)
    result = await recovery.attempt_recovery(command, failed_result)

**Classes:**
- `RecoveryStrategy`: Strategy for recovering from errors
- `ErrorPattern`: Pattern for matching and recovering from errors
- `RecoveryResult`: Result of a recovery attempt
- `ErrorRecovery`: Automatic error recovery system for CLI commands
**Functions:**
- `__init__`: Initialize error recovery system
- `_match_pattern`: Match error text against patterns and extract info
- `_resolve_package_name`: Resolve import name to actual package name
- `_build_fix_command`: Build the fix command from template
- `attempt_recovery`: Attempt to recover from a failed command
- `execute_with_recovery`: Execute command with automatic recovery on failure
- `get_recovery_history`: Get recovery attempt history
- `get_success_rate`: Get recovery success rate
- `add_pattern`: Add a custom error pattern
- `add_package_mapping`: Add a custom package name mapping

### cli_executor.executor
VIBE MCP - CLI Executor

Core command execution engine with safety checks, multiple execution modes,
and comprehensive error detection.

Features:
- Multiple execution modes: LOCAL, DOCKER, WSL, REMOTE
- Blocked dangerous commands
- Timeout handling
- Error type detection
- Async execution support

Usage:
    executor = CLIExecutor()
    result = await executor.execute("pip install requests")

    if result.success:
        print(result.stdout)
    else:
        print(f"Error: {result.error_type}")

**Classes:**
- `ExecutionMode`: Command execution environment
- `ShellType`: Shell type for command execution
- `ErrorType`: Categorized error types for recovery
- `CommandResult`: Result of a command execution
- `ExecutorConfig`: Configuration for CLI executor
- `CLIExecutor`: Executes CLI commands for agents with safety and error recovery
**Functions:**
- `to_dict`: Convert to dictionary for serialization
- `__init__`: Initialize the CLI executor
- `_detect_environment`: Detect available execution environments
- `_check_wsl`: Check if WSL is available
- `_check_docker`: Check if Docker is available and running
- `_is_command_blocked`: Check if command is in the blocked list
- `_is_command_dangerous`: Check if command matches dangerous patterns
- `_detect_error_type`: Detect the type of error from stderr/stdout
- `execute`: Execute a CLI command
- `_execute_local`: Execute command locally
- `_execute_docker`: Execute command in Docker container
- `_execute_wsl`: Execute command in WSL
- `get_history`: Get command execution history
- `clear_history`: Clear command history
- `get_stats`: Get execution statistics
- `run_command`: Quick command execution helper

### cli_executor.__init__
VIBE MCP - CLI Execution Module

Agent-driven command execution system that allows AI agents to safely
execute CLI commands on behalf of users.

Components:
- executor: Core command execution with safety checks
- error_recovery: Automatic error detection and recovery
- agent_interface: High-level semantic methods for agents

Usage:
    from src.cli import AgentCLI

    cli = AgentCLI()
    result = await cli.git_commit("Initial commit")
    result = await cli.pip_install(["requests", "fastapi"])


### core.auto_repair
AI Project Synthesizer - Auto-Repair System

Progressive auto-repair for:
- Code issues
- Configuration problems
- Missing dependencies
- Integration failures

**Classes:**
- `RepairAction`: Types of repair actions
- `RepairStep`: Single repair step
- `RepairPlan`: Plan for repairing gaps
- `AutoRepair`: Automatic repair system for identified gaps
**Functions:**
- `to_dict`
- `to_dict`
- `__init__`
- `create_plan`: Create a repair plan for a gap
- `execute_plan`: Execute a repair plan
- `_execute_step`: Execute a single repair step
- `_create_file`: Create a file with content
- `_modify_file`: Modify a file with find/replace
- `_create_dir`: Create a directory
- `_install_package`: Install a Python package
- `_run_command`: Run a shell command
- `_update_config`: Update a JSON config file
- `_deep_merge`: Deep merge updates into base dict
- `_plan_file_repair`: Create repair plan for file gaps
- `_plan_config_repair`: Create repair plan for config gaps
- `_plan_import_repair`: Create repair plan for import gaps
- `_plan_dependency_repair`: Create repair plan for dependency gaps
- `_plan_database_repair`: Create repair plan for database gaps
- `_plan_integration_repair`: Create repair plan for integration gaps
- `get_repair_history`: Get history of executed repairs
- `get_auto_repair`: Get or create auto-repair instance
- `repair_gaps`: Repair a list of gaps

### core.cache
AI Project Synthesizer - Caching Layer

Multi-backend caching for faster repeated operations:
- SQLite (default, no dependencies)
- Redis (optional, for distributed caching)
- Memory (fast, non-persistent)

Caches:
- Search results
- API responses
- Downloaded resource metadata

**Classes:**
- `CacheEntry`: A cached item with metadata
- `CacheBackend`: Abstract cache backend
- `MemoryCache`: In-memory cache (fast, non-persistent)
- `SQLiteCache`: SQLite-based persistent cache
- `RedisCache`: Redis-based distributed cache (optional)
- `CacheManager`: Unified cache manager with multiple backends
**Functions:**
- `is_expired`: Check if entry is expired
- `get`: Get value from cache
- `set`: Set value in cache
- `delete`: Delete value from cache
- `clear`: Clear all cache entries
- `stats`: Get cache statistics
- `__init__`
- `get`
- `set`
- `delete`
- `clear`
- `stats`
- `_evict_oldest`: Evict oldest entry
- `__init__`
- `_init_db`: Initialize database schema
- `get`
- `set`
- `delete`
- `clear`
- `stats`
- `cleanup_expired`: Remove expired entries
- `__init__`
- `_get_client`: Get or create Redis client
- `get`
- `set`
- `delete`
- `clear`
- `stats`
- `__init__`: Initialize cache manager
- `get`: Get cached value
- `set`: Set cached value with TTL
- `delete`: Delete cached value
- `clear`: Clear all cache
- `stats`: Get cache statistics
- `cache_key`: Generate cache key from arguments
- `get_cache`: Get or create cache manager
- `cached`: Decorator to cache function results
- `decorator`
- `wrapper`

### core.circuit_breaker
AI Project Synthesizer - Circuit Breaker Pattern

Enterprise-grade circuit breaker implementation for external API calls.
Prevents cascade failures and provides automatic recovery with configurable thresholds.

**Classes:**
- `CircuitState`: Circuit breaker states
- `CircuitBreakerConfig`: Configuration for circuit breaker
- `CircuitBreakerStats`: Statistics for circuit breaker
- `CircuitBreakerError`: Base exception for circuit breaker errors
- `CircuitOpenError`: Raised when circuit is open
- `CircuitTimeoutError`: Raised when call times out
- `CircuitBreaker`: Circuit breaker for protecting external service calls
- `CircuitBreakerRegistry`: Registry for managing multiple circuit breakers
**Functions:**
- `__post_init__`: Validate configuration
- `failure_rate`: Calculate failure rate as percentage
- `__init__`: Initialize circuit breaker
- `state`: Current circuit state
- `stats`: Get current statistics
- `_should_attempt_reset`: Check if circuit should attempt to reset from OPEN to HALF_OPEN
- `_record_failure`: Record a failure and potentially open circuit
- `_record_success`: Record a success and potentially close circuit
- `call`: Execute function with circuit breaker protection
- `reset`: Manually reset circuit to closed state
- `force_open`: Manually force circuit to open state
- `get_status`: Get current circuit breaker status
- `__init__`
- `get_breaker`: Get or create circuit breaker by name
- `get_all_status`: Get status of all circuit breakers
- `reset_all`: Reset all circuit breakers
- `circuit_breaker`: Decorator for applying circuit breaker to async functions
- `decorator`
- `wrapper`
- `get_circuit_breaker`: Get circuit breaker from global registry
- `get_all_circuit_breaker_status`: Get status of all circuit breakers
- `reset_all_circuit_breakers`: Reset all circuit breakers

### core.config
AI Project Synthesizer - Core Configuration

This module handles all configuration management including:
- Environment variable loading
- Settings validation
- Platform credentials
- LLM configuration

**Classes:**
- `PlatformSettings`: Platform API credentials and settings
- `LLMSettings`: LLM configuration settings
- `ElevenLabsSettings`: ElevenLabs voice AI configuration
- `AppSettings`: Main application settings
- `Settings`: Combined settings container
**Functions:**
- `get_enabled_platforms`: Return list of platforms with valid credentials
- `ensure_directory_exists`: Ensure directory exists
- `is_production`: Check if running in production
- `is_debug`: Check if debug mode is enabled
- `get_available_llm_providers`: Get list of LLM providers with valid API keys
- `get_settings`: Get cached settings instance

### core.exceptions
AI Project Synthesizer - Custom Exceptions

Hierarchical exception classes for error handling throughout the application.

**Classes:**
- `SynthesizerError`: Base exception for all AI Synthesizer errors
- `DiscoveryError`: Base exception for discovery layer errors
- `RepositoryNotFoundError`: Repository could not be found or accessed
- `PlatformUnavailableError`: Platform API is unavailable or unreachable
- `SearchError`: Error during repository search
- `AnalysisError`: Base exception for analysis layer errors
- `ParseError`: Error parsing source code
- `UnsupportedLanguageError`: Language is not supported for analysis
- `ResolutionError`: Base exception for dependency resolution errors
- `DependencyConflictError`: Unresolvable dependency conflict detected
- `ResolutionTimeoutError`: Dependency resolution timed out
- `SynthesisError`: Base exception for synthesis layer errors
- `MergeConflictError`: Code merge conflict that couldn't be resolved
- `ExtractionError`: Error extracting code from repository
- `TemplateError`: Error applying project template
- `GenerationError`: Base exception for documentation generation errors
- `DiagramGenerationError`: Error generating diagrams
- `RateLimitError`: API rate limit exceeded
- `AuthenticationError`: Authentication failed for platform
- `ConfigurationError`: Configuration error
- `LLMError`: Error from LLM service
- `TimeoutError`: Operation timed out
- `SecurityScanError`: Security scan failed or found issues
**Functions:**
- `__init__`
- `to_dict`: Convert exception to dictionary for JSON serialization
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`
- `__init__`

### core.gap_analyzer
AI Project Synthesizer - Gap Analyzer & Auto-Repair System

Robust progressive gap filling:
- Identifies missing components
- Auto-repairs issues
- Validates system integrity
- Generates repair reports

**Classes:**
- `GapSeverity`: Severity levels for gaps
- `GapCategory`: Categories of gaps
- `Gap`: Represents a system gap
- `AnalysisReport`: Gap analysis report
- `GapAnalyzer`: Comprehensive gap analyzer and auto-repair system
**Functions:**
- `to_dict`
- `total_gaps`
- `critical_gaps`
- `unfixed_gaps`
- `to_dict`
- `to_markdown`: Generate markdown report
- `__init__`
- `_setup_checks`: Set up all gap checks
- `add_gap`: Add a gap to the list
- `analyze`: Run full gap analysis
- `_run_check`: Run a single check
- `_auto_fix_gaps`: Auto-fix all fixable gaps
- `_check_core_imports`: Check core module imports
- `_check_agent_imports`: Check agent imports
- `_check_dashboard_imports`: Check dashboard imports
- `_check_workflow_imports`: Check workflow imports
- `_check_env_file`: Check 
- `_fix_create_env`: Create 
- `_check_settings_file`: Check settings file exists
- `_fix_create_settings`: Create default settings file
- `_check_api_keys`: Check API keys are configured
- `_check_directories`: Check required directories exist
- `_check_n8n_workflows`: Check n8n workflow files exist
- `_check_init_files`: Check __init__
- `_check_database`: Check database connectivity
- `_check_llm_connection`: Check LLM connectivity
- `_check_voice_system`: Check voice system
- `_check_test_coverage`: Check test coverage
- `get_gap_analyzer`: Get or create gap analyzer
- `run_gap_analysis`: Run gap analysis and return report

### core.health
AI Project Synthesizer - Health Checks & Monitoring

Professional health check system for:
- Service status monitoring
- Dependency verification
- API connectivity checks
- Resource availability

**Classes:**
- `HealthStatus`: Health status levels
- `ComponentHealth`: Health status of a component
- `SystemHealth`: Overall system health
- `HealthChecker`: System health checker
**Functions:**
- `to_dict`: Convert to dictionary
- `__init__`: Initialize health checker
- `check_all`: Run all health checks
- `_check_lm_studio`: Check LM Studio connectivity
- `_check_ollama`: Check Ollama connectivity
- `_check_github`: Check GitHub API connectivity
- `_check_huggingface`: Check HuggingFace API
- `_check_kaggle`: Check Kaggle API
- `_check_elevenlabs`: Check ElevenLabs API
- `_check_openai`: Check OpenAI API
- `get_health_checker`: Get or create health checker
- `check_health`: Quick function to check system health

### core.hotkey_manager
AI Project Synthesizer - Hotkey Manager

Global hotkey system for:
- Voice activation (no pause limits)
- Quick actions
- Automation control
- System commands

**Classes:**
- `HotkeyAction`: Available hotkey actions
- `HotkeyBinding`: Hotkey binding configuration
- `HotkeyManager`: Global hotkey management system
**Functions:**
- `__init__`
- `_setup_default_bindings`: Set up default hotkey bindings
- `register`: Register a callback for a hotkey action
- `unregister`: Unregister a callback
- `set_keys`: Update hotkey binding
- `enable`: Enable a hotkey
- `disable`: Disable a hotkey
- `_trigger_action`: Trigger callbacks for an action
- `_register_keyboard_hotkey`: Register a single keyboard hotkey
- `_on_hold_start`: Handle hold key press
- `_on_hold_end`: Handle hold key release
- `start`: Start listening for hotkeys
- `stop`: Stop listening for hotkeys
- `get_bindings`: Get all hotkey bindings
- `is_holding`: Check if a hold key is currently held
- `get_hotkey_manager`: Get or create hotkey manager

### core.lifecycle
AI Project Synthesizer - Lifecycle Management

Enterprise-grade lifecycle management with graceful shutdown,
signal handling, and cleanup procedures for production deployment.

**Classes:**
- `ShutdownState`: Shutdown states
- `ShutdownTask`: Task to execute during shutdown
- `LifecycleManager`: Manages application lifecycle with graceful shutdown
- `ResourceManager`: Manages resources that need cleanup during shutdown
- `BackgroundTaskManager`: Manages background tasks with proper lifecycle integration
**Functions:**
- `__init__`: Initialize lifecycle manager
- `_setup_signal_handlers`: Setup signal handlers for graceful shutdown
- `_signal_handler`: Handle shutdown signals
- `add_shutdown_task`: Add shutdown task
- `remove_shutdown_task`: Remove shutdown task by name
- `track_task`: Track a running task for shutdown
- `cleanup`
- `wait_for_shutdown`: Wait for shutdown signal
- `is_shutting_down`: Check if shutdown is in progress
- `is_shutdown_complete`: Check if shutdown is complete
- `shutdown`: Execute graceful shutdown
- `_cancel_running_tasks`: Cancel all tracked running tasks
- `_execute_shutdown_tasks`: Execute all shutdown tasks
- `_cleanup_resources`: Cleanup any remaining resources
- `get_status`: Get current lifecycle status
- `__init__`
- `register`: Register resource for cleanup
- `unregister`: Unregister resource
- `cleanup_all`: Cleanup all registered resources
- `managed_resource`: Context manager for managed resources
- `track_async_task`: Decorator to track async tasks for shutdown
- `shutdown_on_signal`: Decorator to register function for shutdown
- `get_lifecycle_status`: Get global lifecycle status
- `wait_for_shutdown_signal`: Wait for shutdown signal
- `initiate_shutdown`: Initiate graceful shutdown
- `is_shutting_down`: Check if shutdown is in progress
- `shutdown_logging`: Flush logging during shutdown
- `shutdown_metrics`: Finalize metrics during shutdown
- `__init__`
- `submit`: Submit background task
- `wrapped_task`
- `wait_all`: Wait for all tasks to complete

### core.logging
AI Project Synthesizer - Logging Configuration

Structured logging setup using structlog for consistent,
machine-parseable log output across all components.

**Classes:**
- `LogContext`: Context manager for adding temporary context to logs
**Functions:**
- `setup_logging`: Configure application logging
- `get_logger`: Get a logger instance for the specified module
- `__init__`
- `__enter__`
- `__exit__`
- `_ensure_logging_initialized`: Ensure logging is initialized exactly once

### core.memory
AI Project Synthesizer - Memory System

Persistent memory for:
- Conversation history
- Search history
- Bookmarks
- User preferences
- Agent memories
- Workflow state

**Classes:**
- `MemoryType`: Types of memory entries
- `MemoryEntry`: Single memory entry
- `SearchEntry`: Search history entry
- `Bookmark`: Bookmark entry
- `MemoryStore`: SQLite-based persistent memory store
**Functions:**
- `to_dict`
- `to_dict`
- `to_dict`
- `__init__`
- `_init_db`: Initialize database schema
- `_get_conn`
- `save_memory`: Save a memory entry
- `get_memory`: Get a memory entry by ID
- `search_memories`: Search memories by type and tags
- `delete_memory`: Delete a memory entry
- `save_search`: Save a search to history
- `get_search_history`: Get recent search history
- `replay_search`: Get a search for replay
- `save_bookmark`: Save a bookmark
- `get_bookmarks`: Get bookmarks with optional filtering
- `delete_bookmark`: Delete a bookmark
- `save_message`: Save a conversation message
- `get_conversation`: Get conversation history for a session
- `save_workflow_state`: Save workflow state
- `get_workflow_state`: Get workflow state
- `get_memory_store`: Get or create memory store

### core.observability
AI Project Synthesizer - Observability Module

Enterprise-grade observability with correlation IDs, metrics collection,
and health checks for production monitoring.

**Classes:**
- `CorrelationManager`: Manages correlation IDs for request tracing across the pipeline
- `MetricValue`: Single metric value with timestamp
- `MetricType`: Metric types
- `MetricsCollector`: Collects and manages application metrics
- `HealthCheck`: Individual health check implementation
- `HealthChecker`: Manages and executes multiple health checks
- `PerformanceTracker`: Tracks performance metrics for operations
**Functions:**
- `__init__`
- `generate_id`: Generate a new correlation ID
- `set_correlation_id`: Set correlation ID for current context
- `get_correlation_id`: Get correlation ID for current context
- `clear_correlation_id`: Clear correlation ID from current context
- `correlation_context`: Context manager for correlation ID
- `__init__`: Initialize metrics collector
- `increment`: Increment counter metric
- `set_gauge`: Set gauge metric value
- `record_timer`: Record timer metric
- `record_histogram`: Record histogram value
- `get_counter`: Get counter value
- `get_gauge`: Get gauge value
- `get_metric_values`: Get metric values
- `get_metric_summary`: Get metric summary statistics
- `get_all_metrics`: Get all metrics summary
- `reset`: Reset all metrics
- `__init__`: Initialize health check
- `check`: Execute health check
- `__init__`
- `add_check`: Add health check
- `remove_check`: Remove health check
- `check_all`: Execute all health checks
- `check_single`: Execute single health check
- `get_check_names`: Get all check names
- `check_ollama_health`: Check if Ollama is accessible
- `check_github_api_health`: Check if GitHub API is accessible
- `check_disk_space_health`: Check if sufficient disk space is available
- `__init__`
- `record_operation`: Record operation duration
- `get_operation_stats`: Get operation statistics
- `track_performance`: Context manager for tracking operation performance
- `track_metrics`: Decorator for tracking function metrics
- `decorator`
- `async_wrapper`
- `get_correlation_id`: Get current correlation ID
- `set_correlation_id`: Set correlation ID for current context
- `check_lmstudio_health`: Health check for LM Studio service
- `register_default_health_checks`: Register default health checks for the system
- `check_ollama`

### core.plugins
AI Project Synthesizer - Plugin System

Extensible plugin architecture for:
- Custom platform integrations (new search sources)
- Custom synthesis strategies
- Custom analysis tools
- Custom voice providers

Plugins are discovered from:
1. Built-in plugins (src/plugins/)
2. User plugins (~/.synthesizer/plugins/)
3. Project plugins (.synthesizer/plugins/)

**Classes:**
- `PluginType`: Types of plugins
- `PluginMetadata`: Plugin metadata
- `Plugin`: Base class for all plugins
- `PlatformPlugin`: Plugin for adding new search platforms
- `SynthesisPlugin`: Plugin for custom synthesis strategies
- `AnalysisPlugin`: Plugin for custom code analysis
- `HookPlugin`: Plugin for event hooks
- `PluginManager`: Manages plugin discovery, loading, and lifecycle
**Functions:**
- `metadata`: Return plugin metadata
- `initialize`: Initialize plugin with config
- `shutdown`: Cleanup on shutdown
- `search`: Search the platform
- `get_details`: Get details for a specific item
- `download`: Download an item
- `synthesize`: Synthesize project from sources
- `analyze`: Analyze code at path
- `on_search_start`: Called before search
- `on_search_complete`: Called after search
- `on_synthesis_start`: Called before synthesis
- `on_synthesis_complete`: Called after synthesis
- `__init__`: Initialize plugin manager
- `discover_plugins`: Discover and load all plugins
- `_load_plugin_file`: Load a plugin from file
- `register_plugin`: Register a plugin instance
- `get_plugin`: Get plugin by name
- `get_plugins`: Get all plugins, optionally filtered by type
- `initialize_all`: Initialize all plugins
- `shutdown_all`: Shutdown all plugins
- `list_plugins`: List all registered plugins
- `get_plugin_manager`: Get or create plugin manager

### core.realtime
AI Project Synthesizer - Real-time Event System

Real-time event handling for:
- Workflow updates
- Agent status changes
- Search results streaming
- Health monitoring
- Notifications

**Classes:**
- `EventType`: Types of real-time events
- `Event`: Real-time event
- `EventBus`: Central event bus for real-time communication
**Functions:**
- `to_dict`
- `to_json`
- `__init__`
- `subscribe`: Subscribe to a specific event type
- `subscribe_all`: Subscribe to all events
- `unsubscribe`: Unsubscribe from an event type
- `publish`: Publish an event
- `emit`: Emit an event (sync wrapper)
- `emit_async`: Emit an event asynchronously
- `get_history`: Get event history
- `create_queue`: Create a queue for streaming events
- `remove_queue`: Remove a queue
- `stream_events`: Async generator for streaming events
- `get_event_bus`: Get or create event bus
- `emit_workflow_event`: Emit a workflow event
- `emit_agent_event`: Emit an agent event
- `emit_search_event`: Emit a search event
- `emit_notification`: Emit a notification event

### core.resource_manager
Resource manager for preventing resource leaks.

**Classes:**
- `ResourceManager`: Manages and tracks resources to prevent leaks
- `ResourceLeakDetector`: Detects resource leaks by monitoring system resources
**Functions:**
- `__init__`
- `register`: Register a resource for tracking
- `unregister`: Unregister a resource
- `add_cleanup_callback`: Add a cleanup callback to be called on shutdown
- `cleanup_type`: Clean up all resources of a specific type
- `cleanup_all`: Clean up all tracked resources
- `_sync_cleanup_type`: Synchronous cleanup for when no event loop is available
- `get_stats`: Get statistics on active resources
- `check_for_leaks`: Check for potential resource leaks
- `managed_browser`: Context manager for browser instances
- `managed_process`: Context manager for subprocess processes
- `__init__`
- `_get_current_usage`: Get current resource usage
- `check_for_leaks`: Check if resources have increased beyond threshold
- `start_leak_monitor`: Start monitoring for resource leaks

### core.safe_formatter
Safe template formatter to prevent injection attacks.

**Classes:**
- `SafeTemplateFormatter`: Safe template formatter that only allows whitelisted placeholders
**Functions:**
- `__init__`: Initialize formatter with allowed placeholders
- `format`: Safely format a template with context
- `format_markdown`: Format template for markdown (preserves markdown formatting)

### core.security
AI Project Synthesizer - Security Utilities

Enterprise-grade security utilities for secret management,
input validation, and secure logging.

**Classes:**
- `SecretManager`: Manages secure handling of sensitive data
- `InputValidator`: Validates and sanitizes user inputs
- `SecureLogger`: Wrapper for secure logging that masks secrets
- `SecurityConfig`: Security configuration settings
**Functions:**
- `mask_secrets`: Mask potential secrets in text
- `hash_secret`: Create a secure hash of a secret for comparison
- `generate_secure_id`: Generate a cryptographically secure random ID
- `validate_repository_url`: Validate repository URL format
- `sanitize_filename`: Sanitize filename to prevent path traversal
- `validate_search_query`: Validate search query to prevent injection
- `sanitize_path`: Sanitize file system path to prevent traversal
- `__init__`
- `_sanitize_message`: Sanitize message and kwargs for logging
- `info`: Log info message with secret masking
- `error`: Log error message with secret masking
- `warning`: Log warning message with secret masking
- `debug`: Log debug message with secret masking
- `secure_input`: Decorator for validating and sanitizing function inputs
- `decorator`
- `wrapper`
- `is_domain_allowed`: Check if URL domain is in allowed list
- `get_secure_logger`: Get a secure logger instance

### core.security_utils
Security utilities for input validation and secure operations.

**Functions:**
- `validate_command_args`: Validate and sanitize command arguments
- `validate_path`: Validate file path to prevent directory traversal
- `validate_url`: Validate URL to prevent malicious URLs
- `sanitize_template_string`: Sanitize template strings to prevent injection
- `safe_subprocess_run`: Safely run subprocess with validation
- `secure_filename`: Sanitize filename for secure storage

### core.settings_manager
AI Project Synthesizer - Settings Manager

Comprehensive settings system with:
- Tabbed configuration panels
- Feature toggles
- Hotkey management
- Voice settings (no pause limits)
- Auto-continue options
- Automation controls

**Classes:**
- `SettingsTab`: Settings panel tabs
- `VoiceMode`: Voice interaction modes
- `AutoContinueMode`: Auto-continue behavior
- `GeneralSettings`: General application settings
- `VoiceSettings`: Voice and speech settings
- `AutomationSettings`: Automation and auto-continue settings
- `HotkeySettings`: Hotkey configuration
- `AIMLSettings`: AI/ML configuration
- `WorkflowSettings`: Workflow configuration
- `AdvancedSettings`: Advanced settings
- `AllSettings`: Complete settings configuration
- `SettingsManager`: Central settings management system
**Functions:**
- `__init__`
- `load`: Load settings from file
- `save`: Save settings to file
- `settings`: Get current settings
- `get_tab`: Get settings for a specific tab
- `update`: Update settings for a tab
- `toggle`: Toggle a boolean feature
- `on_change`: Register a change listener
- `_notify`: Notify listeners of a change
- `get_feature_toggles`: Get all feature toggles organized by tab
- `export_settings`: Export all settings as dictionary
- `import_settings`: Import settings from dictionary
- `reset_to_defaults`: Reset settings to defaults
- `get_settings_manager`: Get or create settings manager

### core.telemetry
AI Project Synthesizer - Telemetry System

OPT-IN usage analytics for:
- Understanding usage patterns
- Improving features
- Identifying issues

PRIVACY:
- Disabled by default
- No personal data collected
- No code/content transmitted
- Only aggregate metrics
- Can be disabled anytime

**Classes:**
- `TelemetryEvent`: A telemetry event
- `TelemetryConfig`: Telemetry configuration
- `TelemetryCollector`: Opt-in telemetry collector
**Functions:**
- `to_dict`
- `__init__`: Initialize telemetry collector
- `_generate_anonymous_id`: Generate anonymous machine ID
- `_load_config`: Load saved telemetry config
- `_save_config`: Save telemetry config
- `enable`: Enable telemetry (opt-in)
- `disable`: Disable telemetry
- `is_enabled`: Check if telemetry is enabled
- `track`: Track an event
- `_sanitize_properties`: Remove any potential PII from properties
- `_save_events`: Save events locally
- `get_stats`: Get local telemetry stats
- `track_search`: Track a search event
- `track_assembly`: Track a project assembly
- `track_error`: Track an error (type only, no details)
- `get_telemetry`: Get or create telemetry collector
- `track`: Quick function to track an event

### core.version
AI Project Synthesizer - Version Management

Semantic versioning with automatic version bumping.

**Classes:**
- `VersionInfo`: Semantic version information
**Functions:**
- `__str__`
- `parse`: Parse version string
- `bump_major`: Bump major version
- `bump_minor`: Bump minor version
- `bump_patch`: Bump patch version
- `get_version`: Get current version
- `get_version_info`: Get version info object
- `get_build_info`: Get build information

### core.__init__
AI Project Synthesizer - Core Package

Core utilities, configuration, and shared components.


### dashboard.agent_routes
AI Project Synthesizer - Agent API Routes

API endpoints for agent management:
- Research agent
- Synthesis agent
- Voice agent
- Automation agent
- Code agent

**Classes:**
- `ResearchRequest`
- `SynthesisRequest`
- `VoiceRequest`
- `CodeRequest`
- `FixCodeRequest`
- `AutomationRequest`
**Functions:**
- `get_agents_status`: Get status of all agents
- `run_research`: Run research agent
- `run_synthesis`: Run synthesis agent
- `voice_speak`: Speak text using voice agent
- `voice_process`: Process text with voice agent
- `voice_state`: Get voice agent state
- `voice_start`: Start voice listening
- `voice_stop`: Stop voice listening
- `run_automation`: Run automation agent
- `automation_health_check`: Run health check via automation agent
- `code_generate`: Generate code using code agent
- `code_fix`: Fix code using code agent
- `code_review`: Review code using code agent

### dashboard.app
AI Project Synthesizer - Web Dashboard Application

FastAPI-based web dashboard for visual project management.

**Classes:**
- `SearchRequest`
- `AssembleRequest`
**Functions:**
- `create_app`: Create FastAPI application
- `root`: Dashboard home page
- `health`: Get system health status
- `version`: Get version info
- `cache_stats`: Get cache statistics
- `cache_clear`: Clear cache
- `list_plugins`: List installed plugins
- `search`: Search across platforms
- `assemble`: Assemble a project
- `list_projects`: List assembled projects
- `websocket_endpoint`: WebSocket for real-time updates
- `get_metrics`: Get system metrics
- `record_metrics`: Record metrics from n8n workflows
- `record_health_metrics`: Record health check metrics
- `record_test_metrics`: Record test run metrics
- `receive_alert`: Receive alerts from n8n workflows
- `attempt_recovery`: Attempt to recover unhealthy components
- `speak`: Generate speech from text
- `get_research_topics`: Get current research topics
- `save_research`: Save research results
- `test_search`: Test search functionality
- `test_cache`: Test cache functionality
- `health_component`: Check health of specific component
- `automation_status`: Get automation coordinator status
- `run_automation_tests`: Run integration tests
- `get_dashboard_html`: Generate dashboard HTML
- `run_dashboard`: Run the dashboard server

### dashboard.memory_routes
AI Project Synthesizer - Memory & Bookmarks API Routes

API endpoints for:
- Memory management
- Search history
- Bookmarks
- Conversation history
- Real-time events (SSE)

**Classes:**
- `MemoryRequest`
- `BookmarkRequest`
- `SearchHistoryRequest`
- `MessageRequest`
**Functions:**
- `save_memory`: Save a memory entry
- `get_memories`: Get memories with optional filtering
- `get_memory`: Get a specific memory entry
- `delete_memory`: Delete a memory entry
- `save_search`: Save a search to history
- `get_search_history`: Get search history
- `replay_search`: Get search details for replay
- `save_bookmark`: Save a bookmark
- `get_bookmarks`: Get bookmarks with optional filtering
- `delete_bookmark`: Delete a bookmark
- `save_message`: Save a conversation message
- `get_conversation`: Get conversation history
- `stream_events`: Server-Sent Events stream for real-time updates
- `event_generator`
- `get_event_history`: Get event history
- `emit_event`: Emit a custom event
- `save_workflow_state`: Save workflow state
- `get_workflow_state`: Get workflow state

### dashboard.settings_routes
AI Project Synthesizer - Settings API Routes

API endpoints for settings management:
- Get/update settings by tab
- Feature toggles
- Hotkey management
- Export/import settings

**Classes:**
- `UpdateSettingsRequest`: Request to update settings
- `ToggleFeatureRequest`: Request to toggle a feature
- `UpdateHotkeyRequest`: Request to update a hotkey
**Functions:**
- `get_all_settings`: Get all settings
- `get_tabs`: Get available settings tabs
- `get_tab_settings`: Get settings for a specific tab
- `update_tab_settings`: Update settings for a specific tab
- `toggle_feature`: Toggle a boolean feature
- `get_all_toggles`: Get all feature toggles
- `reset_settings`: Reset settings to defaults
- `export_settings`: Export all settings
- `import_settings`: Import settings
- `get_hotkey_bindings`: Get all hotkey bindings
- `update_hotkey`: Update a hotkey binding
- `enable_hotkey`: Enable a hotkey
- `disable_hotkey`: Disable a hotkey
- `get_voice_quick_settings`: Get quick voice settings
- `toggle_voice_pause`: Toggle voice pause detection
- `toggle_auto_speak`: Toggle auto-speak responses
- `get_automation_quick_settings`: Get quick automation settings
- `toggle_auto_continue`: Toggle auto-continue

### dashboard.webhook_routes
AI Project Synthesizer - Webhook API Routes

Webhook endpoints for external integrations:
- GitHub webhooks
- n8n webhooks
- Custom webhooks
- Slack/Discord notifications

**Functions:**
- `github_webhook`: Handle GitHub webhooks
- `n8n_webhook`: Handle n8n workflow callbacks
- `custom_webhook`: Handle custom webhooks
- `slack_webhook`: Handle Slack webhooks (slash commands, events)
- `discord_webhook`: Handle Discord webhooks (interactions)
- `list_webhooks`: List available webhook endpoints
- `test_webhook`: Test webhook endpoint for debugging

### dashboard.__init__
AI Project Synthesizer - Web Dashboard

Visual interface for:
- Project browsing and assembly
- Search across platforms
- Health monitoring
- Plugin management


### discovery.base_client
AI Project Synthesizer - Platform Client Base

Abstract base class and data models for all platform API clients.
Each platform (GitHub, HuggingFace, etc.) implements this interface.

**Classes:**
- `Platform`: Supported platforms for repository discovery
- `DiscoveryError`: Base exception for discovery errors
- `AuthenticationError`: Authentication failed
- `RateLimitError`: Rate limit exceeded
- `RepositoryNotFoundError`: Repository not found
- `RepositoryInfo`: Standard repository information across all platforms
- `SearchResult`: Result of a search operation
- `FileContent`: Content of a file from a repository
- `DirectoryListing`: Listing of files in a repository directory
- `PlatformClient`: Abstract base class for platform API clients
**Functions:**
- `__init__`
- `to_dict`: Convert to dictionary for serialization
- `to_dict`: Convert to dictionary for serialization
- `text`: Get content as text
- `platform_name`: Return the platform identifier
- `is_authenticated`: Check if client is authenticated
- `search`: Search for repositories matching the query
- `get_repository`: Get detailed information about a specific repository
- `get_contents`: Get contents of a directory in the repository
- `get_file`: Get contents of a specific file
- `clone`: Clone repository to local filesystem
- `get_readme`: Get repository README content
- `get_license`: Get repository license content
- `check_health`: Check if the platform API is accessible

### discovery.firecrawl_client
VIBE MCP - Firecrawl Client Integration

Web scraping client using Firecrawl API for intelligent content extraction.
Implements Phase 5.2 of the VIBE MCP roadmap.

Features:
- Web page scraping and content extraction
- Site mapping and crawling
- Text cleaning and processing
- Async batch processing
- Rate limiting and caching

**Classes:**
- `FirecrawlFormat`: Output format options
- `FirecrawlMode`: Scraping modes
- `ScrapedContent`: Scraped content representation
- `SiteMap`: Site map representation
- `FirecrawlClient`: Firecrawl API client for web scraping
**Functions:**
- `__init__`: Initialize Firecrawl client
- `__aenter__`: Async context manager entry
- `__aexit__`: Async context manager exit
- `_ensure_session`: Ensure aiohttp session exists
- `_request`: Make request to Firecrawl API
- `_check_rate_limit`: Check and respect rate limits
- `_fallback_scrape`: Fallback scraping without Firecrawl API
- `scrape_url`: Scrape a single URL
- `crawl_site`: Crawl an entire site
- `map_site`: Generate a site map
- `batch_scrape`: Scrape multiple URLs concurrently
- `scrape_with_semaphore`
- `test_connection`: Test connection to Firecrawl API
- `clear_cache`: Clear the internal cache
- `get_rate_limit_status`: Get current rate limit status
- `clean_text`: Clean extracted text
- `extract_links`: Extract links from content
- `create_firecrawl_client`: Create and initialize Firecrawl client
- `main`: Test the Firecrawl client

### discovery.firecrawl_enhanced
Enhanced Firecrawl Client for VIBE MCP

Extended web scraping with advanced features:
- Intelligent caching with TTL and invalidation
- Advanced rate limiting with backoff
- Content extraction with AI enhancement
- Batch processing with prioritization
- Integration with browser automation

Builds on the existing FirecrawlClient with additional capabilities.

**Classes:**
- `CacheStrategy`: Caching strategies
- `RateLimitStrategy`: Rate limiting strategies
- `ContentPriority`: Content processing priority
- `CacheEntry`: Cache entry with metadata
- `RateLimitConfig`: Rate limiting configuration
- `ContentExtractionConfig`: Content extraction configuration
- `FirecrawlEnhanced`: Enhanced Firecrawl client with advanced features
- `RateLimiter`: Adaptive rate limiter with multiple strategies
**Functions:**
- `is_expired`
- `age_seconds`
- `__init__`: Initialize enhanced Firecrawl client
- `_init_disk_cache`: Initialize SQLite disk cache
- `_get_from_cache`: Get content from cache
- `_set_cache`: Store content in cache
- `_add_to_memory_cache`: Add to memory cache with LRU eviction
- `_get_cache_key`: Generate cache key for URL and options
- `scrape_url_enhanced`: Enhanced URL scraping with caching and rate limiting
- `_scrape_with_browser`: Scrape using browser automation
- `_enhance_content`: Enhance content with AI processing
- `_extract_tables`: Extract and format tables from content
- `_extract_code_blocks`: Extract code blocks with language detection
- `_detect_language`: Detect content language using simple heuristics
- `_generate_summary`: Generate content summary using AI
- `batch_scrape_priority`: Batch scrape with priority queue
- `process_item`
- `clear_cache`: Clear cache
- `get_cache_stats`: Get cache statistics
- `close`: Cleanup resources
- `__init__`
- `acquire`: Acquire permission to make a request
- `_fixed_wait`: Fixed delay between requests
- `_exponential_backoff_wait`: Exponential backoff after failures
- `_adaptive_wait`: Adaptive delay based on response times
- `_token_bucket_wait`: Token bucket algorithm
- `record_success`: Record successful request
- `record_failure`: Record failed request
- `create_firecrawl_enhanced`: Create and initialize enhanced Firecrawl client
- `main`

### discovery.github_client
AI Project Synthesizer - GitHub Client

Full-featured GitHub API client using ghapi library.
Provides repository search, analysis, and download capabilities.

**Classes:**
- `GitHubClient`: GitHub API client using ghapi
**Functions:**
- `__init__`: Initialize GitHub client
- `_init_api`: Initialize ghapi client
- `platform_name`
- `is_authenticated`
- `search`: Search GitHub repositories
- `get_repository`: Get detailed repository information
- `get_contents`: Get directory contents
- `get_file`: Get file contents
- `clone`: Clone repository to local filesystem
- `_convert_repo`: Convert GitHub API response to RepositoryInfo
- `_search_fallback`: Fallback search using httpx when ghapi is unavailable
- `_convert_repo_dict`: Convert dict response to RepositoryInfo
- `_get_repo_fallback`: Fallback repo fetch using httpx
- `_get_contents_fallback`: Fallback contents fetch using httpx
- `_get_file_fallback`: Fallback file fetch using httpx
- `get_languages`: Get language breakdown for repository
- `get_topics`: Get repository topics/tags
- `check_has_tests`: Check if repository has tests directory
- `check_has_ci`: Check if repository has CI configuration

### discovery.gitlab_client
VIBE MCP - GitLab Client Integration

Comprehensive GitLab API client for project discovery and management.
Implements Phase 5.1 of the VIBE MCP roadmap.

Features:
- Full GitLab API v4 coverage
- Repository search and cloning
- Issue and merge request management
- CI/CD pipeline integration
- Project analytics and insights

**Classes:**
- `GitLabVisibility`: Project visibility levels
- `GitLabState`: Issue/MR state
- `GitLabSort`: Sort options
- `GitLabProject`: GitLab project representation
- `GitLabIssue`: GitLab issue representation
- `GitLabMergeRequest`: GitLab merge request representation
- `GitLabPipeline`: GitLab CI/CD pipeline representation
- `GitLabClient`: Comprehensive GitLab API client
**Functions:**
- `__init__`: Initialize GitLab client
- `__aenter__`: Async context manager entry
- `__aexit__`: Async context manager exit
- `_ensure_session`: Ensure aiohttp session exists
- `_request`: Make authenticated request to GitLab API
- `_check_rate_limit`: Check and respect rate limits
- `_paginate`: Handle paginated responses
- `get_project`: Get a single project by ID or path
- `search_projects`: Search for projects
- `get_project_languages`: Get language statistics for a project
- `get_project_readme`: Get README content for a project
- `clone_project`: Clone a GitLab project
- `_parse_project`: Parse project data from API response
- `get_issues`: Get issues for a project
- `create_issue`: Create a new issue
- `_parse_issue`: Parse issue data from API response
- `get_merge_requests`: Get merge requests for a project
- `_parse_merge_request`: Parse merge request data from API response
- `get_pipelines`: Get CI/CD pipelines for a project
- `_parse_pipeline`: Parse pipeline data from API response
- `get_project_analytics`: Get comprehensive analytics for a project
- `_calculate_monthly_rate`: Calculate monthly creation rate for items
- `get_current_user`: Get current authenticated user
- `get_user_projects`: Get projects for a user
- `get_group_projects`: Get projects in a group
- `test_connection`: Test connection to GitLab API
- `clear_cache`: Clear the internal cache
- `get_rate_limit_status`: Get current rate limit status
- `create_gitlab_client`: Create and initialize GitLab client
- `main`: Test the GitLab client

### discovery.gitlab_enhanced
Enhanced GitLab Client for VIBE MCP

Extended GitLab integration with advanced features:
- Merge request automation
- CI/CD pipeline integration
- Issue tracking automation
- Webhook management
- Project analytics

Builds on the existing GitLabClient with additional automation capabilities.

**Classes:**
- `MRAction`: Merge request actions
- `PipelineTrigger`: Pipeline trigger types
- `MRTemplate`: Merge request template
- `MRReviewResult`: Result of MR review
- `PipelineConfig`: CI/CD pipeline configuration
- `GitLabEnhanced`: Enhanced GitLab client with automation features
**Functions:**
- `__init__`: Initialize enhanced GitLab client
- `_load_mr_templates`: Load MR templates from configuration
- `create_automated_mr`: Create an automated merge request
- `review_mr_with_ai`: Review a merge request using AI
- `get_merge_request`: Get a specific merge request
- `get_mr_changes`: Get merge request changes
- `add_mr_comment`: Add comment to merge request
- `merge_mr`: Merge a merge request
- `_build_review_prompt`: Build AI review prompt
- `_parse_ai_review`: Parse AI review response
- `trigger_pipeline`: Trigger a CI/CD pipeline
- `wait_for_pipeline`: Wait for pipeline to complete
- `get_pipeline`: Get specific pipeline
- `get_pipeline_jobs`: Get jobs for a pipeline
- `retry_pipeline_job`: Retry a failed pipeline job
- `create_issue_from_error`: Create an issue from an error
- `link_issue_to_mr`: Link an issue to a merge request
- `create_webhook`: Create a webhook
- `test_webhook`: Test a webhook
- `open_in_browser`: Open GitLab page in browser for manual operations
- `close_browser`: Close browser if open
- `create_gitlab_enhanced`: Create and initialize enhanced GitLab client
- `main`

### discovery.huggingface_client
AI Project Synthesizer - HuggingFace Client

Full-featured HuggingFace Hub API client.
Provides model, dataset, and space search capabilities.

**Classes:**
- `HFModelInfo`: HuggingFace model information
- `HFDatasetInfo`: HuggingFace dataset information
- `HuggingFaceClient`: HuggingFace Hub API client
**Functions:**
- `to_repository_info`: Convert to standard RepositoryInfo format
- `to_repository_info`: Convert to standard RepositoryInfo format
- `__init__`: Initialize HuggingFace client
- `_init_api`: Initialize huggingface_hub client
- `platform_name`
- `is_authenticated`
- `search`: Search HuggingFace Hub
- `_search_models`: Search HuggingFace models
- `_search_datasets`: Search HuggingFace datasets
- `_search_spaces`: Search HuggingFace Spaces
- `get_repository`: Get detailed repository information
- `_model_to_repo_info`: Convert model info to RepositoryInfo
- `_dataset_to_repo_info`: Convert dataset info to RepositoryInfo
- `_space_to_repo_info`: Convert space info to RepositoryInfo
- `get_contents`: Get directory contents from HuggingFace repo
- `get_file`: Get file contents from HuggingFace repo
- `clone`: Clone HuggingFace repository
- `_search_fallback`: Fallback search using httpx

### discovery.kaggle_client
AI Project Synthesizer - Kaggle Client

Full-featured Kaggle API client for discovering datasets, competitions,
notebooks, and models. Provides comprehensive search and analysis capabilities.

**Classes:**
- `KaggleResourceType`: Types of Kaggle resources
- `KaggleDataset`: Kaggle dataset information
- `KaggleCompetition`: Kaggle competition information
- `KaggleNotebook`: Kaggle notebook/kernel information
- `KaggleModel`: Kaggle model information
- `KaggleClient`: Kaggle API client for discovering datasets, competitions, notebooks, and models
**Functions:**
- `__init__`: Initialize Kaggle client
- `_init_api`: Initialize Kaggle API client
- `platform_name`
- `is_authenticated`
- `search`: Search Kaggle for datasets, competitions, notebooks, or models
- `_search_datasets`: Search Kaggle datasets
- `_search_competitions`: Search Kaggle competitions
- `_search_notebooks`: Search Kaggle notebooks/kernels
- `_search_models`: Search Kaggle models
- `get_repository`: Get detailed information about a Kaggle dataset
- `get_contents`: Get contents of a directory in the dataset
- `get_file`: Get contents of a specific file
- `clone`: Download dataset to local filesystem
- `get_file_content`: Get content of a file from a Kaggle dataset
- `list_directory`: List files in a Kaggle dataset
- `get_trending_datasets`: Get trending/hot datasets
- `get_active_competitions`: Get active competitions
- `get_trending_notebooks`: Get trending notebooks
- `download_dataset`: Download a Kaggle dataset
- `download_competition_data`: Download competition data files
- `create_kaggle_client`: Factory function to create Kaggle client if credentials are available

### discovery.unified_search
AI Project Synthesizer - Unified Search

Cross-platform repository search with intelligent ranking.
Aggregates results from GitHub, HuggingFace, Kaggle, and more.

**Classes:**
- `UnifiedSearchResult`: Result from unified multi-platform search
- `UnifiedSearch`: Unified search across multiple code hosting platforms
**Functions:**
- `to_dict`: Convert to dictionary for JSON serialization
- `__init__`: Initialize unified search with platform credentials
- `_init_clients`: Initialize platform clients
- `available_platforms`: Get list of available (initialized) platforms
- `search`: Search across multiple platforms
- `_search_platform`: Search a single platform
- `_deduplicate`: Remove duplicate repositories across platforms
- `_rank_results`: Rank results using composite scoring
- `_calculate_score`: Calculate relevance score for a repository
- `_cache_key`: Generate cache key for search parameters
- `clear_cache`: Clear the search cache
- `get_repository`: Get repository info from URL
- `_detect_platform`: Detect platform from URL
- `_extract_repo_id`: Extract repository ID from URL
- `create_unified_search`: Create UnifiedSearch instance with settings from config

### discovery.__init__
AI Project Synthesizer - Discovery Module

This module handles repository discovery across multiple platforms:
- GitHub (via ghapi)
- HuggingFace (via huggingface_hub)
- Kaggle (via kaggle API) - datasets, competitions, notebooks, models
- GitLab (via python-gitlab)
- arXiv (via arxiv)
- Papers with Code (via paperswithcode-client)
- Semantic Scholar (via semanticscholar)


### generation.diagram_generator
AI Project Synthesizer - Diagram Generator

Generates Mermaid diagrams for architecture visualization.

**Classes:**
- `DiagramConfig`: Configuration for diagram generation
- `DiagramGenerator`: Generates Mermaid diagrams for documentation
**Functions:**
- `generate`: Generate diagrams based on configuration
- `_generate_architecture`: Generate architecture diagram
- `_generate_flow`: Generate data flow diagram
- `_generate_components`: Generate component diagram
- `generate_from_codebase`: Auto-generate diagrams by analyzing codebase
- `save_diagrams`: Save diagrams to files

### generation.readme_generator
AI Project Synthesizer - README Generator

Generates high-quality README documentation for projects.
Uses LLM enhancement when available.

**Classes:**
- `ProjectInfo`: Extracted project information
- `ReadmeGenerator`: Generates README
**Functions:**
- `__post_init__`
- `__init__`: Initialize the README generator
- `generate`: Generate README for a project
- `_analyze_project`: Analyze project to extract information
- `_parse_pyproject`: Parse pyproject
- `_parse_setup_py`: Parse setup
- `_parse_package_json`: Parse package
- `_detect_language`: Detect primary programming language
- `_detect_frameworks`: Detect frameworks used in project
- `_detect_license_type`: Detect license type from LICENSE file
- `_generate_content`: Generate README content from project info
- `_generate_badges`: Generate badge markdown
- `_generate_features`: Generate features list
- `_generate_prerequisites`: Generate prerequisites section
- `_generate_installation`: Generate installation instructions
- `_generate_usage`: Generate usage example
- `_generate_structure`: Generate project structure tree
- `_generate_configuration`: Generate configuration section
- `_generate_testing`: Generate testing instructions
- `_generate_documentation_section`: Generate documentation section
- `_generate_contributing`: Generate contributing section
- `_generate_license_section`: Generate license section
- `_enhance_description`: Use LLM to enhance project description

### generation.__init__
AI Project Synthesizer - Generation Layer

Documentation and diagram generation.


### llm.litellm_router
VIBE MCP - LiteLLM Router

Unified LLM access using LiteLLM for routing across 100+ providers.
Implements intelligent routing based on task type, cost, and availability.

Features:
- Unified API for 100+ LLM providers
- Intelligent routing based on task type
- Cost tracking and optimization
- Automatic fallback chains
- Rate limiting and retry logic

Routing Strategy:
- simple → ollama/llama3.1 (free, fast)
- coding → claude-sonnet or deepseek-coder (quality)
- reasoning → claude-opus or o1 (deep thinking)
- fast → groq/llama-70b (<100ms)
- long_context → claude-3.5 or gemini-pro (200K+ context)

Usage:
    router = LiteLLMRouter()

    # Simple completion
    result = await router.complete("Explain this code", task_type="coding")

    # Chat completion
    result = await router.chat([
        {"role": "user", "content": "Build a FastAPI app"}
    ], task_type="coding")

**Classes:**
- `TaskType`: Task types for routing decisions
- `Provider`: Supported LLM providers
- `ModelConfig`: Configuration for a model
- `CompletionResult`: Result from LLM completion
- `RouterConfig`: Configuration for LiteLLM router
- `LiteLLMRouter`: Unified LLM router using LiteLLM
**Functions:**
- `__init__`: Initialize the router
- `_on_success`: Callback for successful completions (cost tracking)
- `_get_model_for_task`: Get the appropriate model for a task type
- `_get_fallback_chain`: Get fallback chain for a model
- `complete`: Generate a completion
- `chat`: Generate a chat completion
- `_call_model`: Call a specific model
- `_fallback_ollama`: Fallback to direct Ollama call when LiteLLM unavailable
- `stream`: Stream a completion
- `get_stats`: Get router statistics
- `get_available_models`: Get list of available models
- `reset_stats`: Reset statistics
- `get_litellm_router`: Get or create global LiteLLM router instance

### llm.lmstudio_client
AI Project Synthesizer - LM Studio Client

Client for local LLM inference using LM Studio.
LM Studio provides an OpenAI-compatible API for local model serving.

**Classes:**
- `CompletionResult`: Result from LLM completion
- `LMStudioClient`: Client for LM Studio local LLM inference
**Functions:**
- `__init__`: Initialize LM Studio client
- `_get_client`: Get or create OpenAI client
- `close`: Close the client
- `is_available`: Check if LM Studio is available
- `list_models`: List available models
- `complete`: Generate completion from prompt
- `analyze_code`: Analyze code with appropriate prompt
- `generate_code`: Generate code from description
- `get_model_info`: Get information about a specific model

### llm.ollama_client
AI Project Synthesizer - Ollama Client

Client for local LLM inference using Ollama.

**Classes:**
- `CompletionResult`: Result from LLM completion
- `OllamaClient`: Client for Ollama local LLM inference
**Functions:**
- `__init__`: Initialize Ollama client
- `_get_client`: Get or create HTTP client
- `close`: Close the HTTP client
- `is_available`: Check if Ollama is available
- `list_models`: List available models
- `complete`: Generate completion from prompt
- `analyze_code`: Analyze code with appropriate prompt
- `generate_code`: Generate code from description

### llmdantic_ai_agent
AI Project Synthesizer - Pydantic AI Integration

Type-safe AI agents using Pydantic AI for:
- Structured outputs
- Validated responses
- Tool calling
- Multi-model support

**Classes:**
- `SearchQuery`: Structured search query
- `ProjectIdea`: Structured project idea
- `ResourceRecommendation`: Recommended resource
- `SynthesisResult`: Project synthesis result
- `ConversationResponse`: Structured conversation response
- `AgentDeps`: Dependencies injected into agents
- `AgentFactory`: Factory for creating configured agents
**Functions:**
- `__post_init__`
- `create_lmstudio_model`: Create LM Studio model (OpenAI-compatible)
- `create_openai_model`: Create OpenAI model
- `create_anthropic_model`: Create Anthropic model
- `search_github`: Search GitHub for repositories
- `search_huggingface`: Search HuggingFace for models and datasets
- `analyze_compatibility`: Analyze compatibility between resources
- `get_project_status`: Get current project status
- `research_project`: Research resources for a project idea
- `synthesize_project`: Plan project synthesis from resources
- `chat`: Chat with the assistant
- `create_agent`: Create a configured agent

### llm.router
AI Project Synthesizer - LLM Router

Intelligent routing between local and cloud LLMs based on task complexity.

**Classes:**
- `ProviderType`: LLM provider types
- `TaskComplexity`: Task complexity levels for routing decisions
- `RoutingDecision`: Result of routing decision
- `LLMRouter`: Intelligent router between local and cloud LLMs
**Functions:**
- `__init__`: Initialize the router
- `check_provider_health`: Check if a provider is available
- `get_best_provider`: Get the best available provider with fallback logic
- `estimate_complexity`: Estimate task complexity from prompt
- `route`: Decide which model to use based on size preference and task complexity
- `complete`: Complete prompt with automatic routing and fallback
- `_cloud_complete`: Cloud completion (placeholder for cloud API integration)

### llm.__init__
AI Project Synthesizer - LLM Orchestration Layer

Manages multiple LLM providers including:
- Local: Ollama, LM Studio, LocalAI, vLLM, Text Generation WebUI, KoboldAI, llama.cpp
- Cloud: OpenAI, Anthropic, Groq, Together, OpenRouter, Mistral, DeepSeek, Cohere, Fireworks


### mcp.memory_tools
VIBE MCP - Memory MCP Tools

MCP server tools for memory management using the enhanced Mem0 integration.
Implements Phase 4.3 of the VIBE MCP roadmap.

Features:
- Add, search, and retrieve memories
- Memory consolidation and insights
- Export functionality
- Multi-agent memory support

**Classes:**
- `AddMemoryRequest`: Request to add a memory
- `SearchMemoryRequest`: Request to search memories
- `ConsolidateRequest`: Request to consolidate memories
- `ExportRequest`: Request to export memories
**Functions:**
- `get_memory_system`: Get or create the global memory system
- `parse_category`: Parse category string to enum
- `add_memory`: Add a new memory to the system
- `search_memory`: Search for memories matching the query
- `get_memory`: Retrieve a specific memory by ID
- `update_memory`: Update an existing memory's content
- `delete_memory`: Delete a memory by ID
- `get_context_for_task`: Get relevant memories for a specific task
- `consolidate_memories`: Consolidate old memories to save space
- `get_memory_insights`: Get insights and analytics about stored memories
- `export_memories`: Export memories to a file
- `get_memory_statistics`: Get comprehensive statistics about the memory system
- `remember_preference`: Remember a user preference
- `remember_error_solution`: Remember an error and its solution
- `remember_code_pattern`: Remember a reusable code pattern
- `get_memory_categories`: Get available memory categories
- `get_memory_stats_resource`: Get current memory statistics as JSON
- `run_server`: Run the Memory MCP server

### mcp_server.server
AI Project Synthesizer - MCP Server

Main entry point for the Model Context Protocol server.
Exposes synthesis tools to any MCP-compatible client.

Supported Clients:
- Windsurf IDE
- Claude Desktop
- VS Code (Continue, Cline extensions)
- Cursor IDE
- LM Studio
- JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)
- Neovim / Vim
- Emacs
- Zed Editor
- Sourcegraph Cody
- Open Interpreter
- Any custom MCP client

Usage:
    python -m src.mcp_server.server

Configuration Examples:

Windsurf (~/.windsurf/mcp_config.json):
    {
        "mcpServers": {
            "ai-project-synthesizer": {
                "command": "python",
                "args": ["-m", "src.mcp_server.server"]
            }
        }
    }

Claude Desktop:
    {
        "mcpServers": {
            "ai-project-synthesizer": {
                "command": "python",
                "args": ["-m", "src.mcp_server.server"],
                "cwd": "/path/to/AI_Synthesizer"
            }
        }
    }

VS Code Continue:
    {
        "mcpServers": [{
            "name": "ai-project-synthesizer",
            "command": "python",
            "args": ["-m", "src.mcp_server.server"]
        }]
    }

See docs/MCP_CLIENT_SUPPORT.md for full configuration guide.

**Functions:**
- `list_tools`: List all available MCP tools
- `call_tool`: Handle tool calls from Windsurf
- `main`: Main entry point for the MCP server
- `shutdown_mcp_server`: Shutdown MCP server gracefully

### mcp_server.tools
AI Project Synthesizer - MCP Tool Handlers

Implementation of all MCP tool handlers.
These handle the actual business logic for each tool.

**Functions:**
- `get_synthesis_job`: Thread-safe getter for synthesis job
- `set_synthesis_job`: Thread-safe setter for synthesis job
- `update_synthesis_job`: Thread-safe update for synthesis job
- `get_unified_search`: Get or create unified search instance
- `get_dependency_analyzer`: Get or create dependency analyzer instance
- `handle_search_repositories`: Handle repository search across platforms
- `handle_analyze_repository`: Handle deep repository analysis
- `handle_check_compatibility`: Handle compatibility check between repositories
- `handle_resolve_dependencies`: Handle dependency resolution across repositories
- `handle_synthesize_project`: Handle project synthesis from multiple repositories
- `_update_job`: Update synthesis job progress (thread-safe)
- `handle_generate_documentation`: Handle documentation generation for a project
- `handle_get_synthesis_status`: Handle status query for synthesis operations
- `search_repositories`: Search for repositories across platforms
- `analyze_repository`: Analyze a repository
- `check_compatibility`: Check compatibility between repositories
- `resolve_dependencies`: Resolve dependencies across repositories
- `synthesize_project`: Synthesize a project from multiple repositories
- `generate_documentation`: Generate documentation for a project
- `get_synthesis_status`: Get the status of a synthesis operation
- `get_platforms`: Get available platforms for repository search
- `get_assistant`: Get or create assistant instance
- `handle_assistant_chat`: Chat with the AI assistant
- `handle_assistant_voice`: Generate voice audio for text AND auto-play it
- `handle_assistant_toggle_voice`: Toggle voice on/off for the assistant
- `handle_get_voices`: Get available voices for text-to-speech
- `handle_speak_fast`: FAST streaming voice - optimized for speed and smooth playback
- `handle_assemble_project`: Assemble a complete project from an idea
- `register_all_tools`: Register all tool handlers with the MCP server
- `register_all_resources`: Register all resources with the MCP server
- `register_all_prompts`: Register all prompts with the MCP server

### mcp_server.__init__
AI Project Synthesizer - MCP Server Package

Model Context Protocol server for Windsurf IDE integration.


### memory.mem0_integration
VIBE MCP - Mem0 Integration

Advanced memory system using Mem0 for persistent, intelligent context retention.
Implements the "vibe coding" principle of learning from user interactions.

Features:
- Multi-category memory storage
- Semantic search across memories
- Context retrieval for tasks
- Memory decay and relevance scoring
- Fallback to local storage if Mem0 unavailable

Memory Categories:
- PREFERENCE: User preferences (style, tools, frameworks)
- DECISION: Project decisions (architecture, tech stack)
- PATTERN: Code patterns (reusable components, idioms)
- ERROR_SOLUTION: Error fixes that worked
- CONTEXT: General project context

Usage:
    memory = MemorySystem()

    # Remember user preferences
    await memory.remember_preference("User prefers tabs over spaces")

    # Remember error solutions
    await memory.remember_error_solution(
        error="ModuleNotFoundError: cv2",
        solution="pip install opencv-python"
    )

    # Get relevant context for a task
    context = await memory.get_context_for_task("build a FastAPI app")

**Classes:**
- `MemoryCategory`: Categories for organizing memories
- `MemoryEntry`: A single memory entry
- `MemoryConfig`: Configuration for memory system
- `LocalMemoryStore`: Local fallback memory storage using JSON files
- `MemorySystem`: Advanced memory system for VIBE MCP
**Functions:**
- `memory_type`: Map category to memory type
- `to_dict`: Convert to dictionary
- `from_dict`: Create from dictionary
- `__init__`: Initialize local storage
- `_get_storage_file`: Get the storage file path
- `_load`: Load memories from disk
- `_save`: Save memories to disk
- `_generate_id`: Generate a unique ID for content
- `add`: Add a memory
- `search`: Search memories (simple keyword matching for local store)
- `get`: Get a specific memory
- `update`: Update a memory
- `delete`: Delete a memory
- `get_by_category`: Get all memories in a category
- `get_all`: Get all memories
- `clear`: Clear all memories
- `__init__`: Initialize memory system
- `_initialize`: Initialize the appropriate storage backend
- `is_mem0_active`: Check if Mem0 is the active backend
- `add`: Add a memory
- `search`: Search memories
- `get`: Get a specific memory by ID
- `update`: Update a memory
- `delete`: Delete a memory
- `get_all`: Get all memories, optionally filtered by category
- `remember_preference`: Remember a user preference
- `remember_decision`: Remember a project decision
- `remember_pattern`: Remember a code pattern
- `remember_error_solution`: Remember an error and its solution
- `remember_component`: Remember a reusable component
- `remember_learning`: Remember something learned during a session
- `get_context_for_task`: Get relevant context for a task
- `get_user_preferences`: Get all user preferences
- `get_error_solutions`: Get error solutions, optionally filtered by query
- `consolidate_memories`: Consolidate old memories to save space and improve relevance
- `get_memory_insights`: Get detailed insights about stored memories
- `export_memories`: Export memories to a file
- `_invalidate_cache`: Invalidate cache entries
- `_check_consolidation`: Check if consolidation is needed for a category
- `get_stats`: Get memory system statistics
- `get_memory_system`: Get or create global memory system instance
- `create_memory_system`: Create and initialize memory system with enhanced features

### memory.__init__
VIBE MCP - Memory Module

Persistent memory system using Mem0 for intelligent context retention.
Enables agents to remember user preferences, project decisions, code patterns,
and error solutions across sessions.

Components:
- mem0_integration: Core Mem0 wrapper with enhanced features
- memory_types: Memory categories and schemas

Usage:
    from src.memory import MemorySystem, MemoryCategory

    memory = MemorySystem()

    # Add memories
    await memory.add("User prefers FastAPI over Flask", category=MemoryCategory.PREFERENCE)

    # Search memories
    results = await memory.search("what framework does user prefer")

    # Get context for a task
    context = await memory.get_context_for_task("build an API")


### platform.browser_automation
Browser Automation for VIBE MCP

Comprehensive browser automation using Playwright:
- Page navigation and interaction
- Screenshot capture and comparison
- Form filling and submission
- Web scraping with JavaScript execution
- Testing and validation
- Performance monitoring

Integrates with GitLab (MR testing) and Firecrawl (enhanced scraping).

**Classes:**
- `BrowserType`: Supported browser types
- `ViewportSize`: Common viewport sizes
- `ScreenshotOptions`: Screenshot capture options
- `FormField`: Form field definition
- `PageAction`: Page action definition
- `BrowserSession`: Browser session information
- `BrowserAutomation`: Advanced browser automation with Playwright
**Functions:**
- `__init__`: Initialize browser automation
- `__aenter__`: Async context manager entry
- `__aexit__`: Async context manager exit
- `start`: Start the browser and create a new session
- `close`: Close the browser and cleanup
- `_setup_monitoring`: Setup network and performance monitoring
- `on_request`
- `on_response`
- `navigate`: Navigate to a URL
- `wait_for_load_state`: Wait for specific load state
- `wait_for_selector`: Wait for element to appear
- `screenshot`: Capture screenshot
- `screenshot_element`: Capture screenshot of specific element
- `fill_form`: Fill a form with multiple fields
- `click`: Click on an element
- `type_text`: Type text into an element
- `press_key`: Press a keyboard key
- `scroll_to`: Scroll the page
- `scroll_to_element`: Scroll to specific element
- `evaluate_script`: Execute JavaScript in page context
- `get_element_text`: Get text content of element
- `get_element_attribute`: Get attribute value of element
- `get_page_content`: Get the full page HTML content
- `get_performance_metrics`: Get performance metrics for the current page
- `wait_for_network_idle`: Wait for network to be idle
- `set_user_agent`: Set custom user agent
- `set_cookies`: Set cookies for the current context
- `get_cookies`: Get all cookies
- `clear_network_logs`: Clear network request/response logs
- `create_browser_automation`: Create and initialize browser automation
- `main`

### platform.__init__
VIBE MCP Platform Integrations

This module implements platform-specific integrations:
- Browser automation with Playwright
- Enhanced GitLab client features
- Improved Firecrawl web scraping
- Additional platform tools

Components:
- BrowserAutomation: Playwright-based browser control
- Enhanced GitLab: MR automation, CI/CD integration
- Enhanced Firecrawl: Better scraping with caching


### plugins.example_plugin
Example Plugin - GitLab Integration

This is an example plugin showing how to add a new platform.
Copy this as a template for your own plugins.

**Classes:**
- `GitLabPlugin`: GitLab repository search plugin
**Functions:**
- `metadata`
- `initialize`: Initialize with GitLab credentials
- `search`: Search GitLab repositories
- `get_details`: Get repository details
- `download`: Clone GitLab repository

### plugins.__init__
AI Project Synthesizer - Built-in Plugins

This directory contains built-in plugins that extend functionality.


### quality.dependency_scanner
Dependency Scanner for VIBE MCP

Scans project dependencies for security vulnerabilities:
- Multiple package manager support (pip, npm, yarn, poetry, etc.)
- CVE database integration
- Vulnerability severity assessment
- Auto-fix suggestions
- Integration with QualityGate

Provides comprehensive dependency security analysis.

**Classes:**
- `PackageManager`: Supported package managers
- `SeverityLevel`: Vulnerability severity levels
- `Vulnerability`: Represents a security vulnerability
- `DependencyReport`: Report of dependency scan results
- `DependencyScanner`: Scans project dependencies for vulnerabilities
**Functions:**
- `__init__`
- `scan`: Scan all dependencies in the project
- `_detect_package_managers`: Detect which package managers are used in the project
- `_scan_pip`: Scan Python pip dependencies
- `_scan_poetry`: Scan Python Poetry dependencies
- `_scan_npm`: Scan Node
- `_scan_yarn`: Scan Node
- `_scan_pipenv`: Scan Pipenv dependencies
- `_scan_gradle`: Scan Gradle dependencies
- `_scan_maven`: Scan Maven dependencies
- `_scan_cargo`: Scan Rust Cargo dependencies
- `_scan_go_mod`: Scan Go modules dependencies
- `_scan_composer`: Scan PHP Composer dependencies
- `_parse_severity`: Parse severity string to enum
- `_generate_summary`: Generate vulnerability summary
- `_generate_recommendations`: Generate fix recommendations
- `calculate_risk_score`: Calculate overall risk score from all reports
- `get_most_critical`: Get the most critical vulnerabilities across all reports
- `main`

### quality.lint_checker
Lint Checker for VIBE MCP Quality Pipeline

Integrates with multiple linting tools:
- Ruff: Fast Python linter and formatter
- ESLint: JavaScript/TypeScript linting
- MyPy: Static type checking for Python
- Prettier: Code formatting verification

This ensures all generated code follows consistent style and type safety.

**Classes:**
- `LintLevel`: Lint issue severity levels
- `LintIssue`: Represents a linting issue found
- `LintResult`: Result of a lint check
- `LintChecker`: Comprehensive lint checking for generated code
**Functions:**
- `__init__`
- `check_code`: Check code with appropriate linting tools
- `_check_with_ruff`: Run Ruff Python linter
- `_check_with_mypy`: Run MyPy type checker
- `_check_with_eslint`: Run ESLint for JavaScript/TypeScript
- `_check_with_prettier`: Check code formatting with Prettier
- `_map_ruff_level`: Map Ruff fix availability to lint level
- `_map_eslint_level`: Map ESLint severity to lint level
- `_get_mypy_fix_suggestion`: Get fix suggestion for MyPy error
- `fix_code`: Auto-fix linting issues in code
- `generate_report`: Generate a human-readable lint report
- `install_tools`: Install required linting tools
- `main`

### quality.quality_gate
Quality Gate for VIBE MCP Quality Pipeline

Orchestrates all quality checks:
- SecurityScanner: Security vulnerability detection
- LintChecker: Code style and linting
- TestGenerator: Test coverage generation
- ReviewAgent: Multi-agent code review

Provides unified pass/fail decisions with auto-fix capabilities.

**Classes:**
- `GateStatus`: Quality gate status
- `FixStatus`: Auto-fix status
- `QualityMetrics`: Quality metrics for the gate
- `GateResult`: Result of quality gate evaluation
- `QualityGate`: Unified quality gate for VIBE MCP
**Functions:**
- `__post_init__`
- `__init__`
- `evaluate`: Evaluate code against all quality checks
- `_run_all_checks`: Run all quality checks in parallel
- `_calculate_metrics`: Calculate quality metrics from results
- `_check_pass_criteria`: Check if code passes all quality criteria
- `_apply_auto_fixes`: Apply automatic fixes where possible
- `_get_blocked_issues`: Get issues that block deployment
- `evaluate_directory`: Evaluate all files in a directory
- `generate_report`: Generate a comprehensive quality gate report
- `_get_status_emoji`: Get emoji for status
- `save_report`: Save detailed report to JSON file
- `install_tools`: Install all required quality tools
- `main`

### quality.review_agent
Review Agent for VIBE MCP Quality Pipeline

Uses AutoGen to create multi-agent code review debates:
- SecurityExpert: Reviews for security vulnerabilities
- QualityChecker: Reviews code quality and maintainability
- PerformanceAnalyst: Reviews performance implications
- LeadReviewer: Moderates and synthesizes final review

This ensures comprehensive code review before deployment.

**Classes:**
- `ReviewSeverity`: Severity levels for review issues
- `ReviewStatus`: Review status
- `ReviewIssue`: Represents an issue found during code review
- `ReviewReport`: Complete code review report
- `ReviewAgent`: Multi-agent code review system using AutoGen
**Functions:**
- `__init__`
- `review_code`: Conduct multi-agent code review
- `_initialize_agents`: Initialize AutoGen agents for review
- `_conduct_individual_reviews`: Get initial reviews from each specialist agent
- `_conduct_debate_and_synthesis`: Conduct moderated debate to reach consensus
- `_parse_review_report`: Parse the final review into a structured report
- `review_pull_request`: Review an entire pull request with multiple files
- `generate_report`: Generate a human-readable review report
- `apply_fixes`: Attempt to automatically fix some issues
- `main`

### quality.security_scanner
Security Scanner for VIBE MCP Quality Pipeline

Integrates with multiple security scanning tools:
- Semgrep: Static analysis for security vulnerabilities
- Bandit: Python-specific security issues
- Custom rules: VIBE MCP specific security patterns

This scanner automatically checks all generated code before deployment.

**Classes:**
- `SeverityLevel`: Security issue severity levels
- `SecurityIssue`: Represents a security vulnerability found
- `ScanResult`: Result of a security scan
- `SecurityScanner`: Comprehensive security scanning for generated code
**Functions:**
- `__init__`
- `_load_custom_rules`: Load VIBE MCP specific security rules
- `scan_code`: Scan code with all security tools
- `_scan_with_semgrep`: Run Semgrep security scan
- `_scan_with_bandit`: Run Bandit Python security scan
- `_scan_with_custom_rules`: Scan with VIBE MCP custom rules
- `_map_semgrep_severity`: Map Semgrep severity to our enum
- `_map_bandit_severity`: Map Bandit severity to our enum
- `_get_fix_suggestion`: Get fix suggestion for custom rule
- `scan_directory`: Scan an entire directory for security issues
- `generate_report`: Generate a human-readable security report
- `install_tools`: Install required security scanning tools
- `main`

### quality.test_generator
Test Generator for VIBE MCP Quality Pipeline

Automatically generates unit tests for generated code using:
- AST parsing to extract code structure
- LiteLLM router for intelligent test generation
- pytest for Python, jest for JavaScript/TypeScript
- Edge case detection and coverage analysis

This ensures all generated code has comprehensive test coverage.

**Classes:**
- `TestType`: Types of tests to generate
- `TestFunction`: Represents a generated test function
- `TestSuite`: Represents a complete test suite
- `TestGenerator`: Intelligent test generation for VIBE MCP
- `TestGenerationError`: Raised when test generation fails
**Functions:**
- `__init__`
- `generate_tests`: Generate comprehensive test suite for code
- `_generate_python_tests`: Generate pytest tests for Python code
- `_generate_js_tests`: Generate jest tests for JavaScript/TypeScript
- `_extract_function_info`: Extract information from a Python function AST node
- `_extract_class_info`: Extract information from a Python class AST node
- `_extract_js_functions`: Extract JavaScript functions using regex
- `_extract_js_classes`: Extract JavaScript classes using regex
- `_extract_class_body`: Extract class body from position
- `_detect_function_patterns`: Detect common patterns in function
- `_generate_function_tests`: Generate tests for a specific function using LLM
- `_generate_fallback_tests`: Generate basic tests as fallback
- `_determine_python_imports`: Determine required imports for Python tests
- `_determine_js_imports`: Determine required imports for JS tests
- `_generate_python_setup`: Generate setup code for Python tests
- `_generate_js_setup`: Generate setup code for JS tests
- `_estimate_coverage`: Estimate test coverage based on generated tests
- `write_test_file`: Write test suite to file
- `run_tests`: Run generated tests and return results
- `generate_report`: Generate a human-readable test report
- `main`

### quality.__init__
VIBE MCP Quality Pipeline

This module implements the Security & Quality Pipeline:
- Security vulnerability scanning
- Code linting and style checking
- Automated test generation
- Code review automation
- Dependency vulnerability scanning
- Quality gate enforcement

Components:
- SecurityScanner: Static security analysis (Semgrep, Bandit)
- LintChecker: Code style and quality checks (Ruff, ESLint, mypy)
- TestGenerator: Automated test generation (pytest, jest)
- ReviewAgent: Multi-agent code review (AutoGen)
- QualityGate: Unified quality decisions and auto-fix
- DependencyScanner: Package dependency vulnerability scanning


### recipes.loader
Recipe Loader - Load and validate recipe files.

**Classes:**
- `RecipeSource`: A source repository in a recipe
- `RecipeSynthesis`: Synthesis configuration for a recipe
- `Recipe`: A complete recipe definition
- `RecipeLoader`: Load recipes from the recipes directory
**Functions:**
- `from_dict`: Create a Recipe from a dictionary
- `__init__`: Initialize the recipe loader
- `list_recipes`: List all available recipes
- `load_recipe`: Load a recipe by name
- `validate_recipe`: Validate a recipe and return any errors

### recipes.runner
Recipe Runner - Execute recipes to create projects.

**Classes:**
- `RecipeResult`: Result of running a recipe
- `RecipeRunner`: Execute recipes to create projects
**Functions:**
- `__init__`: Initialize the recipe runner
- `run`: Run a recipe to create a project
- `_process_source`: Process a single source repository
- `_run_post_step`: Run a post-synthesis step

### recipes.__init__
AI Synthesizer Recipe System

Pre-configured project templates for common use cases.


### resolution.conflict_detector
AI Project Synthesizer - Conflict Detector

Detects and analyzes dependency conflicts between repositories.

**Classes:**
- `ConflictInfo`: Detailed information about a conflict
- `ConflictReport`: Complete conflict analysis report
- `ConflictDetector`: Detects dependency conflicts between multiple dependency graphs
**Functions:**
- `has_blocking_conflicts`: Check for unresolvable conflicts
- `to_dict`: Convert to dictionary
- `detect`: Detect conflicts between dependency graphs
- `_check_version_conflict`: Check for version conflicts
- `_check_extras_conflict`: Check for extras conflicts (just informational)
- `_ranges_compatible`: Check if version ranges might be compatible
- `_version_greater`: Check if v1 > v2
- `to_tuple`

### resolutionthon_resolver
AI Project Synthesizer - Python Resolver

Resolves Python dependencies using uv or pip-tools.
Handles version conflicts with SAT solver.

**Classes:**
- `ResolvedPackage`: A resolved package with exact version
- `ResolutionResult`: Result of dependency resolution
- `PythonResolver`: Python dependency resolver using uv SAT solver
**Functions:**
- `to_requirement`: Convert to requirements
- `to_dict`: Convert to dictionary
- `__init__`: Initialize the Python resolver
- `_check_uv`: Check if uv is available
- `_check_pip_compile`: Check if pip-compile is available
- `resolve`: Resolve dependencies to exact versions
- `_resolve_with_uv`: Resolve using uv
- `_resolve_with_pip_compile`: Resolve using pip-compile
- `_simple_resolve`: Simple resolution without SAT solver
- `_parse_lockfile`: Parse lockfile content into packages
- `_parse_conflicts`: Parse conflict information from error message
- `check_conflicts`: Check for potential conflicts without full resolution

### resolution.unified_resolver
AI Project Synthesizer - Unified Resolver

Orchestrates dependency resolution across multiple repositories.
Merges requirements and resolves conflicts using appropriate resolvers.

**Classes:**
- `UnifiedResolutionResult`: Result of unified dependency resolution
- `UnifiedResolver`: Unified dependency resolver for multiple repositories
**Functions:**
- `to_dict`: Convert to dictionary
- `__init__`: Initialize the unified resolver
- `resolve`: Resolve dependencies from multiple repositories
- `_extract_dependencies`: Extract dependencies from a repository
- `_extract_from_url`: Extract dependencies from a remote repository
- `_extract_from_path`: Extract dependencies from a local repository path
- `resolve_from_graphs`: Resolve from pre-analyzed dependency graphs
- `generate_pyproject_toml`: Generate pyproject

### resolution.__init__
AI Project Synthesizer - Resolution Layer

Dependency resolution using uv/pip-tools for Python and npm for Node.js.


### synthesis.project_assembler
AI Project Synthesizer - Automated Project Assembler

THE ULTIMATE GOAL:
1. Find compatible projects across GitHub, HuggingFace, Kaggle
2. Download everything: code, models (.safetensors), datasets
3. Create organized folder structure on G:4. Generate combined requirements.txt
5. Create GitHub repo for user
6. Prepare project for Windsurf IDE to finish

This is the BRAIN that assembles complete projects automatically.

**Classes:**
- `ProjectResource`: A resource to be included in the project
- `AssembledProject`: A fully assembled project ready for development
- `AssemblerConfig`: Configuration for project assembly
- `ProjectAssembler`: Automated project assembler
**Functions:**
- `__init__`: Initialize assembler
- `_init_credentials`: Load credentials
- `assemble`: Assemble a complete project from an idea
- `_generate_project_name`: Generate a project name from idea
- `_slugify`: Convert name to URL-safe slug
- `_create_folder_structure`: Create project folder structure
- `_search_resources`: Search for resources across all platforms
- `_search_arxiv`: Search arXiv for research papers
- `_download_all`: Download all resources
- `_download_github_repo`: Clone a GitHub repository
- `_download_huggingface_model`: Download a HuggingFace model
- `_download_kaggle_dataset`: Download a Kaggle dataset
- `_download_paper`: Download a research paper PDF
- `_generate_project_files`: Generate project files (README, requirements, etc
- `_generate_readme`: Generate README
- `_collect_requirements`: Collect requirements from all repos
- `_generate_gitignore`: Generate 
- `_generate_windsurf_config`: Generate Windsurf IDE configuration
- `_create_github_repo`: Create a GitHub repository for the project
- `_init_and_push_git`: Initialize git and push to GitHub
- `_save_manifest`: Save project manifest for future reference
- `assemble_project`: Quick function to assemble a project

### synthesis.project_builder
AI Project Synthesizer - Project Builder

Orchestrates the complete project synthesis pipeline.
Combines discovery, analysis, resolution, and generation.

**Classes:**
- `SynthesisStatus`: Status of a synthesis operation
- `ExtractionSpec`: Specification for extracting code from a repository
- `SynthesisRequest`: Request for project synthesis
- `SynthesisResult`: Result of synthesis operation
- `BuildResult`: Result from the build method (used by MCP tools)
- `ProjectBuilder`: Orchestrates project synthesis from multiple repositories
**Functions:**
- `to_dict`: Convert to dictionary
- `__init__`: Initialize project builder
- `synthesize`: Execute full synthesis pipeline
- `_validate_request`: Validate synthesis request
- `_discover_repositories`: Discover repositories based on query
- `_analyze_repositories`: Analyze all repositories
- `_resolve_dependencies`: Resolve dependencies across all repositories
- `_synthesize_code`: Synthesize code from repositories
- `_write_dependencies`: Write dependency files
- `_generate_documentation`: Generate project documentation
- `_generate_readme`: Generate README content
- `get_status`: Get status of a synthesis operation
- `list_active`: List all active synthesis operations
- `build`: Build a project from repository specifications

### synthesis.scaffolder
AI Project Synthesizer - Scaffolder

Project template scaffolding using standard project structures.

**Classes:**
- `ScaffoldResult`: Result of scaffolding operation
- `Scaffolder`: Project scaffolder for creating standard project structures
**Functions:**
- `scaffold`: Apply project template scaffolding
- `_generate_gitignore`: Generate 
- `_generate_readme`: Generate README
- `_generate_pyproject`: Generate pyproject
- `_generate_docker`: Generate Docker configuration
- `_generate_ci`: Generate CI configuration

### synthesis.__init__
AI Project Synthesizer - Synthesis Layer

Code merging, project scaffolding, and synthesis operations.


### tui.app
AI Project Synthesizer - Terminal UI Application

Rich-based TUI for full system control:
- Dashboard view
- Settings management
- Agent control
- Workflow monitoring
- Real-time logs

**Classes:**
- `SynthesizerTUI`: Terminal UI for AI Project Synthesizer
**Functions:**
- `__init__`
- `clear`: Clear terminal
- `header`: Display header
- `main_menu`: Display main menu and get choice
- `dashboard_view`: Display dashboard with system status
- `search_view`: Search for resources
- `assemble_view`: Assemble a new project
- `agents_view`: Agent control panel
- `_run_research_agent`: Run research agent
- `_run_synthesis_agent`: Run synthesis agent
- `_run_code_agent`: Run code agent
- `_run_automation_agent`: Run automation agent
- `settings_view`: Settings management
- `metrics_view`: View metrics
- `workflows_view`: Workflow management
- `chat_view`: Interactive chat
- `run`: Run the TUI
- `run_tui`: Run the terminal UI

### tui.wizard
AI Synthesizer Wizard Mode

Interactive guided project creation wizard.

**Classes:**
- `ProjectWizard`: Interactive wizard for creating projects
**Functions:**
- `__init__`: Initialize the wizard
- `run`: Run the interactive wizard
- `_step_project_type`: Step 1: Select project type
- `_step_project_name`: Step 2: Enter project name
- `_step_tech_stack`: Step 3: Confirm/customize tech stack
- `_step_example_repos`: Step 4: Add example repositories
- `_step_output_location`: Step 5: Select output location
- `_step_confirm`: Step 6: Confirm and create
- `run_wizard`: Run the project wizard and return configuration
- `execute_wizard_config`: Execute the wizard configuration to create a project

### tui.__init__
AI Project Synthesizer - Terminal UI

Rich-based terminal interface for full control without browser.


### utils.rate_limiter
AI Project Synthesizer - Rate Limiter

Token bucket rate limiter for API calls.
Supports both synchronous and asynchronous usage.

**Classes:**
- `RateLimitState`: State of a rate limiter
- `RateLimiter`: Token bucket rate limiter
- `MultiRateLimiter`: Manages rate limiters for multiple endpoints
- `AdaptiveRateLimiter`: Rate limiter that adapts based on API responses
**Functions:**
- `__init__`: Initialize rate limiter
- `tokens`: Current available tokens
- `state`: Get current state
- `_refill`: Refill tokens based on elapsed time
- `acquire`: Acquire tokens, waiting if necessary
- `try_acquire`: Try to acquire tokens without waiting
- `time_until_available`: Calculate time until tokens will be available
- `reset`: Reset rate limiter to initial state
- `get_stats`: Get rate limiter statistics
- `__init__`
- `add_limiter`: Add a rate limiter for an endpoint
- `acquire`: Acquire tokens for an endpoint
- `try_acquire`: Try to acquire tokens for an endpoint
- `__init__`
- `report_success`: Report successful request
- `report_rate_limited`: Report rate limit hit
- `set_rate_from_headers`: Set rate based on API headers
- `_update_rate`: Update internal rate

### utils.__init__
AI Project Synthesizer - Utilities

Shared utility functions and helpers.


### vibe.architect_agent
Architect Agent for VIBE MCP

Creates high-level architectural plans before coding:
- Analyzes requirements for architectural patterns
- Generates component diagrams
- Defines data flows and interfaces
- Identifies technology choices
- Provides structured plans for TaskDecomposer

Runs before TaskDecomposer to provide architectural context.

**Classes:**
- `ArchitecturePattern`: Common architectural patterns
- `Component`: Represents a system component
- `DataFlow`: Represents data flow between components
- `ArchitecturePlan`: Complete architectural plan
- `ArchitectAgent`: Creates architectural plans for development tasks
**Functions:**
- `__init__`
- `create_architecture`: Create an architectural plan based on requirements
- `_detect_pattern`: Detect the most suitable architectural pattern
- `_generate_architectural_plan`: Generate detailed architectural plan using LLM
- `_create_basic_plan`: Create a basic fallback plan
- `_generate_diagram`: Generate an ASCII/Mermaid diagram of the architecture
- `_generate_rest_diagram`: Generate REST API architecture diagram
- `_generate_microservices_diagram`: Generate microservices architecture diagram
- `_generate_mvc_diagram`: Generate MVC architecture diagram
- `_generate_generic_diagram`: Generate generic architecture diagram
- `get_component_by_id`: Get a component by its ID
- `get_components_by_type`: Get all components of a specific type
- `validate_plan`: Validate an architectural plan and return issues
- `_has_circular_dependency`: Check if a component has circular dependencies
- `export_plan`: Export architectural plan to file
- `create_markdown_report`: Create a markdown report of the architectural plan
- `main`

### vibe.auto_commit
Auto Commit for VIBE MCP

Automatically commits changes after each phase:
- Git integration for version control
- Configurable commit strategies
- Phase-based commit messages
- Change detection and staging
- Integration with ContextManager

Provides reliable version control for structured processes.

**Classes:**
- `CommitStrategy`: Strategies for automatic commits
- `CommitStatus`: Status of a commit operation
- `CommitInfo`: Information about a commit
- `CommitConfig`: Configuration for auto-commit behavior
- `AutoCommit`: Handles automatic Git commits for task phases
**Functions:**
- `__post_init__`
- `__init__`
- `_find_repo_root`: Find the Git repository root
- `_run_git_command`: Run a Git command
- `_get_changed_files`: Get list of files changed since last phase commit
- `_match_pattern`: Check if file matches ignore pattern
- `_stage_changes`: Stage specific files for commit
- `_get_diff_stats`: Get addition and deletion counts for staged changes
- `_create_commit_message`: Create a structured commit message for a phase
- `commit_phase`: Commit changes for a completed phase
- `_push_changes`: Push changes to remote repository
- `create_feature_branch`: Create a feature branch for the task
- `get_commit_history`: Get commit history
- `rollback_to_commit`: Rollback to a specific commit
- `get_status`: Get current repository status
- `save_config`: Save configuration to file
- `load_config`: Load configuration from file
- `main`

### vibe.auto_rollback
Auto Rollback for VIBE MCP

Automatically rolls back to last successful checkpoint on failures:
- Multiple rollback strategies (Git, file system, state)
- Integration with ContextManager checkpoints
- Configurable rollback modes (auto, interactive, dry-run)
- Rollback pattern tracking for learning
- Failure analysis and prevention

Provides robust error recovery for the Vibe Coding pipeline.

**Classes:**
- `RollbackStrategy`: Available rollback strategies
- `RollbackMode`: Rollback execution modes
- `RollbackStatus`: Status of a rollback operation
- `RollbackPoint`: A point in time that can be rolled back to
- `RollbackResult`: Result of a rollback operation
- `AutoRollback`: Automatic rollback system for phase failures
**Functions:**
- `__init__`
- `_detect_git_repo`: Check if current directory is a Git repository
- `create_rollback_point`: Create a rollback point before executing a phase
- `rollback_on_failure`: Perform rollback when a phase fails
- `_execute_rollback`: Execute the actual rollback
- `_backup_git_state`: Backup current Git state
- `_rollback_git`: Rollback Git state
- `_backup_files`: Backup files to rollback directory
- `_rollback_files`: Restore files from backup
- `_get_tracked_files`: Get list of tracked files in the project
- `_get_current_branch`: Get current Git branch
- `_dry_run_rollback`: Perform a dry run rollback showing what would be done
- `_confirm_rollback`: Ask user to confirm rollback
- `_save_rollback_point`: Save rollback point to disk and memory
- `_get_latest_rollback_point`: Get the latest rollback point for a task/phase
- `_track_failure_pattern`: Track failure patterns for learning
- `get_rollback_history`: Get rollback history
- `set_mode`: Change rollback mode
- `cleanup_old_backups`: Clean up old backup files
- `main`

### vibe.context_injector
Context Injector for VIBE MCP

Provides project context for prompt enhancement:
- Project state and configuration
- Component references and relationships
- Past decisions and patterns
- Current working directory context
- Git status and recent changes

Integrates with Mem0 to learn from project history.

**Classes:**
- `ProjectContext`: Complete project context for prompt enhancement
- `ContextInjector`: Injects relevant project context into prompts
**Functions:**
- `__init__`
- `get_context`: Get comprehensive project context
- `_build_context`: Build project context from various sources
- `_detect_project_type`: Detect project type and tech stack
- `_get_project_name`: Get project name from directory or config
- `_get_current_state`: Get description of current project state
- `_discover_components`: Discover project components
- `_get_past_decisions`: Get relevant past decisions from memory
- `_get_recent_changes`: Get recent file changes
- `_get_recent_files`: Get files modified in the last N hours
- `_get_environment_info`: Get current environment information
- `_get_git_status`: Get git repository status
- `_is_new_project`: Check if this appears to be a new project
- `_get_cache_key`: Generate cache key based on current directory
- `add_decision`: Add a project decision to memory
- `clear_cache`: Clear the context cache
- `main`

### vibe.context_manager
Context Manager for VIBE MCP

Tracks state across task phases:
- Phase state persistence
- Checkpoint creation and restoration
- Progress tracking
- Context inheritance between phases
- Integration with Mem0 for long-term storage

Provides reliable state management for structured processes.

**Classes:**
- `PhaseStatus`: Status of a phase in the task
- `PhaseState`: State information for a single phase
- `TaskContext`: Complete context for a task execution
- `Checkpoint`: A saved state that can be restored
- `ContextManager`: Manages context and state across task phases
**Functions:**
- `__post_init__`
- `__post_init__`
- `__init__`
- `create_context`: Create a new task context
- `get_context`: Get task context, loading from persistence if needed
- `start_phase`: Start a phase in the task
- `complete_phase`: Mark a phase as completed
- `fail_phase`: Mark a phase as failed
- `create_checkpoint`: Create a checkpoint of the current state
- `restore_checkpoint`: Restore task to a previous checkpoint
- `get_progress`: Get progress information for a task
- `_estimate_completion`: Estimate task completion time
- `_save_context`: Save context to Mem0
- `_load_context`: Load context from Mem0
- `_save_checkpoint`: Save checkpoint to Mem0
- `_load_checkpoint`: Load checkpoint from Mem0
- `cleanup`: Clean up task context and checkpoints
- `main`

### vibe.explain_mode
Explain Mode for VIBE MCP

Provides explanations for code decisions and changes:
- Code decision explanations
- Change impact analysis
- Implementation reasoning
- Best practice justifications
- Learning from explanations

Helps users understand why certain decisions were made.

**Classes:**
- `ExplanationType`: Types of explanations
- `ExplanationLevel`: Detail levels for explanations
- `CodeChange`: Represents a code change
- `Explanation`: An explanation of code decisions
- `ExplainMode`: Provides explanations for code decisions and changes
**Functions:**
- `__init__`
- `explain_code_change`: Explain a code change
- `explain_architectural_decision`: Explain an architectural decision
- `explain_refactoring`: Explain a refactoring decision
- `_classify_change`: Classify the type of change for explanation
- `_generate_explanation`: Generate explanation using LLM
- `_generate_architectural_explanation`: Generate architectural decision explanation
- `_generate_refactoring_explanation`: Generate refactoring explanation
- `_parse_text_explanation`: Parse text explanation into structured format
- `_analyze_refactoring`: Analyze what changed in a refactoring
- `_save_explanation`: Save explanation to memory for learning
- `get_explanation_history`: Get explanation history
- `create_explanation_report`: Create a markdown report of explanations
- `main`

### vibe.project_classifier
Project Classifier for VIBE MCP

Automatically detects project patterns and characteristics:
- Project type classification
- Technology stack detection
- Architecture pattern recognition
- Complexity assessment
- Best practice recommendations

Helps Vibe Coding make informed decisions based on project context.

**Classes:**
- `ProjectType`: Common project types
- `ComplexityLevel`: Project complexity levels
- `ArchitecturePattern`: Common architecture patterns
- `TechnologyStack`: Detected technology stack
- `ProjectCharacteristics`: Characteristics of the project
- `ProjectClassifier`: Automatically classifies projects and detects patterns
**Functions:**
- `__init__`
- `classify_project`: Classify the project at the given path
- `_get_project_files`: Get all relevant project files
- `_analyze_structure`: Analyze project structure and size
- `_detect_technology_stack`: Detect the technology stack
- `_detect_patterns`: Detect design patterns in the code
- `_classify_project_type`: Classify the project type
- `_assess_complexity`: Assess project complexity
- `_detect_architecture`: Detect architecture pattern
- `_detect_conventions`: Detect coding conventions used
- `_assess_quality_indicators`: Assess code quality indicators
- `_save_classification`: Save classification to memory for learning
- `get_recommendations`: Get recommendations based on project characteristics
- `main`

### vibe.prompt_enhancer
Prompt Enhancer for VIBE MCP

Automatically structures user prompts into 3-layer format:
1. Context Layer: Project state, stack, component references
2. Task Layer: Clear instructions and requirements
3. Constraints Layer: Security rules, style guidelines, patterns

Orchestrates RulesEngine and ContextInjector to create enhanced prompts.

**Classes:**
- `PromptComplexity`: Complexity levels of prompts
- `PromptLayer`: Represents a layer in the enhanced prompt
- `EnhancedPrompt`: Complete enhanced prompt with all layers
- `PromptEnhancer`: Enhances user prompts with context and constraints
**Functions:**
- `__init__`
- `enhance`: Enhance a user prompt with context and constraints
- `_detect_complexity`: Detect the complexity of a user prompt
- `_build_context_layer`: Build the context layer of the enhanced prompt
- `_build_task_layer`: Build the task layer from user prompt
- `_build_constraints_layer`: Build the constraints layer using rules engine
- `_extract_requirements`: Extract explicit requirements from prompt
- `_extract_expected_output`: Extract expected output from prompt
- `_get_timestamp`: Get current timestamp
- `format_prompt`: Format enhanced prompt into final string
- `learn_from_outcome`: Learn from the outcome of using an enhanced prompt
- `get_similar_prompts`: Get similar successful prompts from memory
- `create_config_file`: Create default configuration file
- `main`

### vibe.rules_engine
Rules Engine for VIBE MCP

Manages and injects rules automatically:
- Security rules: Prevent vulnerabilities
- Style rules: Enforce coding standards
- Project rules: Project-specific conventions
- Priority handling: Security > Project > Style

Rules are loaded from YAML configuration files and can be
dynamically applied based on context.

**Classes:**
- `RuleCategory`: Categories of rules
- `RulePriority`: Priority levels for rules
- `Rule`: Represents a single rule
- `RuleSet`: A collection of rules for a specific context
- `RulesEngine`: Manages and applies rules for code generation
**Functions:**
- `__post_init__`
- `__init__`
- `_load_default_rules`: Load built-in default rules
- `_load_custom_rules`: Load custom rules from YAML files
- `_parse_rule_from_yaml`: Parse a rule from YAML data
- `register_rule`: Register a new rule
- `get_rule`: Get a rule by ID
- `get_applicable_rules`: Get rules applicable to the given prompt and context
- `_is_rule_applicable`: Check if a rule applies to the given prompt and context
- `get_rules_by_category`: Get all rules in a category
- `get_rules_by_tag`: Get all rules with a specific tag
- `resolve_conflicts`: Resolve conflicts between rules based on priority
- `create_rule_files`: Create example rule configuration files
- `export_rules`: Export all rules to a YAML file
- `_get_timestamp`: Get current timestamp
- `main`

### vibe.task_decomposer
Task Decomposer for VIBE MCP

Breaks complex requests into structured phases:
- Analyzes request complexity
- Identifies dependencies
- Creates execution plan
- Estimates effort per phase
- Generates phase-specific prompts

Uses LLM for intelligent decomposition based on context.

**Classes:**
- `PhaseType`: Types of phases in a task
- `TaskComplexity`: Complexity levels for tasks
- `TaskPhase`: Represents a single phase in a task
- `TaskPlan`: Complete task decomposition plan
- `TaskDecomposer`: Decomposes complex tasks into structured phases
**Functions:**
- `__init__`
- `decompose`: Decompose a request into structured phases
- `_detect_task_type`: Detect the type of task from the request
- `_estimate_complexity`: Estimate task complexity based on request and context
- `_create_simple_phase`: Create a single phase for simple tasks
- `_llm_decompose`: Use LLM to decompose complex tasks
- `_pattern_decompose`: Fallback pattern-based decomposition
- `_validate_phases`: Validate and fix phase dependencies
- `_generate_task_id`: Generate unique task ID
- `_estimate_duration`: Estimate duration based on total effort
- `get_execution_order`: Get phases in execution order based on dependencies
- `export_plan`: Export task plan to JSON file
- `create_template`: Create a task template for common patterns
- `main`

### vibe.__init__
VIBE MCP - Vibe Coding Automation

This module implements the Vibe Coding Platform automation features:
- Prompt Engineering Automation
- Structured Process Management
- Quality Pipeline Integration
- Learning & Iteration Features

Components:
- PromptEnhancer: Enhances user prompts with context and constraints
- RulesEngine: Manages and injects coding rules automatically
- ContextInjector: Provides project context for prompts
- TaskDecomposer: Breaks complex requests into structured phases
- ContextManager: Tracks state across phases with persistence
- AutoCommit: Handles Git commits after each phase
- ArchitectAgent: Creates architectural plans before coding
- AutoRollback: Automatically rolls back on phase failures


### voice.elevenlabs_client
AI Project Synthesizer - ElevenLabs Voice Client

Full-featured ElevenLabs integration for:
- Text-to-Speech (TTS)
- Real-time voice streaming (LOW LATENCY)
- Voice cloning
- Voice selection and management

SPEED OPTIMIZATION:
- Use eleven_turbo_v2_5 for fastest response
- Stream audio chunks for smooth playback without gaps
- PCM format for lowest latency

**Classes:**
- `Voice`: ElevenLabs voice information
- `VoiceSettings`: Voice generation settings
- `ElevenLabsClient`: ElevenLabs API client for voice synthesis
**Functions:**
- `__post_init__`
- `__init__`: Initialize ElevenLabs client
- `_get_session`: Get or create aiohttp session
- `close`: Close the client session
- `_resolve_voice_id`: Resolve voice name or ID to voice ID
- `text_to_speech`: Convert text to speech audio
- `stream_speech`: Stream text-to-speech audio in real-time
- `get_voices`: Get all available voices
- `get_voice`: Get specific voice details
- `save_audio`: Generate and save audio to file
- `get_user_info`: Get user subscription info
- `get_usage`: Get character usage info
- `create_elevenlabs_client`: Factory function to create ElevenLabs client if API key is available

### voice.manager
AI Project Synthesizer - Voice Management System

Comprehensive voice management for:
- Voice selection and configuration
- Audio playback control
- Speech recognition
- Voice profiles

**Classes:**
- `VoiceProvider`: Available voice providers
- `AudioFormat`: Audio output formats
- `VoiceProfile`: Voice profile configuration
- `AudioSession`: Active audio session
- `VoiceManager`: Central voice management system
**Functions:**
- `to_dict`
- `__init__`
- `_get_elevenlabs_client`: Get ElevenLabs client
- `_get_piper_client`: Get Piper TTS client
- `list_voices`: List available voice profiles
- `get_voice`: Get a voice profile by ID
- `add_voice`: Add a custom voice profile
- `set_default_voice`: Set the default voice
- `speak`: Generate and play speech
- `speak_fast`: Quick speech with streaming for low latency
- `get_session`: Get current audio session
- `start_session`: Start a new audio session
- `end_session`: End current audio session
- `get_voice_manager`: Get or create voice manager

### voice.player
AI Project Synthesizer - Voice Player

Auto-plays audio for MCP clients that don't have native audio playback.
Tagged for: LM Studio (requires this for voice playback)

Other MCP clients may have native audio support and won't need this.

**Classes:**
- `PlaybackResult`: Result of audio playback
- `VoicePlayer`: Cross-platform audio player for voice output
**Functions:**
- `__init__`: Initialize voice player
- `play_base64`: Play base64-encoded audio
- `play_bytes`: Play audio from bytes
- `play_file`: Play audio file through system speakers
- `_play_windows`: Play audio on Windows using PowerShell
- `_play_macos`: Play audio on macOS using afplay
- `_play_linux`: Play audio on Linux using available player
- `stop`: Stop current playback
- `cleanup`: Clean up temp files
- `get_voice_player`: Get or create global voice player
- `play_audio`: Convenience function to play base64 audio

### voice.realtime_conversation
AI Project Synthesizer - Real-Time Voice Conversation

Instant back-and-forth voice chat:
1. Listens to user via microphone
2. Detects silence (configurable pause threshold)
3. Transcribes speech to text
4. Sends to AI assistant
5. Speaks response immediately (streaming)
6. Loops back to listening

PAUSE DETECTION:
- Default: 3.5 seconds of silence triggers response
- Configurable via pause_threshold parameter

PROACTIVE RESEARCH (when user is idle):
- 30s idle: Light research (quick project search)
- 60s idle: Medium research (more projects + papers)
- 120s idle: Deep research (synthesis recommendations)
- AI presents findings when user returns!

**Classes:**
- `ConversationState`: Current state of the conversation
- `ConversationConfig`: Configuration for real-time conversation
- `RealtimeConversation`: Real-time voice conversation with AI
**Functions:**
- `__init__`: Initialize conversation
- `start`: Start the conversation loop
- `stop`: Stop the conversation
- `_init_components`: Initialize AI and voice components
- `on_research_complete`
- `_set_state`: Update state and notify
- `_listen_loop`: Background thread that captures audio
- `_get_audio_level`: Get audio level from raw data
- `_process_loop`: Main processing loop
- `_transcribe`: Transcribe audio to text using Whisper or cloud API
- `_speak`: Speak text using streaming voice
- `start_voice_chat`: Start a real-time voice conversation

### voice.streaming_player
AI Project Synthesizer - Streaming Voice Player

OPTIMIZED FOR SPEED AND SMOOTH PLAYBACK:
- Streams audio chunks as they arrive (no waiting for full generation)
- Uses turbo model for fastest response
- PCM format for lowest latency
- Buffer management for smooth transitions without gaps

LM STUDIO INTEGRATION:
This provides seamless voice output for MCP clients without native audio.

**Classes:**
- `StreamConfig`: Configuration for streaming playback
- `StreamingVoicePlayer`: Real-time streaming voice player
**Functions:**
- `__init__`: Initialize streaming player
- `_init_api_key`: Get ElevenLabs API key
- `speak`: Speak text with streaming playback
- `_stream_audio`: Stream audio from ElevenLabs API
- `_start_player_thread`: Start background audio player thread
- `_player_loop`: Background thread that plays audio chunks
- `_play_windows_stream`: Play streaming audio on Windows using winsound or pyaudio
- `_play_with_pyaudio`: Play using PyAudio for lowest latency
- `_play_collected_chunks`: Collect chunks and play as file (fallback)
- `_play_macos_stream`: Play streaming audio on macOS
- `_play_linux_stream`: Play streaming audio on Linux
- `stop`: Stop current playback
- `get_streaming_player`: Get or create streaming player
- `speak_fast`: Quick function for fast, smooth voice output

### voice.__init__
AI Project Synthesizer - Voice Module

Voice AI integration including:
- ElevenLabs TTS and real-time voice
- Voice selection and management
- Auto-playback for LM Studio (tagged)
- Voice manager for unified control


### workflows.langchain_integration
AI Project Synthesizer - LangChain Integration

Advanced LLM workflows using LangChain:
- Research chains for multi-step discovery
- Synthesis chains for project assembly
- RAG chains for documentation
- Agent chains for autonomous tasks

**Classes:**
- `ChainConfig`: Configuration for LangChain chains
- `LangChainOrchestrator`: Orchestrates LangChain workflows for the synthesizer
**Functions:**
- `__init__`: Initialize orchestrator
- `_get_llm`: Get or create LLM instance
- `research`: Run research chain to discover resources
- `synthesize`: Run synthesis chain to plan project assembly
- `chat`: Chat with memory for multi-turn conversations
- `create_agent`: Create a ReAct agent with custom tools
- `create_research_chain`: Create a research chain for discovering resources
- `run_chain`
- `create_synthesis_chain`: Create a synthesis chain for project assembly planning
- `run_chain`
- `create_synthesizer_tools`: Create LangChain tools for the synthesizer agent
- `search_github`: Search GitHub repositories
- `search_huggingface`: Search HuggingFace models
- `assemble_project`: Assemble a project from an idea

### workflows.n8n_integration
AI Project Synthesizer - n8n Integration

Local n8n workflow automation for:
- Visual workflow design
- Scheduled tasks
- Webhook triggers
- Multi-step automations

n8n runs locally at http://localhost:5678

**Classes:**
- `WorkflowStatus`: Workflow execution status
- `N8NConfig`: n8n connection configuration
- `N8NWorkflow`: Represents an n8n workflow
- `WorkflowExecution`: Workflow execution result
- `N8NClient`: Client for interacting with local n8n instance
- `N8NWorkflowTemplates`: Pre-built n8n workflow templates for common tasks
**Functions:**
- `to_dict`
- `__init__`: Initialize n8n client
- `_get_client`: Get or create HTTP client
- `close`: Close HTTP client
- `health_check`: Check if n8n is running
- `list_workflows`: List all workflows
- `get_workflow`: Get a specific workflow
- `create_workflow`: Create a new workflow
- `execute_workflow`: Execute a workflow
- `activate_workflow`: Activate a workflow
- `deactivate_workflow`: Deactivate a workflow
- `research_workflow`: Create a research workflow template
- `scheduled_search_workflow`: Create a scheduled search workflow
- `webhook_assembly_workflow`: Create a webhook-triggered assembly workflow
- `voice_notification_workflow`: Create a voice notification workflow
- `setup_n8n_workflows`: Set up default workflows in n8n

### workflows.orchestrator
AI Project Synthesizer - Unified Workflow Orchestrator

Central orchestrator that coordinates:
- LangChain workflows
- Pydantic AI agents
- n8n automation
- Voice interactions
- Project assembly

**Classes:**
- `WorkflowType`: Types of workflows
- `WorkflowEngine`: Workflow execution engines
- `WorkflowStep`: A single step in a workflow
- `WorkflowDefinition`: Complete workflow definition
- `WorkflowResult`: Result of workflow execution
- `WorkflowOrchestrator`: Unified workflow orchestrator
**Functions:**
- `__init__`: Initialize orchestrator
- `_get_langchain`: Get LangChain orchestrator
- `_get_n8n`: Get n8n client
- `research`: Research workflow - Find resources for a project idea
- `synthesize_project`: Full project synthesis workflow
- `conversation`: Conversation workflow with optional voice
- `_execute_action`: Execute a detected action
- `execute`: Execute a custom workflow definition
- `_execute_step`: Execute a single workflow step
- `get_orchestrator`: Get or create workflow orchestrator

### workflows.__init__
AI Project Synthesizer - Workflow Engine

Integrates:
- LangChain for LLM orchestration and chains
- n8n for visual workflow automation
- Pydantic AI for type-safe agents
- Custom workflow definitions


### voice.asr.glm_asr_client
VIBE MCP - GLM-ASR Speech Recognition Client

High-performance speech recognition using GLM-ASR-Nano-2512.
Supports Mandarin, Cantonese, and English with exceptional dialect support.
Outperforms OpenAI Whisper V3 for low-volume speech recognition.

Features:
- 1.5B parameter model for high accuracy
- Multi-language support (Mandarin, Cantonese, English)
- Robust for low-volume speech
- Fast inference with local processing

**Classes:**
- `GLMASRClient`: GLM-ASR speech recognition client
- `FallbackTranscriber`: Simple fallback transcription using basic speech processing
**Functions:**
- `__init__`: Initialize GLM-ASR client
- `initialize`: Initialize the GLM-ASR model
- `transcribe`: Transcribe audio file to text
- `transcribe_batch`: Transcribe multiple audio files in batch
- `detect_language`: Detect the language of an audio file
- `get_supported_languages`: Get list of supported languages
- `release_memory`: Release model memory
- `create_glm_asr_client`: Create and initialize a GLM-ASR client
- `__init__`
- `transcribe`: Fallback transcription - returns placeholder text
- `transcribe_batch`: Fallback batch transcription
- `get_transcription_client`: Get the best available transcription client

### voice.tts.piper_client
VIBE MCP - Piper TTS Client

Local text-to-speech using Piper for fast, offline voice synthesis.
Integrates with extracted ElevenLabs voice samples for voice cloning.

Features:
- Local voice synthesis with <100ms latency
- Support for custom voice models from extracted samples
- Multiple audio formats (WAV, MP3, PCM)
- Voice configuration and management

**Classes:**
- `PiperTTSClient`: Piper TTS client for local voice synthesis
**Functions:**
- `__init__`: Initialize Piper TTS client
- `initialize`: Initialize the Piper TTS client
- `_load_voice_models`: Load available voice models from model directory
- `synthesize`: Synthesize speech from text using Piper
- `get_available_voices`: Get list of available voice models
- `create_voice_model`: Create a custom voice model from audio samples
- `get_extracted_voices`: Get information about extracted voice samples
- `create_piper_client`: Create and initialize a Piper TTS client

### llm.providers.base
AI Project Synthesizer - Base LLM Provider Interface

Abstract base class and common types for all LLM providers.

**Classes:**
- `ProviderType`: Supported LLM provider types
- `ProviderStatus`: Provider health status
- `ProviderCapabilities`: Capabilities supported by a provider
- `ProviderConfig`: Configuration for an LLM provider
- `CompletionResult`: Result from LLM completion
- `StreamChunk`: Chunk from streaming completion
- `LLMProvider`: Abstract base class for LLM providers
**Functions:**
- `__init__`: Initialize provider with configuration
- `name`: Provider name
- `provider_type`: Provider type
- `is_local`: Whether this is a local provider
- `is_available`: Check if provider is available and healthy
- `list_models`: List available models from this provider
- `complete`: Generate completion for prompt
- `stream`: Stream completion for prompt (optional, not all providers support)
- `health_check`: Perform health check and return status
- `get_model_for_size`: Get model name for given size tier
- `close`: Clean up provider resources
- `__repr__`

### llm.providers.ollama
AI Project Synthesizer - Ollama Provider

Native Ollama provider using the Ollama API directly.
Supports all Ollama-specific features including model management.

**Classes:**
- `OllamaProvider`: Native Ollama provider using Ollama's REST API
**Functions:**
- `__init__`
- `is_available`: Check if Ollama server is available
- `list_models`: List available Ollama models
- `get_model_info`: Get detailed information about a model
- `pull_model`: Pull a model from Ollama registry
- `complete`: Generate completion using Ollama API
- `stream`: Stream completion using Ollama API
- `close`: Close the HTTP client

### llm.providers.openai_compatible
AI Project Synthesizer - OpenAI-Compatible Provider

Generic provider for any OpenAI-compatible API including:
- LM Studio
- LocalAI
- vLLM
- Text Generation WebUI (with OpenAI extension)
- Ollama (OpenAI mode)
- Any other OpenAI-compatible server

**Classes:**
- `OpenAICompatibleProvider`: Generic provider for OpenAI-compatible APIs
**Functions:**
- `__init__`
- `is_available`: Check if the OpenAI-compatible server is available
- `list_models`: List available models from the server
- `complete`: Generate completion using OpenAI-compatible API
- `stream`: Stream completion using OpenAI-compatible API
- `close`: Close the client

### llm.providers.registry
AI Project Synthesizer - Provider Registry

Central registry for managing multiple LLM providers with:
- Dynamic provider registration
- Health monitoring
- Automatic fallback
- Load balancing

**Classes:**
- `ProviderInfo`: Information about a registered provider
- `ProviderRegistry`: Central registry for LLM providers
**Functions:**
- `__init__`
- `_register_builtin_providers`: Register built-in provider implementations
- `register_provider_class`: Register a custom provider class
- `register_provider`: Register a new provider with the registry
- `unregister_provider`: Remove a provider from the registry
- `get_provider`: Get a specific provider by name
- `list_providers`: List all registered provider names
- `get_provider_info`: Get detailed info about a provider
- `check_provider_health`: Check health of a specific provider
- `check_all_health`: Check health of all providers
- `get_best_provider`: Get the best available provider
- `complete`: Complete prompt with automatic provider selection and fallback
- `close_all`: Close all provider connections
- `get_provider_registry`: Get the global provider registry instance

### llm.providers.__init__
AI Project Synthesizer - LLM Provider Registry

Unified interface for multiple LLM providers including:
- Ollama (local)
- LM Studio (local, OpenAI-compatible)
- OpenAI (cloud)
- Anthropic (cloud)
- Groq (cloud, fast inference)
- Together AI (cloud)
- OpenRouter (cloud, multi-model)
- Local AI (self-hosted)
- Text Generation WebUI (local)
- vLLM (local/cloud)
- Kobold AI (local)


### automation.n8n_workflows.__init__
n8n Workflow Definitions

JSON workflow files for import into n8n.


