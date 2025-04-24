# Computer Use Agent Project

## Overview
This project demonstrates the use of Azure OpenAI's Computer Use Preview feature to control a web browser and perform online tasks autonomously. The agent can search for information, navigate websites, and interact with web elements without human intervention.

## Features
- Automated browser control using OpenAI's Computer Use Preview
- Sophisticated search box detection and interaction
- Multi-step task execution with visual feedback
- Detailed logging of all operations
- Error handling and recovery mechanisms
- Visual status overlays for real-time feedback

## Requirements
- Python 3.8+
- Azure OpenAI API access with Computer Use Preview enabled
- Playwright for browser automation
- Required Python packages: openai, python-dotenv, playwright

## Setup
1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```
   python -m playwright install
   ```
4. Create a `.env` file with your Azure OpenAI API credentials:
   ```
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_API_VERSION=your_api_version
   ESTIMATED_COST_PER_CALL=0.03
   ```

## Usage
Run the main script to start the browser automation:
```
python main.py
```

The script will:
1. Open a browser window
2. Navigate to Bing
3. Search for "AI news"
4. Click on a relevant news article
5. Log all actions and save screenshots of key steps

## Customization
You can modify the `instructions` variable in the code to change what the agent does. For example:
- Search for different topics
- Navigate to different websites
- Perform more complex multi-step tasks

## License
MIT

## Author
Omkar-55 