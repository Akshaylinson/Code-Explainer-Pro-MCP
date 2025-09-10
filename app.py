
import os
import re
import requests
import json
import time
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama2:7b")
OLLAMA_API = OLLAMA_URL.rstrip("/") + "/api/generate"

OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
MAX_CODE_LENGTH = int(os.getenv("MAX_CODE_LENGTH", "18000"))
HEAD_CHARS = int(os.getenv("HEAD_CHARS", "8000"))
TAIL_CHARS = int(os.getenv("TAIL_CHARS", "8000"))
FLASK_MAX_CONTENT_LENGTH = int(os.getenv("FLASK_MAX_CONTENT_LENGTH", str(32 * 1024 * 1024)))
SESSION_SECRET = os.getenv("SESSION_SECRET", "supersecretkey")

app = Flask(__name__, template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = FLASK_MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = SESSION_SECRET

# Cache for storing recent analysis results
analysis_cache = {}

def check_ollama_connection():
    """Check if Ollama is running and available"""
    try:
        resp = requests.get(f"{OLLAMA_URL.rstrip('/')}/api/tags", timeout=5)
        if resp.status_code == 200:
            return True, "Ollama is running and accessible"
        else:
            return False, f"Ollama returned status code: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama. Make sure it's running on the correct port."
    except requests.exceptions.Timeout:
        return False, "Connection to Ollama timed out."
    except Exception as e:
        return False, f"Error connecting to Ollama: {str(e)}"

def get_available_models():
    """Get list of available models from Ollama"""
    try:
        resp = requests.get(f"{OLLAMA_URL.rstrip('/')}/api/tags", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except:
        return []

def rate_limit(max_requests=10, time_window=60):
    """Decorator to implement rate limiting"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_ip' not in session:
                session['user_ip'] = request.remote_addr
                session['requests'] = []
            
            current_time = time.time()
            # Clean old requests
            session['requests'] = [t for t in session['requests'] if current_time - t < time_window]
            
            if len(session['requests']) >= max_requests:
                return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
                
            session['requests'].append(current_time)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def detect_language(code):
    """Simple language detection based on code patterns"""
    patterns = {
        'python': [r'^import\s+\w', r'^from\s+\w', r'def\s+\w+\(', r'class\s+\w+', r'print\s*\(', r'#.*'],
        'javascript': [r'function\s*\w*\(', r'const\s+|let\s+|var\s+', r'console\.log\(', r'\/\/.*', r'\/\*.*\*\/'],
        'java': [r'public\s+class', r'import\s+java', r'System\.out\.print', r'\/\/.*', r'\/\*.*\*\/'],
        'cpp': [r'#include\s+<.*>', r'using\s+namespace', r'std::', r'\/\/.*', r'\/\*.*\*\/'],
        'html': [r'<!DOCTYPE html>', r'<html', r'<head', r'<body', r'<div', r'<!--.*-->'],
        'css': [r'^\s*\.?\w+\s*\{', r'^\s*@\w+', r'\/\*.*\*\/'],
        'go': [r'package\s+\w+', r'import\s*\(', r'func\s+\w+\(', r'\/\/.*'],
        'rust': [r'fn\s+\w+\(', r'let\s+\w+', r'\/\/.*', r'\/\*.*\*\/'],
        'ruby': [r'def\s+\w+', r'class\s+\w+', r'#.*'],
        'php': [r'<\?php', r'\$\w+', r'\/\/.*', r'\/\*.*\*\/'],
    }
    
    for lang, regexes in patterns.items():
        for pattern in regexes:
            if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                return lang
    return "unknown"

def split_into_sections(text):
    if not text:
        return "", "", "", ""

    # Try to extract multiple sections
    patterns = [
        r"Explanation\s*[:\-]*\s*(.*?)\s*(?:Refactor\s*Suggestions|Refactor)\s*[:\-]*\s*(.*?)\s*(?:Complexity\s*Analysis|Complexity)\s*[:\-]*\s*(.*?)\s*(?:Security\s*Considerations|Security)\s*[:\-]*\s*(.*)",
        r"Explanation\s*[:\-]*\s*(.*?)\s*(?:Refactor\s*Suggestions|Refactor)\s*[:\-]*\s*(.*?)\s*(?:Complexity\s*Analysis|Complexity)\s*[:\-]*\s*(.*)",
        r"Explanation\s*[:\-]*\s*(.*?)\s*(?:Refactor\s*Suggestions|Refactor)\s*[:\-]*\s*(.*)",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            groups = m.groups()
            explanation = groups[0].strip() if len(groups) > 0 else ""
            refactor = groups[1].strip() if len(groups) > 1 else ""
            complexity = groups[2].strip() if len(groups) > 2 else ""
            security = groups[3].strip() if len(groups) > 3 else ""
            return explanation, refactor, complexity, security

    # Fallback: split on section headers
    sections = {
        "explanation": "",
        "refactor": "",
        "complexity": "",
        "security": ""
    }
    
    current_section = None
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if "explanation" in line_lower:
            current_section = "explanation"
            sections[current_section] += line.replace("Explanation", "").replace(":", "").strip() + "\n"
        elif "refactor" in line_lower:
            current_section = "refactor"
            sections[current_section] += line.replace("Refactor Suggestions", "").replace("Refactor", "").replace(":", "").strip() + "\n"
        elif "complexity" in line_lower:
            current_section = "complexity"
            sections[current_section] += line.replace("Complexity Analysis", "").replace("Complexity", "").replace(":", "").strip() + "\n"
        elif "security" in line_lower:
            current_section = "security"
            sections[current_section] += line.replace("Security Considerations", "").replace("Security", "").replace(":", "").strip() + "\n"
        elif current_section:
            sections[current_section] += line.strip() + "\n"
    
    return sections["explanation"], sections["refactor"], sections["complexity"], sections["security"]

def smart_truncate_code(code: str):
    if len(code) <= MAX_CODE_LENGTH:
        return code, False
    head = code[:HEAD_CHARS]
    tail = code[-TAIL_CHARS:]
    truncated_notice = (
        "\n\n/* --- CODE TRUNCATED FOR LLM (head + tail sent). "
        "Full code was longer than allowed. --- */\n\n"
    )
    return head + truncated_notice + tail, True

def generate_prompt(code, language, analysis_type="full"):
    """Generate appropriate prompt based on language and analysis type"""
    
    base_prompt = (
        "You are an expert code analyst and software engineer.\n"
        f"Analyze the following {language} code.\n"
    )
    
    if analysis_type == "full":
        prompt = base_prompt + (
            "Return your answer in four clear sections:\n\n"
            "Explanation\n"
            "(explain what the code does in plain English, step by step)\n\n"
            "Refactor Suggestions\n"
            "(list specific improvements in naming, structure, readability, or optimization with code examples)\n\n"
            "Complexity Analysis\n"
            "(analyze time and space complexity with Big O notation)\n\n"
            "Security Considerations\n"
            "(identify potential security issues and how to fix them)\n\n"
        )
    elif analysis_type == "explain":
        prompt = base_prompt + (
            "Explain what this code does in plain English, step by step.\n"
            "Be detailed but concise.\n\n"
        )
    elif analysis_type == "refactor":
        prompt = base_prompt + (
            "Provide specific refactor suggestions with code examples.\n"
            "Focus on naming, structure, readability, and optimization.\n\n"
        )
    elif analysis_type == "complexity":
        prompt = base_prompt + (
            "Analyze the time and space complexity of this code using Big O notation.\n"
            "Explain your reasoning for each part of the code.\n\n"
        )
    elif analysis_type == "security":
        prompt = base_prompt + (
            "Identify potential security issues in this code.\n"
            "For each issue, explain the risk and provide a fix.\n\n"
        )
    
    prompt += (
        "--- CODE START ---\n"
        f"{code}\n"
        "--- CODE END ---\n\n"
    )
    
    return prompt

@app.route("/", methods=["GET"])
def index():
    # Check Ollama connection and available models
    ollama_connected, message = check_ollama_connection()
    available_models = get_available_models()
    
    return render_template(
        "index.html", 
        model=MODEL, 
        ollama_url=OLLAMA_URL,
        ollama_connected=ollama_connected,
        ollama_message=message,
        available_models=available_models
    )

@app.route("/api/models", methods=["GET"])
def get_models():
    """Get available models from Ollama"""
    try:
        resp = requests.get(f"{OLLAMA_URL.rstrip('/')}/api/tags", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({"models": [model["name"] for model in data.get("models", [])]})
        return jsonify({"models": []})
    except:
        return jsonify({"models": []})

@app.route("/analyze", methods=["POST"])
@rate_limit(max_requests=15, time_window=60)
def analyze():
    # First check if Ollama is available
    ollama_connected, message = check_ollama_connection()
    if not ollama_connected:
        return jsonify({"error": f"Ollama is not available: {message}"}), 503
        
    # Check if model is available
    available_models = get_available_models()
    if MODEL not in available_models:
        return jsonify({"error": f"Model '{MODEL}' is not available. Available models: {', '.join(available_models)}"}), 503

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON input."}), 400

    code = data.get("code") if isinstance(data, dict) else None
    analysis_type = data.get("type", "full")
    
    if not code or not isinstance(code, str) or not code.strip():
        return jsonify({"error": "No code provided. Please paste code in the textarea."}), 400

    # Check cache first
    cache_key = f"{hash(code)}:{analysis_type}"
    if cache_key in analysis_cache:
        return jsonify(analysis_cache[cache_key])

    send_code, truncated_flag = smart_truncate_code(code)
    language = detect_language(send_code)

    prompt = generate_prompt(send_code, language, analysis_type)

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
            "num_predict": int(os.getenv("OLLAMA_MAX_TOKENS", "2000")),
        }
    }

    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        resp_json = resp.json()
    except requests.exceptions.ConnectionError as e:
        return jsonify({"error": f"Cannot connect to Ollama at {OLLAMA_API}. Make sure Ollama is running."}), 502
    except requests.exceptions.Timeout as e:
        return jsonify({"error": f"Request to Ollama timed out after {OLLAMA_TIMEOUT} seconds."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to contact Ollama: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    content = resp_json.get("response")
    if not content:
        return jsonify({"error": "Could not parse response from Ollama."}), 502

    explanation, refactor, complexity, security = split_into_sections(content)

    result = {
        "explanation": explanation,
        "refactor": refactor,
        "complexity": complexity,
        "security": security,
        "truncated": bool(truncated_flag),
        "language": language,
        "analysis_type": analysis_type
    }
    
    # Cache the result
    analysis_cache[cache_key] = result
    if len(analysis_cache) > 100:  # Limit cache size
        oldest_key = next(iter(analysis_cache))
        analysis_cache.pop(oldest_key)

    return jsonify(result), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    ollama_connected, message = check_ollama_connection()
    available_models = get_available_models()
    
    return jsonify({
        "status": "healthy",
        "ollama_connected": ollama_connected,
        "ollama_message": message,
        "available_models": available_models,
        "model": MODEL,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    # Check Ollama connection at startup
    connected, message = check_ollama_connection()
    if connected:
        print(f"✓ Connected to Ollama at {OLLAMA_URL}")
        models = get_available_models()
        if models:
            print(f"✓ Available models: {', '.join(models)}")
        else:
            print("⚠ No models available. Run 'ollama pull llama2' to download a model.")
    else:
        print(f"⚠ {message}")
    
    app.run(host="127.0.0.1", port=5000, debug=True)
