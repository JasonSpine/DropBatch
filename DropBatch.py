# Requires Python 3.5+ and PyQt5 installed!
# pip install PyQt5

import sys, os, re, glob, zipfile, shutil

from PyQt5.QtWidgets import (
	QApplication,
	QMainWindow,
	QWidget,
	QVBoxLayout,
	QHBoxLayout,
	QLabel,
	QCheckBox,
	QSpinBox,
	QMessageBox,
)

from PyQt5.QtCore import (
	Qt,
	QUrl,
	QRunnable,
	QThreadPool,
	QMutex,
)

from PyQt5.QtGui import (
	QImage,
)

supported_image_extensions = (".jpg", ".png", ".jpeg",)
supported_zip_extensions = (".cbz",)

supported_file_extensions = []
supported_file_extensions += supported_image_extensions
supported_file_extensions += supported_zip_extensions

mutex = QMutex()

class JobDefinition:
	def __init__(self):
		self.links = []
		
		self.renameChecked = False
		self.grayscaleChecked = False
		self.resizeChecked = False
		
		self.maxImageSize = 1800
		self.imageQuality = 80

class Runnable(QRunnable):
	def __init__(self, jobDefinition, statusLabel, tasksLabel):
		super().__init__()
		
		self.jobDefinition = jobDefinition
		self.statusLabel = statusLabel
		self.tasksLabel = tasksLabel

	def run(self):
		self.tasksLabel.setText(str(int(self.tasksLabel.text()) + 1))
		
		mutex.lock()
		
		try:
			self.unpack_dirs()
			self.process_files()
		except Exception as err:
			self.show_error_message(type(err).__name__, str(err))
		
		mutex.unlock()
		
		self.tasksLabel.setText(str(int(self.tasksLabel.text()) - 1))
	
	def unpack_dirs(self):
		result = []
		
		for link in self.jobDefinition.links:
			if os.path.isdir(link):
				for ext in supported_file_extensions:
					for imagePath in glob.iglob(os.path.join(link, '**/*%s'%(ext,)), recursive=True):
						result.append(imagePath)
			else:
				_, ext = os.path.splitext(link)
				
				if ext.lower() in supported_file_extensions:
					result.append(link)
		
		self.jobDefinition.links = result
	
	def process_files(self):
		links_count = len(self.jobDefinition.links)
		
		self.statusLabel.setText("%04d/%04d"%(0, links_count,))
		
		for i, link in enumerate(self.jobDefinition.links):
			_, ext = os.path.splitext(link)
			
			if ext.lower() in supported_image_extensions:
				self.process_image(link)
				self.rename_image(link)
			else:
				self.process_zip(link)
			
			self.statusLabel.setText("%04d/%04d"%(i + 1, links_count,))
	
	def process_zip(self, link):
		file_path, file_name = os.path.split(link)
		temp_dir = "tmp_%s"%(file_name,)
		temp_path = os.path.join(file_path, temp_dir)
		
		namelist = []
		
		with zipfile.ZipFile(link, 'r') as myzip:
			namelist = myzip.namelist()
			myzip.extractall(temp_path)
		
		os.chdir(temp_path)
		
		with zipfile.ZipFile(link, 'w') as myzip:
			for imagePath in namelist:
				self.process_image(imagePath)
				myzip.write(imagePath)
		
		os.chdir(file_path)
		
		shutil.rmtree(temp_path)
	
	def process_image(self, link):
		if not self.jobDefinition.grayscaleChecked and not self.jobDefinition.resizeChecked:
			return
		
		img = QImage(link)
		
		anyChanges = False
		
		if self.jobDefinition.resizeChecked and (img.width() > self.jobDefinition.maxImageSize or img.height() > self.jobDefinition.maxImageSize):
			img = img.scaled(
				self.jobDefinition.maxImageSize,
				self.jobDefinition.maxImageSize,
				Qt.KeepAspectRatio,
				Qt.SmoothTransformation)
			anyChanges = True
		
		if self.jobDefinition.grayscaleChecked and not img.isGrayscale():
			img = img.convertToFormat(QImage.Format_Grayscale8)
			#img = img.convertToFormat(QImage.Format_Grayscale16)
			anyChanges = True
		
		if anyChanges:
			img.save(link, quality = self.jobDefinition.imageQuality)
	
	def rename_image(self, link):
		if self.jobDefinition.renameChecked:
			os.rename(link, self.get_rename_filename(link))
	
	def get_rename_filename(self, current_path):
		file_path, file_name = os.path.split(current_path)
		
		file_name = re.sub('\d+', self.process_filename_number, file_name)
		
		return os.path.join(file_path, file_name)
	
	def process_filename_number(self, number_re_match):
		return "%04d"%(int(number_re_match.group(0)),)
		
	def show_error_message(self, error_type, error_description):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Critical)
		msg.setText(error_description)
		#msg.setInformativeText(error_description)
		msg.setWindowTitle(error_type)
		msg.exec_()
		
