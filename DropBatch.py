# Requires Python 3.5+ and PyQt5 installed!
# pip install PyQt5

import sys, os, re, glob

from PyQt5.QtWidgets import (
	QApplication,
	QMainWindow,
	QLabel,
	QCheckBox,
)

from PyQt5.QtCore import (
	Qt,
	QUrl,
	QRunnable,
	QThreadPool,
)

from PyQt5.QtGui import (
	QImage,
)

class JobDefinition:
	def __init__(self):
		self.links = []
		
		self.renameChecked = False
		self.resizeChecked = False
		
		self.grayscaleChecked = False
		self.maxImageSize = 1800

class Runnable(QRunnable):
	def __init__(self, jobDefinition, statusLabel):
		super().__init__()
		
		self.jobDefinition = jobDefinition
		self.statusLabel = statusLabel

	def run(self):
		self.unpack_dirs()
		self.process_files()
	
	def unpack_dirs(self):
		result = []
		
		for link in self.jobDefinition.links:
			if os.path.isdir(link):
				for imagePath in glob.iglob(os.path.join(link, '**/*.jpg'), recursive=True):
					result.append(imagePath)
				for imagePath in glob.iglob(os.path.join(link, '**/*.png'), recursive=True):
					result.append(imagePath)
				for imagePath in glob.iglob(os.path.join(link, '**/*.jpeg'), recursive=True):
					result.append(imagePath)
			else:
				_, ext = os.path.splitext(link)
				
				if ext.lower() in (".jpg", ".png", ".jpeg"):
					result.append(link)
		
		self.jobDefinition.links = result
	
	def process_files(self):
		links_count = len(self.jobDefinition.links)
		
		for i, link in enumerate(self.jobDefinition.links):
			self.statusLabel.setText("%04d/%04d"%(i + 1, links_count,))
			
			if self.jobDefinition.resizeChecked:
				self.resize_image(link)
			if self.jobDefinition.renameChecked:
				os.rename(link, self.get_rename_filename(link))
	
	def resize_image(self, imagePath):
		img = QImage(imagePath)
		
		img = img.scaled(
			self.jobDefinition.maxImageSize,
			self.jobDefinition.maxImageSize,
			Qt.KeepAspectRatio,
			Qt.SmoothTransformation)
			
		img = img.convertToFormat(QImage.Format_Grayscale8)
		#img = img.convertToFormat(QImage.Format_Grayscale16)
		img.save(imagePath, quality = 88)
	
	def get_rename_filename(self, current_path):
		file_path, file_name = os.path.split(current_path)
		
		file_name = re.sub('\d+', self.process_filename_number, file_name)
		
		return os.path.join(file_path, file_name)
	
	def process_filename_number(self, number_re_match):
		return "%06d"%(int(number_re_match.group(0)),)
		
class DropBatch(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Drop Batch")
		self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint | Qt.WindowStaysOnTopHint)
		self.setStyleSheet("background-color: darkblue; color: white;")
		
		self.setAcceptDrops(True)
		#self.resize(350, 200)
		self.setGeometry(20, 50, 350, 200)
		
		self.statusLabel = QLabel("Drag files and folders here!", self)
		self.statusLabel.setGeometry(50, 20, 250, 30)
		
		self.renameCheckbox = QCheckBox("Rename", self)
		self.renameCheckbox.setGeometry(50, 100, 250, 25)
		self.renameCheckbox.setChecked(True)
		
		self.resizeCheckbox = QCheckBox("Resize", self)
		self.resizeCheckbox.setGeometry(50, 130, 250, 25)
		self.resizeCheckbox.setChecked(True)
		
	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()
	
	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls():
			event.setDropAction(Qt.CopyAction)
			event.accept()
		else:
			event.ignore()
			
	def dropEvent(self, event):
		if event.mimeData().hasUrls():
			event.setDropAction(Qt.CopyAction)
			event.accept()
			
			links = []
			
			for url in event.mimeData().urls():
				if url.isLocalFile():
					links.append(str(url.toLocalFile()))
				else:
					pass
					#links.append(str(url.toString()))
			
			jobDefinition = JobDefinition()
			
			jobDefinition.links = links
			jobDefinition.resizeChecked = self.resizeCheckbox.isChecked() == True
			jobDefinition.renameChecked = self.renameCheckbox.isChecked() == True
			
			pool = QThreadPool.globalInstance()
			
			runnable = Runnable(jobDefinition, self.statusLabel)
				
			pool.start(runnable)
		else:
			event.ignore()

app = QApplication(sys.argv)

window = DropBatch()
window.show()

sys.exit(app.exec_())
