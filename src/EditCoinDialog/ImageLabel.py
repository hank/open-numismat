from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

class ImageLabel(QtGui.QLabel):
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        
        self.clear()
        
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)

    def mouseDoubleClickEvent(self, e):
        file = QtCore.QTemporaryFile(QtCore.QDir.tempPath()+"/img_XXXXXX.jpg")
        file.setAutoRemove(False)
        file.open()

        fileName = QtCore.QFileInfo(file).absoluteFilePath()
        self.image.save(fileName)

        executor = QtGui.QDesktopServices()
        executor.openUrl(QtCore.QUrl.fromLocalFile(fileName)) 

    def clear(self):
        self.image = QtGui.QImage()
        self.setPixmap(QtGui.QPixmap.fromImage(self.image))
    
    def resizeEvent(self, e):
        self._showImage()
    
    def showEvent(self, e):
        self._showImage()
    
    def loadFromData(self, data):
        image = QtGui.QImage()
        result = image.loadFromData(data)
        if result:
            self._setImage(image)
        
        return result
    
    def _setImage(self, image):
        self.image = image
        self._showImage()
    
    def _showImage(self):
        if self.image.isNull():
            return
        
        # Label not shown => can't get size for resizing image
        if not self.isVisible():
            return
        
        if self.image.width() > self.width() or self.image.height() > self.height():
            scaledImage = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaledImage = self.image
        
        pixmap = QtGui.QPixmap.fromImage(scaledImage)
        self.setPixmap(pixmap)

class ImageEdit(ImageLabel):
    latestDir = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.PicturesLocation)
    
    def __init__(self, parent=None):
        super(ImageEdit, self).__init__(parent)
        
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

    def contextMenu(self, pos):
        style = QtGui.QApplication.style()

        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        load = QtGui.QAction(icon, self.tr("Load..."), self)
        load.triggered.connect(self.openImage)

        paste = QtGui.QAction(self.tr("Paste"), self)
        paste.triggered.connect(self.pasteImage)

        copy = QtGui.QAction(self.tr("Copy"), self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)
        delete = QtGui.QAction(icon, self.tr("Delete"), self)
        delete.triggered.connect(self.deleteImage)
        delete.setDisabled(self.image.isNull())

        save = QtGui.QAction(self.tr("Save as..."), self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        menu = QtGui.QMenu()
        menu.addAction(load)
        menu.setDefaultAction(load)
        menu.addAction(save)
        menu.addSeparator()
        menu.addAction(paste)
        menu.addAction(copy)
        menu.addAction(delete)
        menu.exec_(self.mapToGlobal(pos))
    
    def mouseDoubleClickEvent(self, e):
        if self.image.isNull():
            self.openImage()
        else:
            super(ImageEdit, self).mouseDoubleClickEvent(e)
        
    def openImage(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                self.tr("Open File"), ImageEdit.latestDir,
                self.tr("Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif);;All files (*.*)"))
        if fileName:
            dir = QtCore.QDir(fileName)
            dir.cdUp()
            ImageEdit.latestDir = dir.absolutePath()

            self.loadFromFile(fileName)

    def deleteImage(self):
        self.clear()
    
    def saveImage(self):
        # TODO: Set default name to coin title + field name 
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("Save File"), ImageEdit.latestDir + '/photo',
                self.tr("Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif);;All files (*.*)"))
        if fileName:
            dir = QtCore.QDir(fileName)
            dir.cdUp()
            ImageEdit.latestDir = dir.absolutePath()

            self.image.save(fileName)
    
    def pasteImage(self):
        mime = QtGui.QApplication.clipboard().mimeData()
        if mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())
        elif mime.hasImage():
            self._setImage(mime.imageData())
        elif mime.hasText():
            # Load image by URL
            self.loadFromUrl(mime.text())

    def copyImage(self):
        if not self.image.isNull():
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setImage(self.image)

    def clear(self):
        super(ImageEdit, self).clear()
        self.setText(self.tr("No image available\n(right-click to add an image)"))

    def loadFromFile(self, fileName):
        image = QtGui.QImage()
        result = image.load(fileName)
        if result:
            self._setImage(image)

        return result
    
    def loadFromUrl(self, url):
        result = False
        
        import urllib.request
        try:
            # Wikipedia require any header 
            req = urllib.request.Request(url, headers={'User-Agent' : "OpenNumismat"})
            data = urllib.request.urlopen(req).read()
            result = self.loadFromData(data)
        except:
            pass
        
        return result
        
    def data(self):
        return self.image

class EdgeImageEdit(ImageEdit):
    def __init__(self, parent=None):
        super(EdgeImageEdit, self).__init__(parent)

    def _setImage(self, image):
        if not image.isNull():
            if image.width() < image.height():
                matrix = QtGui.QMatrix()
                matrix.rotate(90)
                image = image.transformed(matrix, Qt.SmoothTransformation)

        super(EdgeImageEdit, self)._setImage(image)
