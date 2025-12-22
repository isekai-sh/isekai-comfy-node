# Isekai ComfyUI Custom Node

[![Latest Release](https://img.shields.io/github/v/release/isekai-sh/isekai-comfy-node)](https://github.com/isekai-sh/isekai-comfy-node/releases/latest)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/isekai-sh/isekai-comfy-node)](LICENSE)

Isekai Comfy Node is a collection of custom nodes for ComfyUI that integrates well with your Isekai Core deployment. These nodes allow you to upload images directly to Isekai, compress images before saving, manipulate strings for prompts, and generate titles using local Ollama LLMs.

[Access the documentation here](https://isekai.sh/comfyui)

## Support

- **Issues:** Report bugs on [GitHub Issues](https://github.com/isekai-sh/isekai-comfy-node/issues)

## Development

### Project Structure

```
isekai-comfy-node/
├── __init__.py          # Package entry point
├── config.py            # Configuration management
├── README.md            # This file
├── requirements.txt     # Dependencies
├── .gitignore           # Git ignore rules
│
├── nodes/               # Node implementations
│   ├── __init__.py
│   ├── base.py          # Base classes and exceptions
│   ├── upload_node.py   # Isekai Upload (with compression)
│   ├── compress_and_save_node.py # Isekai Compress and Save
│   ├── dynamic_string_node.py
│   ├── concatenate_string_node.py
│   ├── tag_selector_node.py
│   ├── ollama_summarizer_node.py
│   ├── round_robin_node.py
│   └── load_text_node.py
│
└── utils/               # Shared utilities
    ├── __init__.py
    ├── validation.py    # Input validation
    ├── image_utils.py   # Image processing
    └── ollama_client.py # Ollama API client
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
