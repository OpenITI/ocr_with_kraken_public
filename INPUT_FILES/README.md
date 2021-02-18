# INPUT_FILES

Drop your files to be converted in this folder. 

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
