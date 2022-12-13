# Drop Batch
[Download Windows executable (PyInstaller)](https://github.com/JasonSpine/DropBatch/releases/download/v1.0/DropBatch.zip)  
  
![App Window](README_files/AppScreenshot.png)  
Drag and drop image files on app window. These files shall be processed.
## Features
* process files and directories dropped on app window,
* all image files inside a directory and it's subdirectories shall be processed,
* resize images to max width/height (keeping aspect ratio),
* images smaller than max width/height won't be resized,
* replace **numbers** in filenames with **fixed size strings**, e.g. ``file 2.jpg`` => ``file 0002.jpg``,
* convert image colors to grayscale,
* set image compression quality,
* choose which processing options will be applied to your images,
* you don't need to wait until your drop ends processing, you may drop other files and directories on the same app window.

## Primary purpose
I wrote this app, because I wanted to process image files for my e-book reader.  
Reader's screen resolution is 1440x1920, so there is no need for images that are much bigger than this.  
Smaller images also load faster and take less storage.  
  
Sometimes I need to process files with unsortable filenames, like ``1.jpg``, ``2.jpg``, ``3.jpg``, ..., ``10.jpg``, ``11.jpg``, ``12.jpg`` and in my e-book reader their display order is like this: ``1.jpg``, ``10.jpg``, ``11.jpg``, ``12.jpg``, ``2.jpg``, ``3.jpg``, ...  
That's why this app replaces all numbers in filenames to fixed size strings: ``0001.jpg``, ``0002.jpg``, ``0003.jpg``, ..., ``0010.jpg``, ``0011.jpg``, ``0012.jpg``.
