"""
***UNDER CONSTRUCTION!***

The pipeline works as follows:

The repo contains three folders:

* INPUT_FILES: contains a folder for each text,
    which can contain either pdf or image files.
    The name of the folder should be its URI;
    all files in it will receive that URI.
* TEMP: image files are copied/extracted to this folder,
    and OCR conversion takes place here. 
* OUTPUT_FILES: will contain only assembled text files
    and their yml files. 

The script first converts all pdf files in INPUT_FILES (and its subfolders)
that have not been converted yet 
into png files and puts these in a folder with the URI of the text in TEMP

It then copies all image files in INPUT_FILES (and its subfolders)
that have not been converted yet into a folder with the URI of the text in TEMP

In a next step, all image files in the TEMP subfolders are converted using Kraken

Finally, the OCR output for each page of a text is joined into a single file, 
given a text id ("KrakenYYMMDDHHMMSS" : year, month, day, hour, minute, second)
and saved in the OUTPUT_FILES folder, together with a yml file. 


TO DO: 
* post-processing functions

"""

import os
from datetime import datetime as dt
import subprocess
import re
import shutil
from multiprocessing import Pool, cpu_count
import random
import string
import sys
import getopt
from zipfile import ZipFile

INFOLDER = "INPUT_FILES"
OUTFOLDER = "OUTPUT_FILES"
TEMPFOLDER = "TEMP"
OCR_MODEL = "arabPers-WithDiffTypefaces.mlmodel"
SEGM_MODEL = "DEFAULT"
IMG_EXTENSIONS = (".png", ".tif", ".jpg", ".jpeg", "jp2", ".bmp")
OUTPUT_EXT = "" # default: text. Other options: '-x', '--pagexml', '-a', '--alto', '-y', '--abbyy'
LINE_PADDING = 20
BATCH = True  # If False, INFOLDER will provide the name of the output files
try:
    CPU_COUNT = len(os.sched_getaffinity(0))
except:
    CPU_COUNT = cpu_count()


yml_template = """\
00#VERS#CLENGTH##: 
00#VERS#LENGTH###: 
00#VERS#URI######: 
80#VERS#BASED####: 
80#VERS#COLLATED#: 
80#VERS#LINKS####: 
90#VERS#ANNOTATOR: 
90#VERS#COMMENT##: OCRed through Kraken:
    * segmentation model: 
    * OCR model: 
90#VERS#DATE#####: 
90#VERS#ISSUES###: """

text_header = """\
######OpenITI#

#META# Origin: converted with Kraken (ocr model: )
#META# Date: 

#META#Header#End#

"""


def post_process_page(fp):
    # to do

    with open(fp, mode="r", encoding="utf-8") as file:
        page = file.read()

    # adapt the path to the image file in xml mode:
    if "alto" in OUTPUT_EXT:
        tag_regex = r"(<sourceImageInformation>[ \r\n]*<fileName>)[^<]+"
        tag = r"(<sourceImageInformation>\n<fileName>"
        fn = os.path.splitext(os.path.basename(fp))[0]+".png"
        page = re.sub(tag_regex, tag+fn , page)
    elif "pagexml" in OUTPUT_EXT:
        tag_regex = '<Page imageFilename="[^"]+'
        tag = '<Page imageFilename="'
        fn = os.path.splitext(os.path.basename(fp))[0]+".png"
        page = re.sub(tag_regex, tag+fn , page)

    with open(fp, mode="w", encoding="utf-8") as file:
        file.write(page)

def post_process_text(text):
    # to do
    return text

def create_yml(outfn):
    yml = re.sub("(00#VERS#URI######: *)", r"\1"+outfn, yml_template)
    yml = re.sub("(segmentation model: *)", r"\1"+SEGM_MODEL, yml)
    yml = re.sub("(OCR model: *)", r"\1"+OCR_MODEL, yml)
    date = dt.now().strftime("%Y-%m-%d")
    yml = re.sub("90#VERS#DATE#####: *", r"90#VERS#DATE#####: "+str(date), yml)
    return yml