class DropBatch(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Drop Batch")
		self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint | Qt.WindowStaysOnTopHint)
		self.setStyleSheet("background-color: darkblue; color: white;")
		
		self.setAcceptDrops(True)
		
		centralWidget = QWidget(self)
		self.setCentralWidget(centralWidget)
		windowLayout = QVBoxLayout()
		centralWidget.setLayout(windowLayout)
		
		warningLabel = QLabel("WARNING!\nDropped files will be irreversibly\nmodified! Use with caution!")
		warningLabel.setStyleSheet("color: yellow; font-weight: bold; font-size: 10pt")
		warningLabel.setAlignment(Qt.AlignCenter)
		windowLayout.addWidget(warningLabel, 2)
		
		extensionsLabel = QLabel("    ".join("*%s"%(ext,) for ext in supported_file_extensions))
		extensionsLabel.setAlignment(Qt.AlignCenter)
		windowLayout.addWidget(extensionsLabel, 1)
		
		statusLineWidget = QWidget()
		statusLineLayout = QHBoxLayout()
		statusLineWidget.setLayout(statusLineLayout)
		windowLayout.addWidget(statusLineWidget, 1)
		
		self.statusLabel = QLabel("Drag files and folders here!")
		self.statusLabel.setStyleSheet("font-weight: bold; font-size: 9pt")
		statusLineLayout.addWidget(self.statusLabel)
		
		tasksLabel = QLabel("   Tasks: ")
		tasksLabel.setStyleSheet("font-weight: bold; font-size: 9pt")
		statusLineLayout.addWidget(tasksLabel)
		
		self.tasksLabel = QLabel("0")
		self.tasksLabel.setStyleSheet("font-weight: bold; font-size: 9pt")
		statusLineLayout.addWidget(self.tasksLabel)
		
		self.renameCheckbox = QCheckBox('Rename (e.g."v1ch3.jpg" => "v0001ch0003.jpg")')
		self.renameCheckbox.setChecked(True)
		windowLayout.addWidget(self.renameCheckbox, 1)
		
		self.grayscaleCheckbox = QCheckBox("Convert colors to grayscale")
		self.grayscaleCheckbox.setChecked(False)
		windowLayout.addWidget(self.grayscaleCheckbox, 1)
		
		self.resizeCheckbox = QCheckBox("Resize images")
		self.resizeCheckbox.setChecked(True)
		windowLayout.addWidget(self.resizeCheckbox, 1)
		
		maxImageSizeLineWidget = QWidget()
		maxImageSizeLineLayout = QHBoxLayout()
		maxImageSizeLineWidget.setLayout(maxImageSizeLineLayout)
		windowLayout.addWidget(maxImageSizeLineWidget, 1)
		
		maxImageSizeLineLayout.addWidget(QLabel("Max width/height"))
		
		self.maxImageSizeEdit = QSpinBox()
		self.maxImageSizeEdit.setRange(200, 10000)
		self.maxImageSizeEdit.setValue(1800)
		self.maxImageSizeEdit.setSingleStep(100)
		maxImageSizeLineLayout.addWidget(self.maxImageSizeEdit)
		
		imageQualityLineWidget = QWidget()
		imageQualityLineLayout = QHBoxLayout()
		imageQualityLineWidget.setLayout(imageQualityLineLayout)
		windowLayout.addWidget(imageQualityLineWidget, 1)
		
		imageQualityLineLayout.addWidget(QLabel("Compression quality"))
		
		self.imageQualityEdit = QSpinBox()
		self.imageQualityEdit.setRange(0, 100)
		self.imageQualityEdit.setValue(80)
		self.imageQualityEdit.setSingleStep(3)
		
		imageQualityLineLayout.addWidget(self.imageQualityEdit)
		
		
		
		self.setGeometry(20, 50, 4, 4)
		
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
					links.append(url.toLocalFile())
				else:
					pass
					#links.append(str(url.toString()))
			
			jobDefinition = JobDefinition()
			
			jobDefinition.links = links
			jobDefinition.renameChecked = self.renameCheckbox.isChecked() == True
			jobDefinition.grayscaleChecked = self.grayscaleCheckbox.isChecked() == True
			jobDefinition.resizeChecked = self.resizeCheckbox.isChecked() == True
			jobDefinition.maxImageSize = self.maxImageSizeEdit.value()
			jobDefinition.imageQuality = self.imageQualityEdit.value()
			
			pool = QThreadPool.globalInstance()
			
			runnable = Runnable(jobDefinition, self.statusLabel, self.tasksLabel)
				
			pool.start(runnable)
		else:
			event.ignore()

app = QApplication(sys.argv)

window = DropBatch()
window.show()

sys.exit(app.exec_())
