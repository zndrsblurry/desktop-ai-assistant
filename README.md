# AI Desktop Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A robust and scalable AI-powered Desktop Assistant that allows you to control your computer through voice and text commands using Google's Gemini Live API and LangChain.

<!-- ![AI Desktop Assistant Screenshot](docs/screenshot.png) -->
<!-- TODO: Add a screenshot or GIF demo -->

## ✨ Features

- **🗣️ Natural Interaction**: Use voice commands (with real-time transcription) or typed messages.
- **⚡ Real-time & Interruptible**: Powered by Gemini Live API for low-latency, continuous, and interruptible conversations.
- **🖱️ System Control**: Execute precise mouse movements (adaptive optional), keyboard input, manage windows, and perform system operations (launch/close apps, file ops, etc.).
- **🌐 Web Integration**: Search the web (via DuckDuckGo or browser), open URLs. (Browser navigation/scraping can be added).
- **🧠 LangChain Orchestration**: Uses LangChain agents to understand intent and select appropriate tools for complex tasks.
- **🖥️ Cross-Platform (Goal)**: Designed with cross-platform libraries (PyQt, pynput, mss) aiming for compatibility with Windows, macOS, and Linux.
- **🔒 Safety Aware**: Configurable restrictions on accessing sensitive apps/files and confirmation for potentially dangerous actions.
- **🎨 Modern UI**: Sleek, customizable UI built with PyQt6 and QML, featuring voice visualization and light/dark themes.
- **🔧 Modular & Extensible**: Clean architecture using interfaces, dependency injection, and an event bus makes adding new tools and features easier.
- **⚙️ Configurable**: Settings managed via `.env` and YAML files for API keys, themes, behavior, etc.

## 🏗️ Architecture

The application follows a modern, modular design:

- **Event-Driven**: Components communicate via an `EventBus` (publish-subscribe), promoting loose coupling.
- **Dependency Injection**: A simple `DiContainer` manages service instantiation and injection.
- **Async-First**: Leverages `asyncio` and `qasync` for non-blocking operations, crucial for real-time interaction and UI responsiveness.
- **Interfaces (Protocols)**: Abstract base classes (`interfaces/`) define contracts between components (AI Service, Input/Output Providers, Action Executors).
- **Clear Separation**: Distinct layers for UI (`ui/`), Core Logic (`core/`), AI (`ai/`), Actions (`actions/`), Services (`services/`), Inputs (`input/`), and Outputs (`output/`).
- **Type Safety**: Comprehensive type annotations checked with `mypy`.
- **Code Quality**: Maintained using `ruff` (linting/formatting) and `pre-commit` hooks.

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10 or 3.11 recommended.
- **Conda**: Miniconda or Anaconda (for managing non-Python dependencies like PortAudio). [Installation Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)
- **Google Gemini API Key**: Obtain from [Google AI Studio](https://ai.google.dev/).
- **Git**: For cloning the repository.
- **(Optional) Tesseract-OCR Engine**: Required for OCR capabilities (screen text extraction). Install system-wide or via Conda (`conda install -c conda-forge tesseract tesseract-data-eng`). [Tesseract Installation](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- **(Optional) PortAudio**: Required by PyAudio. Conda usually handles this. If installing manually, see [PortAudio website](http://www.portaudio.com/download.html).
- **(Optional) FFmpeg**: Required by OpenCV for certain video operations. Conda usually handles this.
- **(Optional) Playwright Browsers**: If using Playwright for browser automation (`poetry install --extras browser`), run `python -m playwright install` after installing dependencies.

### Setup Instructions

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/yourusername/ai-desktop-assistant.git # Replace with your repo URL
    cd ai-desktop-assistant
    ```

2.  **Run the Setup Script:**
    This script creates the Conda environment, installs dependencies via Poetry, and sets up pre-commit hooks.

    ```bash
    python scripts/setup_dev.py
    ```

    _(On some systems, you might need `python3` instead of `python`)_

3.  **Activate the Conda Environment:**

    ```bash
    conda activate ai-desktop-assistant
    ```

    _(You need to activate the environment in every new terminal session)_

4.  **Create `.env` File:**
    Copy the example file and add your API key:

    ```bash
    cp .env.example .env
    ```

    Now, edit the `.env` file and paste your `GEMINI_API_KEY`.

    ```dotenv
    # .env
    GEMINI_API_KEY=your_actual_gemini_api_key_here
    # Optionally uncomment and set other configurations
    ```

### Running the Application

With the environment activated (`conda activate ai-desktop-assistant`):

```bash
python -m ai_desktop_assistant.main
```

or using the installed script (if poetry install added it to the path):

```bash
assistant
```

Command-line Options:

```bash
assistant --help # Show available options
assistant --debug # Enable detailed debug logging
assistant --no-speech # Disable microphone input and speaker output
assistant --light-mode # Start with the light UI theme
# Add other options defined in main.py
```

### 💻 Usage

- **Voice Input**: Click the microphone icon or use the configured hotkey (if set up) to start/stop listening. Speak naturally.
- **Text Input**: Type commands or questions into the input field at the bottom and press Enter or click the Send button.
- **Action Panel**: Click the icon (usually top-right or configured) to toggle the side panel for quick actions or settings adjustments.
- **Emergency Stop**: Press the Escape key (default) to immediately attempt to stop ongoing actions and potentially the application (behavior configurable).

### 🛠️ Development

- **Environment**: Activate the Conda environment (conda activate ai-desktop-assistant).
- **Dependencies**: Add new dependencies to pyproject.toml and run poetry lock && poetry install. If adding system-level dependencies, update environment.yml and re-run python scripts/setup_dev.py.
- **Code Quality**: Run pre-commit run --all-files to check formatting, linting, and types. Run mypy . for type checking.
- **Testing**: Run tests using pytest. Check coverage with pytest --cov.

### 🤝 Contributing

Contributions are welcome! Please follow these general steps:

- Fork the repository.
- Create a new branch for your feature or bug fix (git checkout -b feature/my-new-feature or git checkout -b fix/issue-123).
- Make your changes, ensuring code quality checks pass (pre-commit run --all-files).
- Add tests for your changes.
- Ensure all tests pass (pytest).
- Commit your changes with clear, descriptive messages (git commit -m 'feat: Add exciting new capability').
- Push your branch to your fork (git push origin feature/my-new-feature).
- Open a Pull Request against the main repository's main or develop branch.

### 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

### 🙏 Acknowledgements

- **Google Gemini API**: For the core AI capabilities.
- **LangChain**: For AI orchestration and tool integration.
- **PyQt / Qt for Python**: For the application's user interface framework.
- **pynput, mss, psutil, pygetwindow**: For cross-platform system interaction.
- **All the amazing open-source libraries used in this project!**
