from PIL import Image, ImageDraw, ImageFont
import textwrap
from waveshare_epd import epd2in13_V2
import time
import os

def update_display_with_option():
    # Display initialization
    display = epd2in13_V2.EPD()  # Initialize the correct display driver
    display.init()
    display.Clear(0xFF)  # Clear the display with white background

    # Update dimensions for 2.13-inch display
    w = display.height  # 122 pixels
    h = display.width   # 250 pixels

    # Prompt the user for input
    mode = input("Would you like to display an image or text? (Enter 'image' or 'text'): ").strip().lower()

    if mode == 'image':
        # Load and display an image
        image_path = input("Enter the full path to the image file: ").strip()
        try:
            image = Image.open(image_path).convert('1')  # Convert to 1-bit image
            image = image.resize((w, h), Image.ANTIALIAS)  # Resize to fit the display
            display.display(display.getbuffer(image))
            print("Image displayed successfully.")
        except Exception as e:
            print(f"Error displaying the image: {e}")

    elif mode == 'text':
        # Text display initialization
        message = input("Please enter a message you would like to display: ")

        # Create a blank image for text
        image = Image.new(mode='1', size=(w, h), color=255)
        draw = ImageDraw.Draw(image)

        # Font and text settings
        font_size = 16  # Smaller font size for smaller display
        font_file = '/home/pi/fonts/NotoSans-Regular.ttf'  # Update path as needed
        font = ImageFont.truetype(font_file, font_size)

        # Calculate text size and wrap text
        wrapped_text = textwrap.fill(message, width=20)  # Adjust width as needed
        lines = wrapped_text.split('\n')
        text_height = len(lines) * font_size

        # Center vertically
        y = (h - text_height) // 2

        # Display each line
        for line in lines:
            text_width, _ = draw.textsize(line, font=font)
            x = (w - text_width) // 2  # Center horizontally
            draw.text((x, y), line, font=font, fill=0, align='center')
            y += font_size  # Move to the next line

        # Update the e-Ink display
        display.display(display.getbuffer(image))
        print("Text displayed successfully.")

    else:
        print("Invalid input. Please enter 'image' or 'text'.")

# Call the function
update_display_with_option()