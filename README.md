# ocr_with_kraken_local
A pipeline for OCR'ing files with Kraken for the OpenITI project.

Clone this repo, add pdf/image files to the INPUT_FILES folder,
and run the `ocr_pipeline.py` script to OCR your texts into OpenITI format.
Add, commit and push your output files back to the OpenITI GitHub. 

NB: only the output files will be pushed back to GitHub,
the files in the INPUT_FILES and TEMP folders will stay on your machine
(for copyright reasons).

*If you don't want to run OCR yourself but have pdfs you would like to have OCR'ed, use this repo to submit your files (only for KITAB team members): 
https://github.com/OpenITI/ocr_with_kraken*

## 1. Submitting files for OCR

To submit files for the OCR pipeline, copy them into the INPUT_FILES folder. 

### Upload a text as a single pdf file

If your text is a single pdf file, make sure that the filename contains the author and title of the text, without spaces. Ideally, use the OpenITI URI system (`<date><Author>.<BookTitle>.pdf`, e.g., 0255Jahiz.Hayawan.pdf)

### Multiple pdfs/images for one text
If your text has one pdf for each volume, or each page is a separate image, upload them in a folder. The name of the folder should contain the the author and title of the text, without spaces. Ideally, use the OpenITI URI system (`<date><Author>.<BookTitle>`). You don't have to bother with changing the names of the pdf files themselves; the output files will receive the name of the folder as their file names.
E.g., 
```
0255Jahiz.Hayawan/
    qsdfmkj_01.pdf
    qsdfmkj_02.pdf
    qsdfmkj_03.pdf
```

## OCR the texts

### OCR all texts in the INPUT_FILES folder:
Inside the ocr_with_kraken repository, run the following command from the command line: 
```
$ python ocr_pipeline.py
```
This will run OCR for all files in the INPUT_FILES folder, skipping the files that have been OCR'ed before.
The text files, with metadata in a yml file, will be in the OUTPUT_FILES folder. 

### OCR only a specific text:
If you want to OCR only one text (one pdf, or one folder containing pdf/image files of page scans of that one text): 

```
$ python ocr_pipeline.py -i INPUT_FILES/0255Jahiz.Hayawan
```
Or, for a specific file:
```
$ python ocr_pipeline.py -i INPUT_FILES/0255Jahiz.Hayawan/0255Jahiz.Hayawan.pdf
```

### OCR all texts in a different folder than `INPUT_FILES`: 
If you want to OCR a batch of texts that are located elsewhere on your machine, you can use the -b / --batch_input option: 

```
$ python ocr_pipeline.py -b D:/Documents/MyScansFolder
```

### OCR for input into eScriptorium
The output of Kraken can be imported into eScriptorium, if the output option `-x` / `--pagexml` is used: 

```
 python ocr_with_kraken.py --pagexml
```

This will create one xml file per page, linked to a specific image file.
Both files can be found in the text's folder in the TEMP folder. 


### More options
See the help command (`$ python ocr_pipeline.py --help`):

```
To run the script with the default options, run:
$ python ocr_with_kraken.py

Command line arguments for ocr_with_kraken.py:

-h, --help : print help info
-b, --batch_input: path to a folder in which all subfolders are to be OCR'ed
                    (default: INPUT_FILES)
-i, --input_folder : path to a specific file/folder to be OCR'ed
                    (output filename will be based on the name of this folder/file)
-o, --output_folder: path to the folder where the OCR'ed texts should be saved
                    (default: OUTPUT_FILES)
-m, --ocr_model : name of the OCR model to be used
                    (should be in models folder)
-s, --segmentation_model : name of the segmentation model to be used
                    (should be in models folder)
-x, --pagexml : export files in pagexml format
-a, --alto : export files in alto xml format
-r, --hocr : export files in hocr xml format
```

## Retrieve output files:
After the script finishes, the final files will be in the OUTPUT_FILES folder. For each text, it will contain
* a text file of the entire text, with OpenITI headers and page numbers
* a yml file with metadata on the conversion (which model was used, etc.)

The file names of both output files will consist of:
* the name of the folder in which the converted files were located
  (in case of a single pdf file: the name of the pdf file)
* a version ID, consisting of the collection ID `Kraken` + a time stamp (YYMMDDHHMMSS: year, month, day, hour, minutes, seconds).
E.g., 0255Jahiz.Hayawan.Kraken210218134925

The TEMP folder contains intermediate files: extracted images from the pdfs, and transcriptions of each separate page.

## Push output files back to GitHub:
After finishing the conversion process, you can push bac; the output files to GitHub: 

```
$ git add .
$ git commit -m "Convert 0255Jahiz.Hayawan"
$ git push origin main
```
NB: only files in the OUTPUT_FILES folder will be pushed back to GitHub. Files in the INPUT_FILES and OUTPUT_FILES folders will remain on your local machine (for copyright reasons, and to reduce traffic load).

## Installing kraken 

(see [http://kraken.re/](http://kraken.re/)

Kraken works best (only?) on Linux and Mac. 

Before installing kraken, install a number of external libraries (in addition to Python >= 3.6 ): 

```
# apt install libpangocairo-1.0 libxml2 libblas3 liblapack3
```

Kraken can be installed in three ways (instructions for Linux; Mac probably quite similar):

* with Python 3, from PyPi: 
```
$ pip install kraken
```
* with Python 3, from GitHub:
```
$ git clone https://github.com/mittagessen/kraken.git
$ cd kraken
$ pip install .
```
* with anaconda:
```
$ wget https://raw.githubusercontent.com/mittagessen/kraken/master/environment.yml
$ conda env create -f environment.yml
```

In our experience, the install with anaconda produces the least problems down the road. 
