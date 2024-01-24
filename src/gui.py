import os
import re

from pathlib import Path

from PySide6.QtCore import QThread, Qt, QEvent, QTimer, QCoreApplication, Signal
from PySide6.QtGui import QCursor, QPainter, QBrush, QPen, QPixmap, QIcon, QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QLineEdit,
)

from src.pipeline import Pipeline


class Gui(QMainWindow):
    to_pipeline_signal = Signal(str)  # For communication with pipeline thread

    def __init__(self, command_line_args):
        super().__init__()
        self.__setup_gui_layout()

        # The main thread of this program runs the GUI, while the pipeline (which contains the main logic) runs in a separate worker thread
        # Threading needed to run the pipeline while retaining interactivity of GUI. Communication between threads is done via signals.
        self.pipeline = Pipeline(command_line_args)
        self.pipeline_thread = QThread()
        self.pipeline.moveToThread(self.pipeline_thread)

        self.to_pipeline_signal.connect(
            self.pipeline.receive_from_gui, Qt.QueuedConnection
        )  # If the gui thread emits a signal, call pipeline.receive_from_gui()
        self.pipeline.message_signal.connect(
            self.__on_message_received, Qt.QueuedConnection
        )  # If the pipeline thread emits a signal, call  gui.__on_message_received()
        self.pipeline.animation_signal.connect(
            self.__start_animation, Qt.QueuedConnection
        )  # If the pipeline thread emits a signal, call  gui.__start_animation()

        self.pipeline_thread.started.connect(
            self.pipeline.start
        )  # Run the pipeline when the thread starts
        self.pipeline_thread.start()  # Start the thread

    def __setup_gui_layout(self):
        # Set window properties
        self.setWindowTitle("Mutiagent Development Suite")
        self.setGeometry(100, 100, 1000, 800)

        # Set the window icon
        icon_path = (
            Path(__file__).parent / "setup/media" / "app_logo.png"
        )  # Replace with the path to your icon file
        self.setWindowIcon(QIcon(str(icon_path)))

        # Scroll Area and Container for Chat Messages
        # 1. Container Widget that goes into the scroll area and will contain all messages
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.addStretch(
            0
        )  # Add a stretch on top for messages to appear at the bottom
        self.scroll_widget.setLayout(self.scroll_layout)

        # 2. Widget that takes a single child widget (scroll_widget) and displays scrollbars when it exceeds the bounds
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setObjectName(
            "myScrollArea"
        )  # unique object name for styling without affecting child widgets

        # Create a text edit for multi-line text input
        self.text_input = QLineEdit(self)
        self.text_input.installEventFilter(self)  # send text if enter is pressed
        self.text_input.setFocus()

        # Create a send button
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.__on_send_clicked)
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Typing animation setup
        self.typing_animation_widget = TypingAnimationWidget()
        self.typing_animation_timer = QTimer(self)
        self.typing_animation_timer.timeout.connect(self.__update_typing_animation)
        self.is_animation_running = False
        self.dots = 0

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.text_input)
        layout.addWidget(self.send_button)

        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Disable the input field and send button initially
        self.__enable_input(False)

        # Apply styling to certain widgets
        self.__apply_styling()

    def __apply_styling(self):
        # border-color = background-color - 20 brightness

        self.setStyleSheet(
            """
            background-color: #E6E6E6; /* Dark grey background */
        """
        )

        self.send_button.setStyleSheet(
            """
            QPushButton {
                background-color: #6D7CA3;
                color: white;
                font-size: 16px;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                margin: 4px 2px;
                border-radius: 5px;               
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #E6DFD9;
                border-style: solid;
                border-width: 0.5px;
                border-color: #B3ADA8;
                color: #1E1F21;
            }
            QPushButton:hover:enabled {
                background-color: #505C78;
            }
        """
        )

        self.text_input.setStyleSheet(
            """
            background-color: #FFFFFF;
            font-size: 16px;
            color: #1E1F21;
            border-style: solid;
            border-width: 1px;
            border-color: #CCCCCC;
            padding: 10px;
        """
        )

        self.scroll_area.setStyleSheet(
            """
            #myScrollArea {                           
                background-color: #FFFFFF;
                color: #1E1F21;
                border-style: solid;
                border-width: 1px;
                border-color: #CCCCCC;
            }
        """
        )

        self.scroll_widget.setStyleSheet(
            """
            background-color: #FFFFFF;
        """
        )

    def __enable_input(self, enable: bool):
        self.send_button.setEnabled(enable)

    def __on_message_received(self, sender, message, is_question):
        if self.is_animation_running:
            self.__stop_animation()

        message_widget = ChatMessageWidget(sender, message)
        self.scroll_layout.insertWidget(-1, message_widget)
        QTimer.singleShot(
            100,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )

        if is_question:
            self.__enable_input(True)
        else:
            self.to_pipeline_signal.emit(None)  # Continue pipeline execution

    def __on_send_clicked(self):
        user_input = self.text_input.text()
        self.text_input.clear()
        self.__enable_input(False)

        message_widget = ChatMessageWidget("You", user_input)
        self.scroll_layout.insertWidget(-1, message_widget)
        QTimer.singleShot(
            100,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )

        self.to_pipeline_signal.emit(user_input)

    def eventFilter(self, obj, event):
        # adds keyboard control
        if (
            obj == self.text_input
            and event.type() == QEvent.KeyPress
            and event.key() in [Qt.Key_Return, Qt.Key_Enter]
            and self.send_button.isEnabled()
        ):
            self.__on_send_clicked()
            return True
        return super().eventFilter(obj, event)

    def __start_animation(self, text):
        if not self.is_animation_running:
            self.is_animation_running = True
            self.animation_text = text
            self.dots = 0
            self.scroll_layout.insertWidget(
                -1, self.typing_animation_widget
            )  # Insert at top
            QTimer.singleShot(
                100,
                lambda: self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().maximum()
                ),
            )
            self.typing_animation_timer.start(300)

    def __stop_animation(self):
        if self.is_animation_running:
            self.typing_animation_timer.stop()
            self.is_animation_running = False
            self.scroll_layout.removeWidget(self.typing_animation_widget)
            self.typing_animation_widget.setParent(None)  # Remove widget from layout
            QTimer.singleShot(
                100,
                lambda: self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().maximum()
                ),
            )

    def __update_typing_animation(self):
        self.dots += 1
        self.typing_animation_widget.update_text(self.animation_text, self.dots)


