Code Explainer Pro
A professional-grade code analysis tool that provides detailed explanations, refactor suggestions, complexity analysis, and security reviews for your code. Powered by local Ollama LLM.


✨ Features
Multi-Language Support: Automatically detects and analyzes code in Python, JavaScript, Java, C++, HTML, CSS, Go, Rust, Ruby, and PHP

Comprehensive Analysis:

Code Explanations (step-by-step breakdown)

Refactor Suggestions (with code examples)

Complexity Analysis (Big O notation)

Security Review (vulnerability identification)

Smart Code Processing: Handles large files with intelligent truncation

Modern UI: Responsive design with dark/light mode support

Connection Diagnostics: Real-time Ollama status monitoring

Rate Limiting: Prevents abuse with configurable rate limits

Code Formatting: Basic code formatting for improved readability

🚀 Quick Start
Prerequisites
Python 3.7 or higher

Ollama installed and running

At least one Ollama model downloaded

Installation
Clone or download the project files

bash
# If using git
git clone <your-repo-url>
cd code-explainer-pro
Install Python dependencies

bash
pip install flask requests python-dotenv
Set up Ollama

bash
# Start Ollama service
ollama serve

# Download a model (in a separate terminal)
ollama pull llama2
# or
ollama pull codellama:7b
Configure environment (optional)

bash
# Edit the .env file if you need custom settings
cp .env.example .env
# Edit .env with your preferred settings
Run the application

bash
python app.py
Open your browser
Navigate to http://localhost:5000

⚙️ Configuration
Environment Variables
Create a .env file to customize the application:

env
# Ollama connection settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2:7b

# Request handling
OLLAMA_TIMEOUT=120
OLLAMA_MAX_TOKENS=2000
OLLAMA_TEMPERATURE=0.2

# Code processing
MAX_CODE_LENGTH=18000
HEAD_CHARS=8000
TAIL_CHARS=8000

# Flask settings
FLASK_MAX_CONTENT_LENGTH=33554432  # 32MB in bytes
SESSION_SECRET=your-secret-key-here
Default Values
Ollama URL: http://localhost:11434

Default Model: llama2:7b

Max Code Length: 18,000 characters

Request Timeout: 120 seconds

🎯 Usage
Paste your code into the source code textarea

Select analysis type:

Full Analysis (default): All four analysis types

Explain Only: Just the code explanation

Refactor Only: Only refactor suggestions

Complexity: Time and space complexity analysis

Security: Security vulnerability review

Click "Analyze Code" to process your code

Review results in the tabbed output sections

Supported Languages
Python

JavaScript

Java

C++

HTML

CSS

Go

Rust

Ruby

PHP

🔧 Troubleshooting
Common Issues
"Cannot connect to Ollama" error

Ensure Ollama is running: ollama serve

Verify the port in your .env file matches Ollama's port (default: 11434)

Check if models are downloaded: ollama list

"Model not available" error

Download a model: ollama pull llama2

Code truncation warning

The app automatically truncates very large files (>18,000 chars)

It preserves both the beginning and end of your code

Slow responses

Try a smaller model or reduce the OLLAMA_MAX_TOKENS value

For large code files, use specific analysis types instead of "Full Analysis"

Performance Tips
Use smaller models for faster responses

For large codebases, analyze specific sections rather than entire files

Use the specific analysis types (Explain, Refactor, etc.) instead of Full Analysis for quicker results

📁 Project Structure
text
code-explainer-pro/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration (create if needed)
└── templates/
    └── index.html        # Main web interface
🛠️ Development
Adding New Language Support
Extend the detect_language() function in app.py with new patterns

Update the prompt generation in generate_prompt() for language-specific analysis

Customizing Prompts
Modify the generate_prompt() function to change how the LLM is instructed to analyze code.

Extending Analysis Types
Add new analysis types by:

Adding new options to the UI

Extending the prompt generation logic

Adding new response parsing in split_into_sections()

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the project

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Ollama for providing the local LLM infrastructure

Flask web framework

All the open-source LLM model creators

📞 Support
If you encounter any problems or have questions:

Check the troubleshooting section above

Ensure Ollama is properly installed and running

Verify you have at least one model downloaded

Check that your firewall isn't blocking local connections

