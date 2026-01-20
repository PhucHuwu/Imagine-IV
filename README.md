# Imagine-IV

A desktop automation tool for Grok Imagine video generation. This application automates the process of generating AI videos using Grok's Imagine feature.

## Features

- **Image Generation**
    - Automated image generation from text prompts
    - Toggle auto-prompt generation (OpenRouter) or use manual prompts
    - Batch processing with customizable settings
- **Video Generation**
    - Generate 6s or 12s videos from source images
    - 6s mode: Single video generation
    - 12s mode: Automatically concatenates two 6s videos using FFmpeg
    - Toggle auto-prompt or use manual prompts
- **Prompt Management**
    - OpenRouter API integration for AI-generated prompts
    - Manual prompt cards with expand/collapse functionality
    - Prompts are saved to config for reuse
- **Automation**
    - Built-in Chrome browser automation
    - Multi-threading support (up to 20 threads)
    - Automatic video concatenation using FFmpeg

## Requirements

- Python 3.11+
- Google Chrome browser installed
- OpenRouter API key (for auto-prompt generation)

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
2. **Windows**: Run `Imagine-IV.exe`
3. **macOS**: Extract zip and run `Imagine-IV.app`
    > Right-click and select "Open" to bypass Gatekeeper, or run `xattr -cr Imagine-IV.app`

## Configuration

Edit `config.json` to configure:

| Setting                     | Description                         | Default |
| --------------------------- | ----------------------------------- | ------- |
| `openrouter_api_key`        | Your OpenRouter API key             | -       |
| `openrouter_model`          | Model to use for prompt generation  | -       |
| `auto_prompt_enabled`       | Enable auto-prompt for images       | true    |
| `video_auto_prompt_enabled` | Enable auto-prompt for videos       | true    |
| `video_duration`            | Video duration in seconds (6 or 12) | 6       |
| `timeout_seconds`           | Timeout for operations              | 60      |
| `batch_size`                | Number of batches to generate       | 10      |

## Usage

1. Launch the application
2. Click "Mở Trình Duyệt Để Đăng Nhập" to start Chrome
3. Log in to Grok manually
4. Click "Xác Nhận Đã Đăng Nhập" once logged in
5. Choose tab:
    - **Tạo Ảnh**: Generate images with auto or manual prompts
    - **Tạo Video**: Generate 6s or 12s videos
6. Configure settings and click "Bắt Đầu"

### Manual Prompts

When auto-prompt is disabled:

- Click "+ Thêm prompt" to add prompt cards
- Each card can be expanded/collapsed for easier editing
- Prompts are automatically saved to config.json
- For 12s videos, each batch requires 2 prompts (video1 + video2)

## Project Structure

```
Imagine-IV/
├── main.py              # Entry point
├── config.json          # User configuration
├── requirements.txt     # Python dependencies
└── src/
    ├── browser_manager.py    # Chrome automation
    ├── grok_automation.py    # Grok-specific automation
    ├── image_generator.py    # Image generation logic
    ├── video_generator.py    # Video generation logic
    ├── video_processor.py    # FFmpeg operations
    ├── prompt_generator.py   # OpenRouter API client
    └── gui/                  # User interface
        ├── main_window.py
        ├── image_tab.py
        ├── video_tab.py
        ├── config_tab.py
        └── prompt_card.py    # Reusable prompt card widget
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool automates interactions with Grok Imagine. Use responsibly and in accordance with Grok's terms of service.
