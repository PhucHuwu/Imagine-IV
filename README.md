# Imagine-IV

A desktop automation tool for Grok Imagine video generation. This application automates the process of generating AI videos using Grok's Imagine feature.

## Features

- Automated image generation from text prompts
- Video generation from source images
- Batch processing with customizable settings
- OpenRouter API integration for prompt generation
- Automatic video concatenation using FFmpeg
- Built-in Chrome browser automation

## Requirements

- Python 3.11+
- Google Chrome browser installed
- OpenRouter API key (for prompt generation)

## Installation

### From Source

1. Clone the repository:

```bash
git clone https://github.com/PhucHuwu/Imagine-IV.git
cd Imagine-IV
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the application:
    - Copy `config.json.template` to `config.json`
    - Add your OpenRouter API key and model settings

4. Run the application:

```bash
python main.py
```

### From Release

1. Download the latest release from the [Releases](https://github.com/PhucHuwu/Imagine-IV/releases) page
2. Extract and run `Imagine-IV.exe`

## Configuration

Edit `config.json` to configure:

| Setting              | Description                        |
| -------------------- | ---------------------------------- |
| `openrouter_api_key` | Your OpenRouter API key            |
| `openrouter_model`   | Model to use for prompt generation |
| `timeout_seconds`    | Timeout for operations             |
| `batch_size`         | Number of videos per batch         |

## Usage

1. Launch the application
2. Click "Open Browser" to start Chrome
3. Log in to Grok manually
4. Click "Confirm Login" once logged in
5. Configure generation settings in the "Image" or "Video" tabs
6. Click "Start" to begin automated generation

## Project Structure

```
Imagine-IV/
├── main.py              # Entry point
├── config.json          # User configuration
├── requirements.txt     # Python dependencies
└── src/
    ├── browser_manager.py    # Chrome automation
    ├── grok_automation.py    # Grok-specific automation
    ├── video_generator.py    # Video generation logic
    ├── video_processor.py    # FFmpeg operations
    ├── prompt_generator.py   # OpenRouter API client
    └── gui/                  # User interface
```

## License

This project is for educational purposes only.

## Disclaimer

This tool automates interactions with Grok Imagine. Use responsibly and in accordance with Grok's terms of service.
