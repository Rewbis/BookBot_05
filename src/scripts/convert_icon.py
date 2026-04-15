from PIL import Image
import os

def convert_png_to_ico(png_path, ico_path):
    img = Image.open(png_path)
    # Icon sizes to include
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"Icon converted and saved to {ico_path}")

if __name__ == "__main__":
    # Path to the generated icon
    source = r"C:\Users\b_wes\.gemini\antigravity\brain\28d4d6e9-be2d-447b-8db7-e05d58573d06\bookbot_icon_1776258767742.png"
    dest = r"e:\Coding\BookBot_05\src\scripts\bookbot.ico"
    if os.path.exists(source):
        convert_png_to_ico(source, dest)
    else:
        print(f"Source icon not found at {source}")
