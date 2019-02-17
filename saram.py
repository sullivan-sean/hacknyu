import io
import os
import subprocess
import sys
import time
import pytesseract
from subprocess import call

import PIL.Image as Im
import pyocr
import pyocr.builders
from PIL import Image as Im
from wand.image import Image

VALIDITY = [".jpg",".gif",".png",".tga",".tif",".bmp", ".pdf"]

FNULL = open(os.devnull, 'w') #Open file in write mode to The file path of the null device. For example: '/dev/null' 

class ArgumentMissingException(Exception):
    def __init__(self):
        print("usage: {} <dirname>".format(sys.argv[0]))
        sys.exit(1)

class Saram:
    def __init__(self):
        ocr_language = 'eng'

        tools = pyocr.get_available_tools()
        if len(tools) == 0:
            print("No OCR tool found")
            sys.exit(1)
        self.tool = tools[0]

        try:
            langs = self.tool.get_available_languages()
            self.lang = langs[0]
            if ocr_language in langs:
                self.lang = ocr_language
        except Exception as e:
            print("{}".format(e))

    def create_directory(self, path):
        if not os.path.exists(path): #No path
            os.makedirs(path) #Create path

    def pdf_run(self, image_file_name, filename):
        image_pdf = Image(filename=image_file_name, resolution=300)
        image_page = image_pdf.convert("png")

        page = 1

        names = []
        for page, img in enumerate(image_page.sequence):
            img_per_page = Image(image=img)
            img_per_page.type = 'grayscale'
            img_per_page.depth = 8
            img_per_page.density = 300

            try:
                img_per_page.level(black=0.3, white=1.0, gamma=1.5, channel=None)
            except AttributeError as e:
                print("Update Wand library: %s" % e)

            img_buf = "saram_" + filename + str(page) + ".png"
            names.append(img_buf)
            img_per_page.save(filename=img_buf)
            img.destroy()
        return names

    def get_rotation_info(self, filename):
        arguments = ' %s - --psm 0'
        stdoutdata = subprocess.getoutput('tesseract' + arguments % filename)
        degrees = None

        for line in stdoutdata.splitlines():
            info = 'Orientation in degrees: '
            if info in line:
                degrees = float(line.replace(info, '').strip())
        return degrees

    def main(self, f):
        fname, ext = os.path.splitext(f)
        remove_names = False

        if ext.lower() == ".pdf":
            filename = ''.join(e for e in fname if e.isalnum() or e == '-')
            names = self.pdf_run(f, filename)
            remove_names = True
        elif ext.lower() in VALIDITY:
            names = [f]
        else:
            raise Exception('Must use pdf')

        text = ''
        for name in names:
            degrees = self.get_rotation_info(name)
            print(degrees, name)
            if degrees:
                im1 = Im.open(name)
                im1.rotate(degrees).save(name)
            text += pytesseract.image_to_string(Im.open(name))
            if remove_names:
                os.remove(name)
        with open("out.txt", "w") as text_file:
            print(text, file=text_file)
        return text

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ArgumentMissingException
    path = sys.argv[1]
    path = os.path.abspath(path)
    s = Saram()
    print(s.main(path))
