import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QListWidget, QListWidgetItem, QTextEdit, 
                            QPushButton, QLabel, QScrollArea, QSplitter)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPixmap, QScreen, QPainter
from pynput import mouse

class ScreenshotManager(QMainWindow):
    screenshot_taken = pyqtSignal(QPixmap)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screenshot Manager")
        self.screenshots = []
        self.is_recording = False
        self.mouse_listener = None
        self.capture_width = 800  # Increased capture width
        self.capture_height = 600  # Increased capture height
        self.initUI()
        
        self.screenshot_taken.connect(self.add_screenshot)
        
    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        self.screen_label = QLabel("Current Screen: Auto-detect")
        
        control_layout.addWidget(self.record_button)
        control_layout.addWidget(self.screen_label)
        left_layout.addLayout(control_layout)
        
        # Screenshot list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.show_screenshots)
        left_layout.addWidget(QLabel("Screenshots:"))
        left_layout.addWidget(self.list_widget)
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Vertical scroll area for stacked screenshots
        self.preview_scroll = QScrollArea()
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_scroll.setWidget(self.preview_container)
        self.preview_scroll.setWidgetResizable(True)
        right_layout.addWidget(QLabel("Preview:"))
        right_layout.addWidget(self.preview_scroll)
        
        # Notes area
        self.notes_edit = QTextEdit()
        right_layout.addWidget(QLabel("Notes:"))
        right_layout.addWidget(self.notes_edit)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        
        self.setGeometry(100, 100, 1600, 1000)  # Larger window
        
    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_button.setText("Stop Recording")
            self.record_button.setStyleSheet("background-color: #ff6b6b;")
            self.mouse_listener = mouse.Listener(on_click=self._handle_click)
            self.mouse_listener.start()
        else:
            self.is_recording = False
            self.record_button.setText("Start Recording")
            self.record_button.setStyleSheet("")
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
    
    def get_screen_at_position(self, x, y):
        """Get the screen containing the given coordinates."""
        point = QPoint(x, y)
        screens = QApplication.screens()
        
        for screen in screens:
            geometry = screen.geometry()
            if geometry.contains(point):
                return screen, geometry
                
        return QApplication.primaryScreen(), QApplication.primaryScreen().geometry()
    
    def _handle_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed and self.is_recording:
            screen, screen_geo = self.get_screen_at_position(x, y)
            
            if screen:
                # Update screen label
                screen_index = QApplication.screens().index(screen)
                self.screen_label.setText(f"Current Screen: {screen_index + 1}")
                
                # Calculate capture region centered on click
                half_width = self.capture_width // 2
                half_height = self.capture_height // 2
                
                # Adjust coordinates relative to screen
                screen_x = x - screen_geo.x()
                screen_y = y - screen_geo.y()
                
                # Calculate region
                region = QRect(
                    screen_x - half_width,
                    screen_y - half_height,
                    self.capture_width,
                    self.capture_height
                )
                
                # Ensure region stays within screen bounds
                if region.left() < 0:
                    region.moveLeft(0)
                if region.top() < 0:
                    region.moveTop(0)
                if region.right() > screen_geo.width():
                    region.moveRight(screen_geo.width())
                if region.bottom() > screen_geo.height():
                    region.moveBottom(screen_geo.height())
                
                # Capture screenshot
                pixmap = screen.grabWindow(
                    0,
                    region.x() + screen_geo.x(),
                    region.y() + screen_geo.y(),
                    region.width(),
                    region.height()
                )
                
                self.screenshot_taken.emit(pixmap)
    
    def add_screenshot(self, pixmap):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.screenshots.append({
            'pixmap': pixmap,
            'timestamp': timestamp,
            'notes': ''
        })
        
        self.list_widget.addItem(timestamp)
        self.list_widget.setCurrentRow(self.list_widget.count() - 1)
        self.show_screenshots(self.list_widget.currentItem())
    
    def show_screenshots(self, current_item=None):
        # Clear existing previews
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Show all screenshots up to and including the selected one
        if current_item:
            current_index = self.list_widget.row(current_item)
            
            for i in range(current_index + 1):
                screenshot = self.screenshots[i]
                preview_label = QLabel()
                preview_label.setPixmap(screenshot['pixmap'])
                preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_layout.addWidget(preview_label)
                
                # Add timestamp label
                timestamp_label = QLabel(f"Screenshot {screenshot['timestamp']}")
                timestamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_layout.addWidget(timestamp_label)
                
                # Add spacing between screenshots
                spacer = QLabel()
                spacer.setFixedHeight(20)
                self.preview_layout.addWidget(spacer)
        
        # Add stretch at the end
        self.preview_layout.addStretch()
        
        # Update notes for the current screenshot
        if current_item:
            current_index = self.list_widget.row(current_item)
            self.notes_edit.setText(self.screenshots[current_index]['notes'])
            try:
                self.notes_edit.textChanged.disconnect()
            except:
                pass
            self.notes_edit.textChanged.connect(lambda: self.update_notes(current_index))
    
    def update_notes(self, index):
        self.screenshots[index]['notes'] = self.notes_edit.toPlainText()
    
    def closeEvent(self, event):
        if self.mouse_listener:
            self.mouse_listener.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    ex = ScreenshotManager()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
