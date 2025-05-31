from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QGraphicsDropShadowEffect, QTextEdit, QInputDialog
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QObject, QThread, pyqtSlot
import threading
import subprocess
import os
import sys # Import sys
import pyautogui as gui

# --- Worker Thread for Running Subprocess ---
class SubprocessWorker(QObject):
    # Signal to emit output lines
    outputReady = pyqtSignal(str)
    # Signal when process finishes
    processFinished = pyqtSignal()

    def __init__(self, main_py_path, project_root):
        super().__init__()
        self.main_py_path = main_py_path
        self.project_root = project_root
        self.process = None
        self._isRunning = True

    def run(self):
        try:
            print(f"Executing: {self.main_py_path}") # Debug print
            # Use python3 for macOS/Linux, python for Windows might be needed
            python_executable = sys.executable # Use the same python that runs the UI
            # Add -u for unbuffered output from the Python subprocess
            command = [python_executable, "-u", self.main_py_path]

            # Start the process with proper environment
            # Use line buffering (-u) and handle potential encoding issues
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,  # <-- Add this to enable writing to stdin
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8', # Explicitly set encoding
                errors='replace', # Handle potential decoding errors
                bufsize=1, # Line buffering
                cwd=self.project_root, # Set working directory to project root
                env={**os.environ, 'PYTHONPATH': self.project_root} # Ensure Python can find your modules
            )

            # --- Real-time Output Reading ---
            # Read stdout line by line
            if self.process.stdout:
                for line in iter(self.process.stdout.readline, ''):
                    if not self._isRunning:
                        break
                    self.outputReady.emit(line.strip())
                self.process.stdout.close()

            # Read stderr line by line (optional, but good for debugging)
            stderr_output = ""
            if self.process.stderr:
                for line in iter(self.process.stderr.readline, ''):
                     if not self._isRunning:
                        break
                     stderr_output += line # Collect stderr
                self.process.stderr.close()
                if stderr_output:
                    self.outputReady.emit(f"STDERR: {stderr_output.strip()}") # Emit stderr as well

            # Wait for the process to terminate
            self.process.wait()

        except FileNotFoundError:
             self.outputReady.emit(f"Error: Python executable not found or '{self.main_py_path}' does not exist.")
        except Exception as e:
            self.outputReady.emit(f"Subprocess error: {str(e)}")
            import traceback
            self.outputReady.emit(traceback.format_exc()) # Emit full traceback
        finally:
            self.processFinished.emit()
            print("Subprocess worker finished.") # Debug print

    def stop(self):
        self._isRunning = False
        if self.process and self.process.poll() is None: # Check if process is running
            print("Terminating subprocess...")
            self.process.terminate() # Try to terminate gracefully
            try:
                self.process.wait(timeout=5) # Wait a bit
            except subprocess.TimeoutExpired:
                print("Subprocess did not terminate gracefully, killing...")
                self.process.kill() # Force kill if necessary
            print("Subprocess stopped.")

    @pyqtSlot(str) # Slot to receive input from UI and send to subprocess
    def send_input_to_subprocess(self, text):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(text + '\n') # Add newline, as readline() expects it
                self.process.stdin.flush()
            except Exception as e:
                self.outputReady.emit(f"Error writing to subprocess stdin: {e}")

# --- Size Animator (No changes needed) ---
class SizeAnimator(QObject):
    sizeChanged = pyqtSignal(QSize)

    def animate(self, size, delay=0):
        QTimer.singleShot(delay, lambda: self.sizeChanged.emit(size))

