# AI Project Synthesizer Examples

This directory contains example demonstrations of what the AI Project Synthesizer can create.

## Available Examples

### 1. [Web Scraper Demo](./web-scraper-demo.md)
Shows how to synthesize a complete web scraping project with:
- BeautifulSoup and requests integration
- E-commerce data extraction
- Export capabilities
- Rate limiting and error handling

### 2. [ML API Demo](./ml-api-demo.md)
Demonstrates synthesis of a Machine Learning API with:
- FastAPI backend
- HuggingFace model integration
- Text classification endpoints
- Docker deployment support

## How to Use These Examples

1. **Start the MCP Server**
   ```bash
   python -m src.mcp_server.server
   ```

2. **Connect via Windsurf/Claude/VS Code**
   - Use the MCP client of your choice
   - Ensure the server is properly configured

3. **Run the Synthesis Command**
   Copy and paste the synthesis command from each demo into your MCP client.

4. **Review the Generated Project**
   The synthesizer will create a new directory with:
   - Complete project structure
   - All necessary dependencies
   - Working code examples
   - Documentation

## What Gets Synthesized?

For each project idea, the AI Project Synthesizer:

1. **Searches Across Platforms**
   - GitHub for code repositories
   - HuggingFace for ML models
   - Kaggle for datasets
   - arXiv for research papers

2. **Creates Unified Structure**
   - Organized source code layout
   - Configuration files
   - Test suites
   - Documentation

3. **Generates Dependencies**
   - Merges requirements from all sources
   - Resolves version conflicts
   - Includes development tools

4. **Prepares for Development**
   - Git initialization
   - IDE configuration
   - Docker support (when applicable)
   - GitHub repo creation

## Customizing Synthesized Projects

After synthesis, you can:
- Modify the generated code
- Add your own features
- Configure settings
- Deploy to production

## Contributing Examples

Have a great example of what you synthesized? Submit a PR to add it here!

## Tips for Best Results

1. **Be Specific in Your Ideas**
   - Include technologies you want
   - Mention specific features
   - Describe the use case

2. **Start Simple**
   - Begin with basic functionality
   - Add complexity iteratively
   - Test each component

3. **Review Generated Code**
   - Understand what was created
   - Customize for your needs
   - Add error handling

4. **Use Version Control**
   - Commit the synthesized project
   - Track your modifications
   - Create branches for features