class ChatMessageWidget(QWidget):
    def __init__(self, sender, message):
        super().__init__()

        # Construct the path to the image
        image_path = str(
            Path(__file__).parent
            / "setup/media"
            / "headshots"
            / f"{sender.capitalize()}.jpg"
        )

        # For debugging until final decision on bot names is made
        if not os.path.exists(image_path):
            new_sender = self.__translate_name(sender)
            image_path = str(
                Path(__file__).parent
                / "setup/media"
                / "headshots"
                / f"{new_sender.capitalize()}.jpg"
            )

        # Load the image into QPixmap and make it circular
        pixmap = QPixmap(image_path)
        mask = QPixmap(pixmap.size())
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(QPen(Qt.white))
        painter.drawEllipse(0, 0, mask.width(), mask.height())
        painter.end()

        pixmap.setMask(mask.mask())
        scaled_pixmap = pixmap.scaled(
            50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Image Label
        self.image_label = QLabel(self)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setFixedSize(50, 50)

        # Text Label
        self.text_label = QLabel(self)
        self.text_label.setOpenExternalLinks(True)
        formatted_message = self.__add_formatting(sender, message)
        self.text_label.setText(f"<b>{sender}</b>: {formatted_message}")
        self.text_label.setWordWrap(True)
        text_background_color = "#C8CFE3" if sender == "You" else "#E2DED4"
        self.text_label.setStyleSheet(
            f"""
                background-color: {text_background_color};
                border-radius: 10px;
                padding: 15px;
            """
        )

        # Layout
        layout = QHBoxLayout()

        if sender == "You":
            # User message: Align to the right
            layout.addWidget(
                self.text_label, 1, alignment=Qt.AlignVCenter
            )  # Add text label first for right alignment
            layout.addWidget(self.image_label, alignment=Qt.AlignVCenter)  # Then image
            self.text_label.setAlignment(Qt.AlignRight)

        else:
            # Other sender: Align to the left
            layout.addWidget(self.image_label, alignment=Qt.AlignVCenter)
            layout.addWidget(self.text_label, 1, alignment=Qt.AlignVCenter)
            self.text_label.setAlignment(Qt.AlignLeft)

        self.setLayout(layout)

    def __translate_name(self, name):
        """For debugging purposes until final decision on names is made"""
        d = {
            "Orchestrator": "Santiago",
            "Database Dev": "Bukarest",
            "Database Tester": "Testarest",
            "Database Doc": "Docarest",
            "Backend Dev": "Nikosia",
            "Backend Tester": "Testosia",
            "Backend Doc": "Docosia",
            "Frontend Dev": "Amsterdam",
            "Frontend Tester": "Testerdam",
            "Frontend Doc": "Docerdam",
        }
        return d[name]

    def __add_formatting(self, sender, message):
        role = sender[-3:]
        layer = sender[:-4]

        # Add code formatting
        if role == "Dev":
            # Add line breaks if line > max_line_length
            max_line_length = 120
            lines = message.split("\n")
            for i, line in enumerate(lines):
                if len(line) > max_line_length:
                    new_line = ""
                    while len(line) > max_line_length:
                        new_line += line[:max_line_length] + "\n"
                        line = line[max_line_length:]
                    new_line += line
                    lines[i] = new_line
            message = "\n".join(lines)

            # To display code properly the html tags need to be replaced with their html entity equivalents
            message = message.replace(" ", "&nbsp;")
            message = message.replace("<", "&lt;").replace(">", "&gt;")

            # Comment highlighting
            if layer == "Backend":
                message = re.sub(
                    r"(#.*?$)",
                    r'<span style="color: gray; font-style: italic;">\1</span>',
                    message,
                    flags=re.MULTILINE,
                )
            elif layer == "Database":
                message = re.sub(
                    r"(--.*?$)",
                    r'<span style="color: gray; font-style: italic;">\1</span>',
                    message,
                    flags=re.MULTILINE,
                )
            elif layer == "Frontend":
                message = re.sub(
                    r"(//.*?$)",
                    r'<span style="color: gray; font-style: italic;">\1</span>',
                    message,
                    flags=re.MULTILINE,
                )

            # Define basic keywords that should be highlighted
            keywords = {
                "Backend": [
                    "def",
                    "return",
                    "class",
                    "None",
                    "True",
                    "False",
                    "self",
                    "init",
                    "lambda",
                    "global",
                    "nonlocal",
                    "yield",
                    "with",
                    "as",
                    "assert",
                    "del",
                    "from",
                    "global",
                    "nonlocal",
                    "pass",
                    "raise",
                    "yield",
                    "if",
                    "else",
                    "elif",
                    "for",
                    "while",
                    "break",
                    "continue",
                    "try",
                    "except",
                    "finally",
                    "in",
                    "is",
                    "and",
                    "or",
                    "not",
                    "import",
                    "from",
                    "as",
                    "try",
                    "except",
                    "finally",
                    "with",
                    "as",
                    "exec",
                    "print",
                    "int",
                    "float",
                    "str",
                    "list",
                    "dict",
                    "tuple",
                    "set",
                    "bool",
                    "bytes",
                    "object",
                ],
                "Database": [
                    "SELECT",
                    "FROM",
                    "WHERE",
                    "GROUP&nbsp;BY",
                    "ORDER&nbsp;BY",
                    "LIMIT",
                    "OFFSET",
                    "HAVING",
                    "DISTINCT",
                    "INSERT INTO",
                    "VALUES",
                    "UPDATE",
                    "SET",
                    "DELETE",
                    "ALTER&nbsp;TABLE",
                    "DROP&nbsp;TABLE",
                    "CREATE&nbsp;TABLE",
                    "CREATE&nbsp;INDEX",
                    "AND",
                    "OR",
                    "NOT",
                    "IN",
                    "BETWEEN",
                    "IS&nbsp;NULL",
                    "IS&nbsp;NOT&nbsp;NULL",
                ],
                "Frontend": [
                    "<!DOCTYPE html>",
                    "<html>",
                    "</html>",
                    "<body>",
                    "</body>",
                    "<script>",
                    "</script>",
                    "<style>",
                    "</style>",
                    "<link>",
                    "<meta>",
                    "<head>",
                    "</head>",
                    "<title>",
                    "</title>",
                    "<header>",
                    "</header>",
                    "<footer>",
                    "</footer>",
                    "<main>",
                    "</main>",
                    "<div>",
                    "</div>",
                    "<span>",
                    "</span>",
                    "<p>",
                    "</p>",
                    "<a>",
                    "</a>",
                    "<img>",
                    "<ul>",
                    "<ol>",
                    "<li>",
                    "<section>",
                    "</section>",
                    "<button>",
                    "</button>",
                    "<input>",
                    "<label>",
                    "<form>",
                    "</form>",
                    "<select>",
                    "<option>",
                    "<textarea>",
                    "<table>",
                    "<tr>",
                    "<td>",
                    "<th>",
                    "<thead>",
                    "<tbody>",
                    "<tfoot>",
                ],
            }

            # Apply keyword highlighting
            for kw in keywords[layer]:
                message = re.sub(
                    r"\b" + re.escape(kw) + r"\b",
                    f'<span style="color: #4654B3; font-weight: bold;">{kw}</span>',
                    message,
                )

        # Add line breaks
        if role == "Doc" or role == "Dev":
            message = "<br><br>" + message.replace("\n", "<br>")

        return message


class TypingAnimationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("")
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_text(self, text, dots):
        self.label.setText(f'<span style="color: gray">{text}{"." * (dots % 4)}</span>')