def get_img_fp_from_xml(xml_fp):
    """Extract the filename of the image file on which the page transcription is based
    from the xml file"""
    with open(xml_fp, mode="r", encoding="utf-8") as file:
        xml = file.read()
    tags = [r"<sourceImageInformation>[ \r\n]*<fileName>([^<]+)",
            r'<Page imageFilename="([^"]+)']
    for tag_regex in tags:
        if re.findall(tag_regex, xml):
            return re.findall(tag_regex, xml)[0].strip()

def finalize_output():
    """For every OCR'ed book, join all pages into one text file, \
    assign it an OpenITI id, and save it with a yml file in OUTFOLDER"""
    print("joining separate page files into single file:")
    outfiles = list(os.listdir(OUTFOLDER))
    outfile_uris = [re.split("-[a-z]{3}\d", f)[0] for f in outfiles]
    outfile_uris = set([".".join(f.split(".")[:-1]) for f in outfile_uris])
    if not BATCH:
        uri = os.path.basename(INFOLDER.strip("/"))
        if uri.endswith(".pdf") or uri.endswith(IMG_EXTENSIONS):
            uri = os.path.splitext(uri)[0]
    for folder in os.listdir(TEMPFOLDER):
        if not BATCH:
            if folder == uri:
                add_this = True
            else:
                add_this = False
        else:
            add_this = True
        if add_this:
            folder_pth = os.path.join(TEMPFOLDER, folder)
            if folder in outfile_uris:
                print("* ", folder, "already joined")
            elif os.path.isdir(folder_pth):
                print("* ", folder)
                xml_extensions = ("alto", "pagexml") # add 'hocr'!
                xml_fps = [os.path.join(folder_pth, fn) \
                           for fn in os.listdir(folder_pth) \
                           if fn.endswith(xml_extensions)]
                if xml_fps:
                    ts = dt.now().strftime("%y%m%d%H%M%S")
                    outfn = "{}.Kraken{}-ara1".format(folder, ts) # FN.KrakenYYMMDDHHMMSS-ara1
                    outfp = os.path.join(OUTFOLDER, outfn+".zip")
                    with ZipFile(outfp, mode="w") as z:
                        for xml_fp in xml_fps:
                            try:
                                z.write(xml_fp)
                                img_fn = get_img_fp_from_xml(xml_fp)
                                print(img_fn)
                                img_fp = os.path.splitext(xml_fp)[0] + os.path.splitext(img_fn)[1]
                                print(img_fp)
                                z.write(img_fp)
                            except:
                                print("no image file found for", xml_fp)


                txt_extensions = ("txt", )
                txt_fps = [os.path.join(folder_pth, fn) \
                           for fn in os.listdir(folder_pth) \
                           if fn.endswith(txt_extensions)]
                if txt_fps:
                    text = ""
                    ts = dt.now().strftime("%y%m%d%H%M%S")
                    outfn = "{}.Kraken{}-ara1".format(folder, ts) # FN.KrakenYYMMDDHHMMSS-ara1
                    outfp = os.path.join(OUTFOLDER, outfn)
                    with open(outfp, mode="a", encoding="utf-8") as outfile:
                        intro = text_header
                        intro = re.sub("Date: ", "Date: "+dt.now().strftime("%Y-%m-%d"), intro)
                        intro = re.sub("ocr model: ", "ocr model: "+OCR_MODEL, intro)
                        outfile.write(intro)
                        for fp in sorted(txt_fps):
                            with open(fp, mode="r", encoding="utf-8") as r:
                                outfile.write(r.read())
                                try:
                                    v,p = re.findall("(\d+)_(\d+$)", fp.split(".")[-2])[0]
                                except:
                                    v = "00"
                                    try:
                                        p = re.findall("\d+$", fp.split(".")[-2])[0]
                                    except:
                                        p = "000"
                                outfile.write("\n\nPageV{}P{}\n\n{}\n\n".format(v, p, "="*60))

                    # post-process the text:
                    with open(outfp, mode="r", encoding="utf-8") as outfile:
                        text = outfile.read()
                    with open(outfp, mode="w", encoding="utf-8") as outfile:
                        outfile.write(post_process_text(text))

                # create yml file:
                if txt_fps or xml_fps:
                    if outfp.endswith(".zip"):
                        outfp = outfp[:-4]
                    with open(outfp+".yml", mode="w", encoding="utf-8") as outyml:
                        yml_s = create_yml(outfn)
                        outyml.write(yml_s)

