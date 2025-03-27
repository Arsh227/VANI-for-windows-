# Vani - AI Personal Assistant

Vani is a powerful, automated AI assistant that helps you manage your daily tasks efficiently. Built with Python, it integrates various AI services and system controls to provide a seamless experience.

## Features

- **Voice Interaction**: Natural language processing for voice commands
- **Document Management**: Create and edit Word documents, including essay writing
- **Web Browsing**: Search and navigate the web with voice commands
- **Image Analysis**: Take photos and analyze them using Gemini Vision AI
- **System Control**: Manage applications, volume, and system settings
- **Music Control**: Control Spotify and manage music playback
- **Smart Search**: Intelligent search across various platforms (Google, YouTube, etc.)

## Requirements

- Python 3.8+
- Windows 10/11
- Google Chrome
- Microsoft Word (for document features)
- Spotify (for music features)

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd vani-ai-assistant
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
GEMINI_API_KEY=your_gemini_api_key
GEMINI_VISION_API_KEY=your_gemini_vision_api_key
```

## Usage

1. Run the assistant:
```bash
python main.py
```

2. Common commands:
- "Write an essay on [topic]"
- "What do you see?" (for image analysis)
- "Search on browser [query]"
- "Open [application]"
- "Play [song] on Spotify"

## Project Structure

- `features/`: Core functionality modules
- `models/`: AI model integrations
- `utils/`: Utility functions
- `tests/`: Test files
- `data/`: Data storage and caching

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 