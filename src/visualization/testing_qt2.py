from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QScrollArea, QLabel, QLineEdit
from PySide6.QtCore import QObject, Signal, QThread, Qt, QEvent, QTimer
from PySide6.QtGui import QCursor, QPainter, QBrush, QPen, QPixmap, QIcon

import sys

from PySide6.QtGui import QPixmap
from pathlib import Path


class Pipeline(QObject):
    message_signal = Signal(str, str, bool)

    def __init__(self):
        super().__init__()
        self._input = None
        self._pause_execution = False

    def run(self):
        self.send_message(sender="Santiago", message="Hi there!")
        response = self.send_message(sender="Amsterdam", message="What is your name?", is_question=True)

        response = self.send_message(sender="Nikosia", message=f"Hi {response}, how is it going?", is_question=True)
        self.send_message(sender="Bukarest", message="Great, Bye!")
        # TBC
 
    def send_message(self, sender, message, is_question=False):
        self.message_signal.emit(sender, message, is_question)
        self._pause_execution = True

        while self._pause_execution:
            QThread.msleep(100)  

        return self._input 
    
    def receive_message(self, input=None):
        self._input = input
        self._pause_execution = False
    

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Mutiagent Development Suite")
        self.setGeometry(100, 100, 800, 600)

        # Set the window icon
        icon_path = Path(__file__).parent / "app_logo.png"  # Replace with the path to your icon file
        self.setWindowIcon(QIcon(str(icon_path)))

        # Scroll Area and Container for Chat Messages
        # 1. Container Widget that goes into the scroll area and will contain all messages
        self.scroll_widget = QWidget()  
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.addStretch(0)  # Add a stretch on top for messages to appear at the bottom
        self.scroll_widget.setLayout(self.scroll_layout)

        # 2. Widget that takes a single child widget (scroll_widget) and displays scrollbars when it exceeds the bounds
        self.scroll_area = QScrollArea(self) 
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setObjectName("myScrollArea")  # unique object name for styling without affecting child widgets

        
        # Create a text edit for multi-line text input
        self.text_input = QLineEdit(self)
        self.text_input.installEventFilter(self) # send text if enter is pressed
        self.text_input.setFocus()

        # Create a send button
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Typing animation setup
        self.typing_animation_widget = TypingAnimationWidget()
        self.typing_animation_timer = QTimer(self)
        self.typing_animation_timer.timeout.connect(self.update_typing_animation)
        self.is_typing_animation_running = False
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
        self.enable_input(False)

        # Apply styling to certain widgets
        self.__apply_styling()

        # Initialize the program and the worker thread
        # Threading needed to run the pipeline while retaining interactivity of GUI
        self.pipeline = Pipeline()
        self.pipeline_thread = QThread() 
        self.pipeline.moveToThread(self.pipeline_thread)

        self.pipeline_thread.started.connect(self.pipeline.run)
        self.pipeline.message_signal.connect(self.on_message_received)
        self.pipeline_thread.start()

    def __apply_styling(self):
         # border-color = background-color - 20 brightness

        self.send_button.setStyleSheet("""
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
                color: #1E1F21;
            }
            QPushButton:hover:enabled {
                background-color: #505C78;
            }
        """)

        self.text_input.setStyleSheet("""
            background-color: #FFFFFF;
            font-size: 16px;
            color: #1E1F21;
            border-style: solid;
            border-width: 1px;
            border-color: #CCCCCC;
            padding: 10px;
        """)

        self.scroll_area.setStyleSheet("""
            #myScrollArea {                           
                background-color: #FFFFFF;
                color: #1E1F21;
                border-style: solid;
                border-width: 1px;
                border-color: #CCCCCC;
            }
        """)

        self.scroll_widget.setStyleSheet("""
            background-color: #FFFFFF;
        """)






    def enable_input(self, enable: bool):
        self.send_button.setEnabled(enable)

    def on_message_received(self, sender, message, is_question):
        self.start_typing_animation(sender)
        QTimer.singleShot(2000, lambda: self.add_message_to_scroll_area(sender, message, is_question))

    def on_send_clicked(self):
        user_input = self.text_input.text()

        message_widget = ChatMessageWidget("You", user_input, is_user=True)
        self.scroll_layout.insertWidget(-1, message_widget)
        self.scroll_area.verticalScrollBar().setValue(0) # Adjust scroll position if needed

        self.text_input.clear()
        self.enable_input(False)
        self.pipeline.receive_message(user_input)


    def add_message_to_scroll_area(self, sender, message, is_question):
        self.stop_typing_animation()
        
        message_widget = ChatMessageWidget(sender, message)
        self.scroll_layout.insertWidget(-1, message_widget)
        self.scroll_area.verticalScrollBar().setValue(0) # Adjust scroll position if needed

        if is_question:
            self.enable_input(True)
        else:
            self.pipeline.receive_message() # Continue pipeline execution


    def eventFilter(self, obj, event):
        # adds keyboard control
        if obj == self.text_input and event.type() == QEvent.KeyPress and event.key() in [Qt.Key_Return, Qt.Key_Enter] and self.send_button.isEnabled():
            self.on_send_clicked()
            return True
        return super().eventFilter(obj, event)
   

    def start_typing_animation(self, sender):
        if not self.is_typing_animation_running:
            self.is_typing_animation_running = True
            self.typing_sender = sender
            self.dots = 0
            self.scroll_layout.insertWidget(-1, self.typing_animation_widget)  # Insert at top
            self.typing_animation_timer.start(300)

    def stop_typing_animation(self):
        if self.is_typing_animation_running:
            self.typing_animation_timer.stop()
            self.is_typing_animation_running = False
            self.scroll_layout.removeWidget(self.typing_animation_widget)
            self.typing_animation_widget.setParent(None)  # Remove widget from layout

    def update_typing_animation(self):
        self.dots += 1
        self.typing_animation_widget.update_text(self.typing_sender, self.dots)




class ChatMessageWidget(QWidget):
    def __init__(self, sender, message, is_user=False):
        super().__init__()

        # Construct the path to the image
        image_path = str(Path(__file__).parent / "headshots" / f"{sender.capitalize()}.jpg")
        
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
        scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Image Label
        self.image_label = QLabel(self)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setFixedSize(50, 50)

        # Text Label
        self.text_label = QLabel(f"<b>{sender}</b>: {message}", self)
        self.text_label.setWordWrap(True)
        text_background_color = "#C8CFE3" if is_user else "#E2DED4"
        self.text_label.setStyleSheet(f"""
            background-color: {text_background_color};
            border-radius: 10px;
            padding: 15px;
        """)

        # Layout
        layout = QHBoxLayout()

        if is_user:
            # User message: Align to the right
            layout.addWidget(self.text_label, 1, alignment=Qt.AlignVCenter)  # Add text label first for right alignment
            layout.addWidget(self.image_label, alignment=Qt.AlignVCenter)    # Then image
            self.text_label.setAlignment(Qt.AlignRight)
        
        else:
            # Other sender: Align to the left
            layout.addWidget(self.image_label, alignment=Qt.AlignVCenter)
            layout.addWidget(self.text_label, 1, alignment=Qt.AlignVCenter)
            self.text_label.setAlignment(Qt.AlignLeft)

        self.setLayout(layout)



class TypingAnimationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("is typing...")
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_text(self, sender, dots):
        self.label.setText(f"{sender} is typing{'.' * (dots % 4)}")





def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #E6E6E6; /* Dark grey background */
        }
    """)
                         

    main_window = ChatWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()