def normalize_path(fp, suffix, ext):
    """Make filenames for files in nested folders.

    Args:
        fp (str): path to the current file
        ext (str): extension for the new file name
        suffix (str): suffix for the new file name
            (to be inserted in front of the extension).
            Use "" for no extension, and r"\1" for
            keeping the original extension.


    Returns:
        tup (uri: name of the first-level folder,
             f: filename)

    Examples of filenames:
        INFOLDER/booktitle/-001.png > booktitle_001.pdf
        INFOLDER/booktitle/booktitle_01/booktitle_01-001.jpg > booktitle_01_01_001.jpg
        INFOLDER/booktitle/booktitle_01/-001.jpg > booktitle_01_001.jpg
        INFOLDER/booktitle/01/001.jpg > booktitle_01_001.jpg

    (uri in all examples is booktitle)
    """
    if ext.startswith("."):
        ext = ext[1:]
    if BATCH:
        f = re.sub(INFOLDER+"/", "", fp)
        uri = f.split("/")[0]
    else:  # single file/folder mode:
        f = re.sub(os.path.dirname(INFOLDER.strip("/"))+"/", "", fp)
        uri = os.path.basename(INFOLDER)
    f = re.sub(r"/{}".format(uri), "", f) 
    f = re.sub("/", "_", f)
    f = re.sub(r"[_\-]+(\d+\.[a-z]+)$", r"_\1", f)
    if ext:
        f = re.sub("\.([a-z]+)$", suffix+"."+ext, f)
    else:
        f = re.sub("\.([a-z]+)$", suffix, f)
    return uri, f

def convert_pdf(infp, img_folder):
    """Extract images from pdf to png format and extract text from images.

    NB: because we are doing this in parallel processes,
    the files are first extracted into a temporary directory.
    The script uses the poppler library pdfimages to do this;
    this gives the extracted files filenames like "-001.png", "-002.png", etc.
    Since some texts have a pdf for each volume, these filenames need
    to be combined with a volume-specific file name.
    The script appends the pdfimages-generated filename
    to the filename created by the normalize_path function.
    """
    print("Extracting images from", infp)
    # create a temporary folder to extract the images into:
    tmp = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    tmp = os.path.join(os.path.dirname(infp), tmp+"/")
    os.makedirs(tmp)
    print("created temp folder", tmp)
    # extract images:
    subprocess.run(["pdfimages", infp, tmp, "-png"], stdout=subprocess.PIPE)
    print("images extracted into", tmp)
    for img_fn in os.listdir(tmp):
        img_fp = os.path.join(tmp, img_fn)
        uri, fn = normalize_path(infp, "", "")
        img_fn = fn + "_" + img_fn[1:]
        dest_fp = os.path.join(img_folder, img_fn)
        os.rename(img_fp, dest_fp)
    # remove temp folder:
    try:
        os.rmdir(tmp)
    except:
        print("directory not yet empty. Try again in 2 seconds")
        time.sleep(2)
        os.rmdir(tmp)
    print("Extracted images moved into", img_folder)

def prepare_pdf_file(infp):
    """Extract images from pdf file if that was not done before."""
    uri, img_fn = normalize_path(infp, "_001", ".png")
    if not BATCH: # single-folder mode: use name of input folder for output folder
        uri = os.path.basename(INFOLDER.strip("/"))
        uri, ext = os.path.splitext(uri)
    img_folder = os.path.join(TEMPFOLDER, uri)
    print("img_folder:", img_folder)
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    img_fp = os.path.join(img_folder, img_fn)
    print("img_fp:", img_fp)
    if not os.path.exists(img_fp):
        convert_pdf(infp, img_folder)
    else:
        print("PDF was already converted:", img_fp)