# --- Main UI Class ---
class JarvisUI(QWidget):
    # Signal to request stopping the worker
    stopWorker = pyqtSignal()
    sendInputToWorker = pyqtSignal(str) # Signal to send input text to the worker

    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.worker = None
        self.is_listening = False # Flag to track if main.py is running
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Jarvis UI')
        # Reduced initial size for better screen fit if not full screen
        # self.setGeometry(80, 80, 800, 600)
        self.setGeometry(80, 80, 400, 400) # Original size

        # Set window attributes for transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10) # Reduced spacing

        # --- Microphone GIF ---
        self.mic_label = QLabel(self)
        self.add_gif_to_label(self.mic_label,
                              f"{os.getcwd()}/USER_INTERFACE/jarvis_ui.gif",
                              size=(720, 220), # Keep original GIF size
                              alignment=Qt.AlignCenter)
        self.mic_label.setAlignment(Qt.AlignCenter)
        # Connect click event
        self.mic_label.mousePressEvent = self.toggle_listening

        # --- Text Area for Output ---
        self.output_text_area = QTextEdit(self)
        self.output_text_area.setReadOnly(True)
        # Basic styling for the text area
        self.output_text_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.6); /* Semi-transparent black */
                color: #00FF00; /* Green text */
                border: 1px solid #00FF00; /* Green border */
                border-radius: 5px;
                font-family: Consolas, Courier New, monospace;
                font-size: 11pt; /* Slightly smaller font */
            }
        """)
        # Set a fixed height or allow it to expand
        self.output_text_area.setFixedHeight(150) # Example fixed height

        # --- Text Input Field and Send Button ---
        input_field_layout = QHBoxLayout() # Horizontal layout for input field and button

        self.user_input_field = QLineEdit(self)
        self.user_input_field.setPlaceholderText("Type your command or message here...")
        self.user_input_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.7); /* Semi-transparent black */
                color: #00FF00; /* Green text */
                border: 1px solid #00FF00; /* Green border */
                border-radius: 3px;
                padding: 5px;
                font-family: Consolas, Courier New, monospace;
                font-size: 10pt;
            }
        """)
        self.user_input_field.returnPressed.connect(self.send_typed_input_to_worker) # Send on Enter

        self.send_text_button = QPushButton("Send", self)
        self.send_text_button.setStyleSheet("""
            QPushButton {
                background-color: #003300; /* Darker green */
                color: #00FF00; /* Green text */
                border: 1px solid #00FF00;
                border-radius: 3px;
                padding: 5px 10px;
                font-family: Consolas, Courier New, monospace;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #005500; /* Lighter green on hover */
            }
            QPushButton:pressed {
                background-color: #002200; /* Even darker green when pressed */
            }
        """)
        self.send_text_button.clicked.connect(self.send_typed_input_to_worker)

        input_field_layout.addWidget(self.user_input_field)
        input_field_layout.addWidget(self.send_text_button)

        # --- Add Widgets to Layout ---
        main_layout.addWidget(self.mic_label, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.output_text_area) # Add text area below GIF
        main_layout.addLayout(input_field_layout) # Add the input field and button layout

        # --- Size Animator ---
        self.size_animator = SizeAnimator()
        self.size_animator.sizeChanged.connect(self.mic_label.setFixedSize)

    def add_gif_to_label(self, label, gif_path, size=None, alignment=None):
        # Ensure the path exists
        if not os.path.exists(gif_path):
            print(f"Error: GIF not found at {gif_path}")
            label.setText("GIF not found") # Placeholder text
            if size: label.setFixedSize(*size)
            if alignment: label.setAlignment(alignment)
            return

        movie = QMovie(gif_path)
        if not movie.isValid():
             print(f"Error: Could not load GIF {gif_path}")
             label.setText("Invalid GIF")
             if size: label.setFixedSize(*size)
             if alignment: label.setAlignment(alignment)
             return

        label.setMovie(movie)
        self.movie = movie # Save reference to the movie
        movie.start()

        if size:
            label.setFixedSize(*size)

        if alignment:
            label.setAlignment(alignment)

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.black) # Set shadow color for visibility
        shadow.setOffset(3, 3)    # Give it a slight offset
        label.setGraphicsEffect(shadow)

    def toggle_listening(self, event):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        if self.is_listening: # Prevent starting multiple instances
            return

        self.is_listening = True
        self.output_text_area.clear() # Clear previous output
        self.output_text_area.append("Starting Jarvis...")
        print("Attempting to start listening...") # Debug print

        # --- Prepare and Start Worker Thread ---
        try:
            # Get the project root directory (where main.py is located)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Construct the path to main.py
            path_to_main_py = os.path.join(project_root, "main.py")

            if not os.path.exists(path_to_main_py):
                 self.handle_output(f"Error: main.py not found at {path_to_main_py}")
                 self.is_listening = False
                 return

            # Create worker and thread
            self.worker_thread = QThread()
            self.worker = SubprocessWorker(path_to_main_py, project_root)
            self.worker.moveToThread(self.worker_thread)

            # Connect signals/slots
            self.worker.outputReady.connect(self.handle_output)
            self.worker.processFinished.connect(self.on_process_finished)
            # Connect the thread's started signal to the worker's run method
            self.worker_thread.started.connect(self.worker.run)
            # Connect stop signal
            self.stopWorker.connect(self.worker.stop)
            # Connect signal to send input from UI to worker
            self.sendInputToWorker.connect(self.worker.send_input_to_subprocess)

            # Start the thread
            self.worker_thread.start()

            # Animate GIF slightly bigger when starting
            self.size_animator.animate(QSize(750, 230)) # Slightly larger
            self.size_animator.animate(QSize(720, 220), delay=500) # Back to normal


        except Exception as e:
            self.handle_output(f"Error setting up worker thread: {str(e)}")
            import traceback
            self.handle_output(traceback.format_exc())
            self.is_listening = False # Reset flag on error

    def stop_listening(self):
        if not self.is_listening or not self.worker_thread or not self.worker:
            return

        print("Attempting to stop listening...") # Debug print
        self.output_text_area.append("Stopping Jarvis...")
        self.stopWorker.emit() # Signal the worker to stop the subprocess

        # Optionally wait a short time for cleanup, but don't block UI long
        # self.worker_thread.quit()
        # self.worker_thread.wait(1000) # Wait max 1 second

        # The on_process_finished slot will handle final cleanup

    @pyqtSlot(str) # Decorator to mark this as a slot
    def handle_output(self, output):
        # --- Check for input request magic string ---
        magic_string = "__UI_EXPECTING_INPUT_START__:"
        if output.startswith(magic_string):
            prompt = output[len(magic_string):].strip()
            self.request_user_input(prompt)
            # Don't display the magic string itself in the output area
            return

        # Ignore empty or whitespace-only output
        if not output.strip():
            return

        # Append output to the text area
        self.output_text_area.append(output)
        self.output_text_area.ensureCursorVisible() # Scroll to the bottom

        # --- Optional: Animate GIF based on output ---
        # You could add logic here to change animation based on keywords
        # For example, if "Jarvis:" is in the output, make it pulse
        if "Jarvis:" in output or "human:" in output:
             # Simple pulse animation
             self.size_animator.animate(QSize(750, 230)) # Slightly larger
             self.size_animator.animate(QSize(720, 220), delay=300) # Back to normal after 300ms

    def send_typed_input_to_worker(self):
        """Sends text from the user_input_field to the worker subprocess."""
        text_to_send = self.user_input_field.text().strip()
        # Always send input to the worker, even if empty
        if text_to_send:
            # Display in the UI's output area
            self.output_text_area.append(f"You: {text_to_send}")
            self.output_text_area.ensureCursorVisible()
        self.sendInputToWorker.emit(text_to_send) # Send to the worker
        self.user_input_field.clear() # Clear the input field

    def request_user_input(self, prompt_text):
        text, ok = QInputDialog.getText(self, "User Input Required", prompt_text)
        if ok:
            self.sendInputToWorker.emit(str(text)) # Send the entered text to the worker
        else:
            # User cancelled the dialog, send an empty line or a specific signal
            self.sendInputToWorker.emit("") # Send empty string if cancelled

    @pyqtSlot() # Decorator for the finished signal
    def on_process_finished(self):
        print("Process finished signal received.") # Debug print
        self.output_text_area.append("Jarvis process finished.")
        self.is_listening = False

        # Clean up thread
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait(500) # Wait briefly for thread cleanup
            self.worker_thread = None
        self.worker = None

        # Reset GIF size
        self.size_animator.animate(QSize(720, 220))

    # --- Graceful Shutdown on UI Close ---
    def closeEvent(self, event):
        print("Close event triggered.")
        self.stop_listening() # Attempt to stop the subprocess if running
        # Wait a bit for the thread/process to potentially clean up
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(1000) # Wait max 1 sec
        event.accept() # Accept the close event


if __name__ == '__main__':
    # Minimize all windows on macOS (Keep if desired)
    try:
        gui.hotkey("command", "m")
    except Exception as e:
        print(f"Could not minimize windows (pyautogui error): {e}")

    app = QApplication(sys.argv) # Use sys.argv

    jarvis_ui = JarvisUI()
    # Make it full screen or regular window
    # jarvis_ui.showFullScreen()
    jarvis_ui.show() # Show as a normal window initially

    sys.exit(app.exec_()) # Proper way to exit PyQt application
