"""
Help screen for the PyQt5-based AI Desktop Assistant.
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

logger = logging.getLogger(__name__)


class HelpScreen(QWidget):
    """Help screen with documentation and usage instructions."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up the help UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml(
            """
        <!DOCTYPE html>
        <html><head><style>
            body { font-family: sans-serif; line-height: 1.4; }
            h2 { color: #6fa8dc; border-bottom: 1px solid #555; padding-bottom: 5px; }
            h3 { color: #e0e0e0; margin-top: 15px; margin-bottom: 5px; }
            ul, ol { margin-left: 20px; }
            li { margin-bottom: 6px; }
            p { margin-bottom: 10px; }
            b { color: #a2cffe; }
            code { background-color: #3a3a3a; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
            .warning { color: #f9cb9c; font-weight: bold; }
        </style></head><body>
        <h2>AI Desktop Assistant Help</h2>

        <h3>Overview</h3>
        <p>This application uses AI to understand your screen and follow your voice commands to interact with your computer.</p>

        <h3>Requirements</h3>
        <ul>
            <li>A working microphone connected and selected as default input.</li>
            <li>A stable internet connection.</li>
            <li>An <b>API key</b> with billing enabled (vision models process images and can incur costs). Enter your key in the <b>Settings</b> tab.</li>
            <li>Required Python packages installed (app checks on startup).</li>
            <li>Appropriate OS permissions (Microphone access, potentially Accessibility/Input Monitoring on macOS for hotkeys/control).</li>
        </ul>

        <h3>First Use</h3>
        <ol>
            <li>Go to the <b>Settings</b> tab.</li>
            <li>Enter your <b>API key</b>.</li>
            <li>Click <b>Apply Settings</b>.</li>
            <li>Go back to the <b>Dashboard</b> tab.</li>
            <li>If you have multiple monitors, select the one you want the assistant to "see" using the radio buttons. Click <b>Refresh Monitor List</b> if needed.</li>
            <li>Click the green <b>Start Assistant</b> button.</li>
            <li>Your OS might ask for microphone permission the first time – please allow it.</li>
        </ol>

        <h3>Using the Assistant</h3>
        <ul>
            <li>Wait for the status bar to say "Listening...".</li>
            <li>Speak your command clearly. Examples:
                <ul>
                    <li>"Click the <b>File</b> menu."</li>
                    <li>"Type <code>Project Report Q3</code> into the search bar."</li>
                    <li>"Open <b>Notepad</b>." (Might require you to tell it how, e.g., "Press Windows key, type notepad, press enter")</li>
                    <li>"Scroll down the page."</li>
                    <li>"Press <b>Control S</b> to save." (Say "Control", not "Ctrl")</li>
                    <li>"What is the title of the active window?"</li>
                    <li>"Move the mouse to <b>x: 850, y: 320</b>."</li>
                </ul>
             </li>
            <li>The assistant will analyze the screen, state its plan (spoken and/or via caption if enabled), and then attempt to perform the actions (clicks, typing etc.).</li>
        </ul>

        <h3>Controls & Hotkeys</h3>
        <ul>
            <li><b>Start/Stop Assistant:</b> Use the button on the Dashboard.</li>
            <li><b>Pause/Resume:</b> Press <b>F12</b> (default) or your configured key. Button also available.</li>
            <li><b>Emergency Stop:</b> Press <b>ESC</b> (default) or your configured key. <span class="warning">This immediately stops all actions and the assistant.</span> Button also available.</li>
            <li>Hotkey changes in <b>Settings</b> require an assistant restart to take effect.</li>
        </ul>

        <h3>Settings Explained</h3>
        <ul>
            <li><b>API Key:</b> Your secret key for accessing AI services. Keep it safe!</li>
            <li><b>Model:</b> AI model for screen analysis.</li>
            <li><b>Voice Feedback:</b> Toggle spoken responses using Text-to-Speech (TTS).</li>
            <li><b>Screen Captions:</b> Show assistant's response text as an overlay on your screen.</li>
            <li><b>TTS Settings:</b> Choose "Standard" (offline, faster, less natural) or "Natural" (online, better quality). Adjust speed only for Standard voice.</li>
            <li><b>Screen Analysis Interval:</b> How often the assistant takes a screenshot to understand context for *each command*. Does not affect preview FPS.</li>
            <li><b>Hotkeys:</b> Customize keyboard shortcuts for critical functions.</li>
        </ul>

        <h3>Troubleshooting</h3>
        <ul>
            <li><b>"Could not understand audio":</b> Check microphone connection/settings in OS, ensure mic access permission, reduce background noise, speak clearly.</li>
            <li><b>"API Error":</b> Check your API key, ensure billing is active, check internet connection.</li>
            <li><b>Natural Voice Not Working:</b> Check API key/billing, internet. Ensure required packages installed correctly.</li>
            <li><b>Assistant Performs Wrong Action:</b> The AI might misinterpret the screen or your command. Try being more specific. Use Pause or Emergency Stop if it's doing something unintended.</li>
            <li><b>Hotkeys Not Working:</b> Ensure app has focus. On macOS, check System Settings > Privacy & Security > Accessibility and Input Monitoring. On Windows, sometimes running as Administrator helps (use with caution). Restart the assistant after changing hotkeys.</li>
            <li><b>General Issues:</b> Check the <b>Activity Log</b> on the Dashboard for detailed error messages.</li>
        </ul>
        </body></html>
        """
        )

        layout.addWidget(help_text)
