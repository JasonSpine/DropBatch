# Drop Batch
[Download Windows executable (PyInstaller)](https://github.com/JasonSpine/DropBatch/releases/download/v1.2/DropBatch.zip)  
  
Windows Defender doesn't like this executable, because of "Unknown publisher"...  
If that's the case, please click ``More info`` and ``Run anyway`` button.  
You may also run this app directly from Python script if you don't trust this executable...  
Anyway, rest assured, this executable and app code is not harmful for your PC...  
  
![App Screenshot](README_files/AppGif.gif)  
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
* CBZ files support - images will be extracted, converted and saved as a new CBZ file,
* you don't need to wait until your drop ends processing, you may drop other files and directories on the same app window and their processing will be enqueued,
* you may choose to save dropped directories as *.cbz

## Primary purpose
I wrote this app, because I wanted to process image files for my e-book reader.  
Reader's screen resolution is 1440x1920, so there is no need for images that are much bigger than this.  
Smaller images also load faster and take less storage.  
  
Sometimes I need to process files with unsortable filenames, like ``1.jpg``, ``2.jpg``, ``3.jpg``, ..., ``10.jpg``, ``11.jpg``, ``12.jpg``.  
In my e-book reader their display order is like this: ``1.jpg``, ``10.jpg``, ``11.jpg``, ``12.jpg``, ``2.jpg``, ``3.jpg``, ...  
That's why this app replaces all numbers in filenames to fixed size strings: ``0001.jpg``, ``0002.jpg``, ``0003.jpg``, ..., ``0010.jpg``, ``0011.jpg``, ``0012.jpg``.
