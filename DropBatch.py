# Requires Python 3.5+ and PyQt5 installed!
# pip install PyQt5

import sys, os, re, glob, zipfile, shutil, datetime

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
		
		self.createCbzChecked = False

class Runnable(QRunnable):
	def __init__(self, jobDefinition, statusLabel, tasksLabel):
		super().__init__()
		
		self.jobDefinition = jobDefinition
		self.statusLabel = statusLabel
		self.tasksLabel = tasksLabel

	def run(self):
		if self.validation_failed():
			return
		
		# increment tasks counter
		self.tasksLabel.setText(str(int(self.tasksLabel.text()) + 1))
		
		mutex.lock()
		
		try:
			self.group_links()
			self.process_drop()
		except Exception as err:
			self.show_error_message(type(err).__name__, str(err))
		
		mutex.unlock()
		
		# decrement tasks counter
		self.tasksLabel.setText(str(int(self.tasksLabel.text()) - 1))
	
	def validation_failed(self):
		if len(self.jobDefinition.links) < 1:
			return True
		
		return False
	
	def group_links(self):
		self.parent_directory = os.path.dirname(self.jobDefinition.links[0])
		
		self.dropped_images = []
		self.dropped_folders = []
		self.dropped_cbz = []
		
		for link in self.jobDefinition.links:
			if os.path.isdir(link):
				self.dropped_folders.append(link)
			else:
				ext = os.path.splitext(link)[1].lower()
				
				if ext in supported_image_extensions:
					self.dropped_images.append(link)
				elif ext in supported_zip_extensions:
					self.dropped_cbz.append(link)
	
	def get_folder_images(self, dropped_folder):
		result = []
		
		for ext in supported_image_extensions:
			for imagePath in glob.iglob(os.path.join(dropped_folder, '*%s'%(ext,)), recursive = False):
				result.append(imagePath)
		
		return result
		
	def process_drop(self):
		self.process_all_images(os.path.join(self.parent_directory, self.gen_new_container_name()))
		self.process_all_folders()
		self.process_all_cbz()
	
	def process_all_images(self, target_folder):
		files_count = len(self.dropped_images)
		
		if files_count < 1:
			return
		
		os.mkdir(target_folder)
		
		self.statusLabel.setText("%04d/%04d"%(0, files_count,))
		
		for i, image in enumerate(self.dropped_images):
			self.process_image(image, target_folder)
			
			self.statusLabel.setText("%04d/%04d"%(i + 1, files_count,))
	
	def process_all_folders(self):
		for folder in self.dropped_folders:
			self.process_folder(folder)
		
	def process_all_cbz(self):
		for cbz in self.dropped_cbz:
			self.process_cbz(cbz)
	
	def process_image(self, link, target_dir):
		file_path, file_name = os.path.split(link)
		target_link = os.path.join(target_dir, file_name)
		
		if self.jobDefinition.renameChecked:
			target_link = self.get_rename_filename(target_link)
		
		if not self.jobDefinition.grayscaleChecked and not self.jobDefinition.resizeChecked:
			shutil.copy(link, target_link)
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
			img.save(target_link, quality = self.jobDefinition.imageQuality)
		else:
			shutil.copy(link, target_link)
	
	def process_folder(self, folder_link):
		self.dropped_images = self.get_folder_images(folder_link)
		
		if len(self.dropped_images) < 1:
			return
		
		target_folder = "%s_%s"%(folder_link, self.gen_new_container_name(),)
		self.process_all_images(target_folder)
		
		self.save_folder_content_as_cbz(target_folder, target_folder + ".cbz")
	
	def process_cbz(self, link):
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
	
	def get_rename_filename(self, current_path):
		file_path, file_name = os.path.split(current_path)
		
		file_name = re.sub('\d+', self.process_filename_number, file_name)
		
		return os.path.join(file_path, file_name)
	
	def process_filename_number(self, number_re_match):
		return "%04d"%(int(number_re_match.group(0)),)
	
	def save_folder_content_as_cbz(self, folder, cbz_path):
		if not self.jobDefinition.createCbzChecked:
			return
		
		os.chdir(folder)
		
		with zipfile.ZipFile(cbz_path, 'w') as myzip:
			for imagePath in glob.iglob("*", recursive = False):
				myzip.write(os.path.relpath(imagePath))
		
		os.chdir(self.parent_directory) # to make folder removal possible	
		shutil.rmtree(folder)
	
	def gen_new_container_name(self):
		ct = datetime.datetime.now() # current time
		return "DropBatch_%s"%(ct.strftime("%Y%m%d_%H%M%S"),)
	
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
		#self.setStyleSheet("background-color: #fffeea")
		
		self.setAcceptDrops(True)
		
		centralWidget = QWidget(self)
		self.setCentralWidget(centralWidget)
		windowLayout = QVBoxLayout()
		centralWidget.setLayout(windowLayout)
		
		warningLabel = QLabel("DRAG AND DROP FILES HERE!!!\nConverted files will be saved\nnext to dropped files")
		warningLabel.setStyleSheet("color: darkblue; font-weight: bold")
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
		self.statusLabel.setStyleSheet("font-weight: bold")
		statusLineLayout.addWidget(self.statusLabel)
		
		tasksLabel = QLabel("   Tasks: ")
		tasksLabel.setStyleSheet("font-weight: bold")
		statusLineLayout.addWidget(tasksLabel)
		
		self.tasksLabel = QLabel("0")
		self.tasksLabel.setStyleSheet("font-weight: bold")
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
		
		maxImageSizeLabel = QLabel("Max width/height")
		maxImageSizeLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		maxImageSizeLineLayout.addWidget(maxImageSizeLabel)
		
		self.maxImageSizeEdit = QSpinBox()
		self.maxImageSizeEdit.setRange(200, 10000)
		self.maxImageSizeEdit.setValue(1800)
		self.maxImageSizeEdit.setSingleStep(100)
		maxImageSizeLineLayout.addWidget(self.maxImageSizeEdit)
		
		imageQualityLineWidget = QWidget()
		imageQualityLineLayout = QHBoxLayout()
		imageQualityLineWidget.setLayout(imageQualityLineLayout)
		windowLayout.addWidget(imageQualityLineWidget, 1)
		
		imageQualityLabel = QLabel("Compression quality")
		imageQualityLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		imageQualityLineLayout.addWidget(imageQualityLabel)
		
		self.imageQualityEdit = QSpinBox()
		self.imageQualityEdit.setRange(0, 100)
		self.imageQualityEdit.setValue(80)
		self.imageQualityEdit.setSingleStep(3)
		
		imageQualityLineLayout.addWidget(self.imageQualityEdit)
		
		self.createCbzCheckbox = QCheckBox("Save dropped directories as *.cbz")
		self.createCbzCheckbox.setChecked(False)
		windowLayout.addWidget(self.createCbzCheckbox, 1)
		
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
			jobDefinition.createCbzChecked = self.createCbzCheckbox.isChecked() == True
			
			pool = QThreadPool.globalInstance()
			
			runnable = Runnable(jobDefinition, self.statusLabel, self.tasksLabel)
				
			pool.start(runnable)
		else:
			event.ignore()

app = QApplication(sys.argv)

window = DropBatch()
window.show()

sys.exit(app.exec_())