def prepare_files_for_conversion(in_pth):
    """Extract images from pdfs and copy image files to
    the text's folder in TEMPFOLDER

    Args:
        in_pth (str): path to the folder (or file)
    """

    if os.path.isfile(in_pth):  # single file mode
        print("converting single file", in_pth)
        uri, ext = os.path.splitext(os.path.basename(in_pth))
        dest_folder = os.path.join(TEMPFOLDER, uri)
        os.makedirs(dest_folder, exist_ok=True)
        if in_pth.endswith(".pdf"):
            prepare_pdf_file(in_pth)
        elif in_pth.endswith(IMG_EXTENSIONS):
            dest_fp = os.path.join(dest_folder, uri+"."+ext)
            if not os.path.exists(dest_fp):
                shutil.copyfile(in_pth, dest_fp)
            else:
                print(in_pth, "already converted")
        return

    print("Extracting images from pdf files")
    pdf_files = [fn for fn in os.listdir(in_pth) if fn.endswith(".pdf")]
    pdf_files = [os.path.join(in_pth, fn) for fn in pdf_files]
    with Pool(processes=CPU_COUNT) as pool:
        pool.map(prepare_pdf_file, pdf_files)
    #for fp in pdf_files:
    #    prepare_pdf_file(fp)


    print("collecting image files")
    image_files = []
    for fn in os.listdir(in_pth):
        fp = os.path.join(in_pth, fn)
        if os.path.isdir(fp): # pdf or image files inside a directory
            sub_folder = os.path.join(in_pth, fn)
            prepare_files_for_conversion(sub_folder)
        elif fn.endswith(IMG_EXTENSIONS):
            #img_folder_name = re.sub("[_\-]*\d+\.[a-z]+$", "", fn)
            #img_folder = os.path.join(TEMPFOLDER, img_folder_name)
            uri, fn = normalize_path(fp, "", r"\1")
            dest_folder = os.path.join(TEMPFOLDER, uri)
            os.makedirs(dest_folder, exist_ok=True)
            dest_fp = os.path.join(dest_folder, fn)
            if not os.path.exists(dest_fp):
                image_files.append((fp, dest_fp))
            else:
                print(fn, "already converted")
        else:
            print(fn, "ignored")
    print("copying images to destination folders in TEMPFOLDER")
    with Pool(processes=CPU_COUNT) as pool:
        pool.starmap(shutil.copyfile, image_files)


def convert_img(img_fp, dest_fp, pad=LINE_PADDING):
    """Extract text from image file.

    Args:
        img_fp (str): path to the input image (in INFOLDER or TEMPFOLDER)
        dest_fp (str): path to the output text file within the same folder
    """
    print("OCR'ing", img_fp, "with kraken")
    kraken_cmd =  ['kraken', '-i', img_fp, dest_fp, 'binarize']
    kraken_cmd += ['segment', '-d', 'horizontal-rl', '-p', str(pad), str(pad)]
    kraken_cmd += ['ocr', '-m', 'models/{}'.format(OCR_MODEL)]
    if OUTPUT_EXT in ['-x', '--pagexml', '-a', '--alto', '--hocr']:
        kraken_cmd.append(OUTPUT_EXT)
    subprocess.run(kraken_cmd, stdout=subprocess.PIPE)

    print("post-processing", dest_fp)
    post_process_page(dest_fp)


