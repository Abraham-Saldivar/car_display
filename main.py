#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import threading
import logging
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request
from flask_mail import Mail, Message
from waveshare_epd import epd7in5_V2
import textwrap
import traceback

# Initialize directories
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

# Touch input and e-Ink display initialization
from TP_lib import gt1151
from TP_lib import epd2in13_V2

logging.basicConfig(level=logging.DEBUG)
flag_t = 1

def pthread_irq():
    print("pthread running")
    while flag_t == 1:
        if(gt.digital_read(gt.INT) == 0):
            GT_Dev.Touch = 1
        else:
            GT_Dev.Touch = 0
    print("thread:exit")

# Image and text update logic
def update_display_with_option():
    display = epd7in5_V2.EPD()
    display.init()
    display.Clear()

    w = display.height
    h = display.width

    mode = input("Would you like to display an image or text? (Enter 'image' or 'text'): ").strip().lower()

    if mode == 'image':
        image_path = input("Enter the full path to the image file: ").strip()
        try:
            image = Image.open(image_path).convert('1')
            image = image.resize((w, h))
            display.display(display.getbuffer(image))
            print("Image displayed successfully.")
        except Exception as e:
            print(f"Error displaying the image: {e}")
    elif mode == 'text':
        message = input("Please enter a message you would like to display: ")

        image = Image.new(mode='1', size=(w, h), color=255)
        draw = ImageDraw.Draw(image)

        font_size = 36
        font_file = '/home/nin110/Projects/e-Paper/first_project/images/Noto_Sans/NotoSans-ExtraBold.ttf'
        font = ImageFont.truetype(font_file, font_size)

        wrapped_text = textwrap.fill(message, width=20)
        lines = wrapped_text.split('\n')
        text_height = len(lines) * font_size

        y = (h - text_height) // 2

        for line in lines:
            text_width, _ = draw.textsize(line, font=font)
            x = (w - text_width) // 2
            draw.text((x, y), line, font=font, fill=0, align='center')
            y += font_size

        display.display(display.getbuffer(image))
        print("Text displayed successfully.")
    else:
        print("Invalid input. Please enter 'image' or 'text'.")

def Show_Photo_Small(image, small):
    for t in range(1, 5):
        if(small*2+t > 6):
            newimage = Image.open(os.path.join(picdir, PhotoPath_S[0]))
            image.paste(newimage, ((t-1)//2*45+2, (t%2)*124+2))
        else:
            newimage = Image.open(os.path.join(picdir, PhotoPath_S[small*2+t]))
            image.paste(newimage, ((t-1)//2*45+2, (t%2)*124+2))

def Show_Photo_Large(image, large):
    if(large > 6):
        newimage = Image.open(os.path.join(picdir, PhotoPath_L[0]))
        image.paste(newimage, (2, 2))
    else:
        newimage = Image.open(os.path.join(picdir, PhotoPath_L[large]))
        image.paste(newimage, (2, 2))

def Read_BMP(File, x, y):
    newimage = Image.open(os.path.join(picdir, File))
    image.paste(newimage, (x, y))

# Start the display update loop
def run_display_loop():
    epd = epd2in13_V2.EPD_2IN13_V2()
    gt = gt1151.GT1151()
    GT_Dev = gt1151.GT_Development()
    GT_Old = gt1151.GT_Development()

    epd.init(epd.FULL_UPDATE)
    gt.GT_Init()
    epd.Clear(0xFF)

    t = threading.Thread(target=pthread_irq)
    t.setDaemon(True)
    t.start()

    font15 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 15)
    font24 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 24)
    
    image = Image.open(os.path.join(picdir, 'Menu.bmp'))
    epd.displayPartBaseImage(epd.getbuffer(image))
    DrawImage = ImageDraw.Draw(image)
    epd.init(epd.PART_UPDATE)

    i = j = k = ReFlag = SelfFlag = Page = Photo_L = Photo_S = 0
    PhotoPath_S = ["Photo_1_0.bmp", "Photo_1_1.bmp", "Photo_1_2.bmp", "Photo_1_3.bmp", "Photo_1_4.bmp", "Photo_1_5.bmp", "Photo_1_6.bmp"]
    PhotoPath_L = ["Photo_2_0.bmp", "Photo_2_1.bmp", "Photo_2_2.bmp", "Photo_2_3.bmp", "Photo_2_4.bmp", "Photo_2_5.bmp", "Photo_2_6.bmp"]
    PagePath = ["Menu.bmp", "White_board.bmp", "Photo_1.bmp", "Photo_2.bmp"]

    while True:
        if i > 12 or ReFlag == 1:
            if Page == 1 and SelfFlag == 0:
                epd.displayPartial(epd.getbuffer(image))
            else:
                epd.displayPartial_Wait(epd.getbuffer(image))
            i = 0
            k = 0
            j += 1
            ReFlag = 0
            print("*** Draw Refresh ***\r\n")
        elif k > 50000 and i > 0 and Page == 1:
            epd.displayPartial(epd.getbuffer(image))
            i = 0
            k = 0
            j += 1
            print("*** Overtime Refresh ***\r\n")
        elif j > 50 or SelfFlag:
            SelfFlag = 0
            j = 0
            epd.init(epd.FULL_UPDATE)
            epd.displayPartBaseImage(epd.getbuffer(image))
            epd.init(epd.PART_UPDATE)
            print("--- Self Refresh ---\r\n")
        else:
            k += 1

        gt.GT_Scan(GT_Dev, GT_Old)
        if GT_Old.X[0] == GT_Dev.X[0] and GT_Old.Y[0] == GT_Dev.Y[0] and GT_Old.S[0] == GT_Dev.S[0]:
            continue

        if GT_Dev.TouchpointFlag:
            i += 1
            GT_Dev.TouchpointFlag = 0

            if Page == 0 and ReFlag == 0:  
                if GT_Dev.X[0] > 29 and GT_Dev.X[0] < 92 and GT_Dev.Y[0] > 56 and GT_Dev.Y[0] < 95:
                    print("Photo ...\r\n")
                    Page = 2
                    Read_BMP(PagePath[Page], 0, 0)
                    Show_Photo_Small(image, Photo_S)
                    ReFlag = 1
                elif GT_Dev.X[0] > 29 and GT_Dev.X[0] < 92 and GT_Dev.Y[0] > 153 and GT_Dev.Y[0] < 193:
                    print("Draw ...\r\n")
                    Page = 1
                    Read_BMP(PagePath[Page], 0, 0)
                    ReFlag = 1

            if Page == 1 and ReFlag == 0:
                DrawImage.rectangle([(GT_Dev.X[0], GT_Dev.Y[0]), (GT_Dev.X[0] + GT_Dev.S[0]/8 + 1, GT_Dev.Y[0] + GT_Dev.S[0]/8 + 1)], fill=0)
                if GT_Dev.X[0] > 96 and GT_Dev.X[0] < 118 and GT_Dev.Y[0] > 6 and GT_Dev.Y[0] < 30:
                    print("Home ...\r\n")
                    Page = 1
                    Read_BMP(PagePath[Page], 0, 0)
                    ReFlag = 1

        time.sleep(0.1)