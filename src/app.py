from __future__ import annotations

from . import backend  # noqa: F401  — must run before other matplotlib imports

from PyQt6.QtCore import QEventLoop, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
	QApplication,
	QWidget,
	QVBoxLayout,
	QPushButton,
	QLineEdit,
	QLabel,
	QFileDialog,
	QStackedWidget,
	QProgressBar,
)
from PIL import Image
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

import numpy as np

from .grid import create_grid
from .parsing import parse_function
from .transform import warp_image_rgb


class TransformWorker(QThread):
	progress = pyqtSignal(int)
	finished_ok = pyqtSignal(object)
	failed = pyqtSignal(str)

	def __init__(self, image: Image.Image, f):
		super().__init__()
		self._image = image
		self._f = f

	def run(self) -> None:
		try:
			self.progress.emit(2)
			img_np = np.array(self._image)
			self.progress.emit(6)

			def on_progress(p: int) -> None:
				# warp reports 0..100 → map to 6..99 on the bar
				self.progress.emit(6 + int(p * 93 / 100))

			out = warp_image_rgb(img_np, self._f, progress=on_progress)
			self.finished_ok.emit(out)
		except Exception as e:
			self.failed.emit(str(e))


class ConformalApp(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle("Conformal Mapping Visualizer")

		layout = QVBoxLayout()

		self.label = QLabel("Enter f(z):")
		layout.addWidget(self.label)

		self.input = QLineEdit()
		self.input.setText("z**2")
		layout.addWidget(self.input)

		self.visualize_btn = QPushButton("New Function")
		self.visualize_btn.clicked.connect(self.start_new_animation)
		layout.addWidget(self.visualize_btn)

		self.upload_btn = QPushButton("Upload Image")
		self.upload_btn.clicked.connect(self.upload_image)
		layout.addWidget(self.upload_btn)

		self.clear_image_btn = QPushButton("Clear Image")
		self.clear_image_btn.clicked.connect(self.clear_image)
		layout.addWidget(self.clear_image_btn)

		self.transform_stack = QStackedWidget()
		self.transform_btn = QPushButton("Apply Transformation")
		self.transform_btn.clicked.connect(self.apply_transformation)
		self.transform_progress = QProgressBar()
		self.transform_progress.setRange(0, 100)
		self.transform_progress.setTextVisible(True)
		self.transform_progress.setFormat("%p%")
		btn_h = max(self.transform_btn.sizeHint().height(), 28)
		self.transform_btn.setMinimumHeight(btn_h)
		self.transform_progress.setMinimumHeight(btn_h)
		self.transform_stack.setMinimumHeight(btn_h)
		self.transform_stack.addWidget(self.transform_btn)
		self.transform_stack.addWidget(self.transform_progress)
		layout.addWidget(self.transform_stack)

		self.save_btn = QPushButton("Save Image")
		self.save_btn.clicked.connect(self.save_image)
		self.save_btn.setEnabled(False)
		layout.addWidget(self.save_btn)

		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		layout.addWidget(self.canvas)

		self.setLayout(layout)

		self.ax = self.figure.add_subplot(111)
		self.ax_left = None
		self.ax_right = None

		self.anim = None
		self._transform_worker: TransformWorker | None = None

	def _setup_animation_axes(self):
		self.figure.clear()
		self.ax = self.figure.add_subplot(111)
		self.ax_left = None
		self.ax_right = None

	def _setup_image_axes(self):
		self.figure.clear()
		self.ax = None
		self.ax_left, self.ax_right = self.figure.subplots(1, 2)
		self.figure.tight_layout()

	def _empty_image_panels(self):
		self.ax_left.clear()
		self.ax_right.clear()
		self.ax_left.set_title("Original")
		self.ax_right.set_title("Transformed")
		self.ax_left.axis("off")
		self.ax_right.axis("off")

	def stop_animation(self):
		if self.anim:
			self.anim.event_source.stop()
			self.anim = None

	def start_new_animation(self):
		self.stop_animation()
		self._setup_animation_axes()

		expr = self.input.text()

		f, _latex_str = parse_function(expr)

		if f is None:
			return

		self.lines = create_grid()
		self.plots = []

		for line in self.lines:
			plot, = self.ax.plot([], [], lw=1)
			self.plots.append((plot, line))

		self.ax.set_xlim(-4, 4)
		self.ax.set_ylim(-4, 4)
		self.ax.set_aspect("equal")

		def update(frame):
			t = frame / 100

			for plot, z in self.plots:
				try:
					w = f(z)
					interp = (1 - t) * z + t * w
					plot.set_data(interp.real, interp.imag)
				except Exception:
					plot.set_data([], [])

			if frame == 99:
				self.anim.event_source.stop()

			return [p[0] for p in self.plots]

		self.anim = FuncAnimation(
			self.figure,
			update,
			frames=100,
			interval=30,
			blit=True,
			repeat=False,
		)

		self.canvas.draw()
		self.visualize_btn.setText("Function selected")
		self.visualize_btn.setStyleSheet("background-color: green; color: white;")

	def upload_image(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self, "Open Image", "", "Images (*.png *.jpg *.jpeg)"
		)

		if not file_path:
			return

		self.stop_animation()
		if hasattr(self, "output_image"):
			delattr(self, "output_image")
		self.save_btn.setEnabled(False)

		self.image = Image.open(file_path).convert("RGB")
		self.original_size = self.image.size
		print("Loaded image:", self.original_size)

		self._setup_image_axes()
		self.ax_left.imshow(np.array(self.image))
		self.ax_left.set_title("Original")
		self.ax_left.axis("off")
		self.ax_right.set_title("Transformed")
		self.ax_right.set_facecolor("#eaeaea")
		self.ax_right.axis("off")

		self.canvas.draw()

		self.upload_btn.setText("Image selected")
		self.upload_btn.setStyleSheet("background-color: green; color: white;")

	def clear_image(self):
		self.stop_animation()
		for attr in ("image", "output_image", "original_size"):
			if hasattr(self, attr):
				delattr(self, attr)

		self.upload_btn.setText("Upload Image")
		self.upload_btn.setStyleSheet("")

		self._setup_image_axes()
		self._empty_image_panels()
		self.canvas.draw()

		self.save_btn.setEnabled(False)

	def _set_transform_busy(self, busy: bool) -> None:
		self.visualize_btn.setEnabled(not busy)
		self.upload_btn.setEnabled(not busy)
		self.clear_image_btn.setEnabled(not busy)
		if busy:
			self.save_btn.setEnabled(False)
		else:
			self.save_btn.setEnabled(hasattr(self, "output_image"))

	def _on_transform_progress(self, value: int) -> None:
		self.transform_progress.setValue(value)
		self.transform_progress.update()

	def _on_transform_finished(self, output: np.ndarray) -> None:
		self._set_transform_busy(False)
		self.transform_progress.setValue(100)
		self.transform_stack.setCurrentWidget(self.transform_btn)
		self._transform_worker = None

		self.output_image = Image.fromarray(output)
		self.output_image = self.output_image.resize(self.original_size)

		self._setup_image_axes()
		self.ax_left.imshow(np.array(self.image))
		self.ax_left.set_title("Original")
		self.ax_left.axis("off")
		self.ax_right.imshow(self.output_image)
		self.ax_right.set_title("Transformed")
		self.ax_right.axis("off")
		self.canvas.draw()
		self.save_btn.setEnabled(True)

	def _on_transform_failed(self, message: str) -> None:
		self._set_transform_busy(False)
		self.transform_progress.setValue(0)
		self.transform_stack.setCurrentWidget(self.transform_btn)
		self._transform_worker = None
		print("Transform failed:", message)

	def apply_transformation(self):
		if not hasattr(self, "image"):
			print("No image loaded")
			return

		if self._transform_worker is not None and self._transform_worker.isRunning():
			return

		expr = self.input.text()
		f, _ = parse_function(expr)

		if f is None:
			return

		self.stop_animation()

		self._set_transform_busy(True)
		self.transform_progress.setValue(0)
		self.transform_stack.setCurrentWidget(self.transform_progress)
		QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)

		# Defer worker so the stacked widget can paint before heavy work starts.
		QTimer.singleShot(0, lambda: self._start_transform_worker(f))

	def _start_transform_worker(self, f) -> None:
		if self._transform_worker is not None and self._transform_worker.isRunning():
			return
		if not hasattr(self, "image"):
			self._set_transform_busy(False)
			self.transform_stack.setCurrentWidget(self.transform_btn)
			return

		worker = TransformWorker(self.image, f)
		worker.progress.connect(
			self._on_transform_progress,
			Qt.ConnectionType.QueuedConnection,
		)
		worker.finished_ok.connect(
			self._on_transform_finished,
			Qt.ConnectionType.QueuedConnection,
		)
		worker.failed.connect(
			self._on_transform_failed,
			Qt.ConnectionType.QueuedConnection,
		)
		worker.finished.connect(worker.deleteLater)
		self._transform_worker = worker
		worker.start()

	def save_image(self):
		if not hasattr(self, "output_image"):
			print("No transformed image to save")
			return

		file_path, _ = QFileDialog.getSaveFileName(
			self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
		)

		if file_path:
			try:
				self.output_image.save(file_path)
				print(f"Image saved to {file_path}")
			except Exception as e:
				print("Error saving image:", e)
