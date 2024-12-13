import os
import sys
import json
import threading
from PySide6.QtCore import QUrl, QTimer, QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtGui import QIcon

from src.controllers.resource import Resources

class ResourceThread(QThread):
    update_cpu_signal = Signal(float)
    update_memory_signal = Signal(object)
    update_gpu_signal = Signal(list)

    def __init__(self, resources):
        super().__init__()
        self.resources = resources

    def run(self):
        while True:
            cpu_usage = self.resources.get_cpu_usage()
            self.update_cpu_signal.emit(cpu_usage)

            total_memory, used_memory, free_memory, memory_percent = self.resources.get_memory_usage()
            memory_data = {
                "totalMemory": total_memory,
                "usedMemory": used_memory,
                "freeMemory": free_memory,
                "memoryPercent": memory_percent
            }
            self.update_memory_signal.emit(memory_data)

            gpu_info = self.resources.get_gpu_usage()
            self.update_gpu_signal.emit(gpu_info)

            self.msleep(1000)


class CreateWindow:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.window = QMainWindow()
        self.window.setWindowTitle("Задачный диспетчер")
        self.window.setGeometry(100, 100, 1000, 600)

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.window.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        self.central_widget.setLayout(self.layout)
        self.window.setCentralWidget(self.central_widget)

        self.channel = QWebChannel()
        self.resources = Resources()
        self.channel.registerObject("resources", self.resources)

        self.web_view.page().setWebChannel(self.channel)

        self.load_html()

        self.resource_thread = ResourceThread(self.resources)
        self.resource_thread.update_cpu_signal.connect(self.update_cpu)
        self.resource_thread.update_memory_signal.connect(self.update_memory)
        self.resource_thread.update_gpu_signal.connect(self.update_gpu)
        self.resource_thread.start()

    def load_html(self):
        html_file = os.path.join(os.path.dirname(__file__), "templates", "taskmenager.html")
        html_file = os.path.normpath(html_file)

        if os.path.exists(html_file):
            self.web_view.setUrl(QUrl.fromLocalFile(html_file))
        else:
            print(f"HTML-файл не найден: {html_file}")

    def update_cpu(self, cpu_usage):
        self.web_view.page().runJavaScript(f"updateCPUUsage({cpu_usage});")

    def update_memory(self, memory_data):
        self.web_view.page().runJavaScript(f"updateMemoryUsage({memory_data['totalMemory']}, {memory_data['usedMemory']}, {memory_data['freeMemory']}, {memory_data['memoryPercent']});")

    def update_gpu(self, gpu_info):
        self.web_view.page().runJavaScript(f"updateGPUInfo({json.dumps(gpu_info)});")

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    window = CreateWindow()
    window.run()