def convert_image_files():
    """Convert all image files in TEMPFOLDER that have not been converted yet."""
    print("Collecting image files that have not been converted")
    img_files = []
    if not BATCH: 
        uri = os.path.basename(INFOLDER.strip("/"))
        if uri.endswith(".pdf") or uri.endswith(IMG_EXTENSIONS):
            uri = os.path.splitext(uri)[0]
    for f in os.listdir(TEMPFOLDER):
        if not BATCH:
            if f == uri:
                add_this = True
            else:
                add_this = False
        else:
            add_this = True
        if add_this:
            folder = os.path.join(TEMPFOLDER, f)
            if os.path.isdir(folder):
                for fn in os.listdir(folder):
                    if fn.endswith(IMG_EXTENSIONS):
                        fp = os.path.join(folder, fn)
                        bare_fp, ext = os.path.splitext(fp)
                        if OUTPUT_EXT:
                            txt_fp = bare_fp + re.sub("-+", ".", OUTPUT_EXT)
                        else:
                            txt_fp = bare_fp+".txt"
                        if not os.path.exists(txt_fp):
                            img_files.append((fp, txt_fp))
                    else:
                        print("Ignoring", fn)
    print("Converting image files to text using", CPU_COUNT, "CPU cores.")
    with Pool(processes=CPU_COUNT) as pool:
        pool.starmap(convert_img, img_files)
    print("Finished all conversions")

def main():
    prepare_files_for_conversion(INFOLDER)
    convert_image_files()
    finalize_output()


info = """\
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
"""

if __name__ == "__main__":

    argv = sys.argv[1:]
    opt_str = "hxarb:i:o:m:s:"
    opt_list = ["help", "pagexml", "alto", "hocr",
                "batch_input=", "input_folder=", "output_folder=",
                "ocr_model=", "segmentation_model="]
    try:
        opts, args = getopt.getopt(argv, opt_str, opt_list)
    except Exception as e:
        print(e)
        print("Input incorrect: \n"+info)
        sys.exit(2)

    for opt, arg in opts:
        #global OUTPUT_EXT
        OUTPUT_EXT = ""
        if opt in ["-h", "--help"]:
            print(info)
            os.exit(0)
        elif opt in ["-a", "--alto"]:
            OUTPUT_EXT = "--alto"
        elif opt in ["-x", "--pagexml"]:
            OUTPUT_EXT = "--pagexml"
        elif opt in ["-r", "--hocr"]:
            OUTPUT_EXT = "--hocr"
        elif opt in ["-b", "--batch_input"]:
            #global INFOLDER
            INFOLDER = arg.strip("/")
            print("INFOLDER variable set to", INFOLDER)
            if not os.path.isdir(INFOLDER):
                print("ERROR:", INFOLDER, "is not a directory")
        elif opt in ["-i", "--input_folder"]:
            #global BATCH
            BATCH = False
            #global INFOLDER
            INFOLDER = arg.strip("/")
        elif opt in ["-o", "--output_folder"]:
            #global OUTFOLDER
            OUTFOLDER = arg.strip("/")
            print("OUTFOLDER variable set to", OUTFOLDER)
            if not os.path.isdir(OUTFOLDER):
                print("ERROR:", OUTFOLDER, "is not a directory")
        elif opt in ["-m", "--ocr_model"]:
            #global OCR_MODEL
            OCR_MODEL = arg
            print("OCR_MODEL variable set to", OCR_MODEL)
            if not os.path.isfile(os.path.join("models", OCR_MODEL)):
                m = re.sub(".+models/", "", OCR_MODEL)
                if os.path.isfile(os.path.join("models", m)):
                    OCR_MODEL = m
                else:
                    print("ERROR:", OCR_MODEL, "not found in models folder")
        elif opt in ["-s", "--segmentation_model"]:
            #global SEGM_MODEL
            SEGM_MODEL = arg
            print("SEGM_MODEL variable set to", SEGM_MODEL)
            if not os.path.isfile(os.path.join("models", SEGM_MODEL)):
                s = re.sub(".+models/", "", SEGM_MODEL)
                if os.path.isfile(os.path.join("models", s)):
                    SEGM_MODEL = s
                else:
                    print("ERROR:", SEGM_MODEL, "not found in models folder")


    main()
