# Drop Batch
![App Window](README_files/AppScreenshot.png)  
Drag and drop image files on app window. These files shall be processed.

## Primary purpose
I wrote this app, because I wanted to process image files for my e-book reader.  
Reader's screen resolution is 1440x1920, so images are resized to 1800x1800 (keeping aspect ratio). Smaller images load faster too.  
  
Sometimes I need to process files with unsortable filenames, like ``1.jpg``, ``2.jpg``, ``3.jpg``, ..., ``10.jpg``, ``11.jpg``, ``12.jpg`` and in my e-book reader (``*.cbz`` file) their display order is like this: ``1.jpg``, ``10.jpg``, ``11.jpg``, ``12.jpg``, ``2.jpg``, ``3.jpg``, ...  
That's why this app replaces all numbers in filenames to fixed size strings: ``000001.jpg``, ``000002.jpg``, ``000003.jpg``, ..., ``000010.jpg``, ``000011.jpg``, ``000012.jpg``.

## Features
