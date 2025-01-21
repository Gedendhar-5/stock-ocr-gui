import re
import tkinter as tk
import os
from datetime import datetime
from tkinter import ttk, filedialog
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# Set Tesseract path (adjust this to your installation path)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Global set to track processed stocks
existing_stocks = set()

def preprocess_image(image):
    """Enhance the image for better OCR results."""
    grayscale_image = image.convert("L")
    contrast_image = ImageEnhance.Contrast(grayscale_image).enhance(2.5)
    sharp_image = ImageEnhance.Sharpness(contrast_image).enhance(2.0)
    resized_image = sharp_image.resize((sharp_image.width * 2, sharp_image.height * 2))
    return resized_image

def process_image_from_path(file_path):
    """Process an uploaded image to extract stocks meeting the criteria."""
    try:
        image = Image.open(file_path)
        processed_image = preprocess_image(image)
        extracted_text = pytesseract.image_to_string(processed_image)

        # Debug: Print extracted OCR text
        print("[DEBUG] OCR Extracted Text:")
        print(extracted_text)

        # Define helper functions for validation and conversion
        def is_valid_volume_or_float(value):
            return re.match(r"^\d+\.?\d*[MK]$", value)

        def is_valid_stock_ticker(ticker):
            return len(ticker) > 1 and len(ticker) <= 5 and ticker.isupper()

        def convert_to_number(value):
            if "M" in value:
                return float(value[:-1]) * 1_000_000
            elif "K" in value:
                return float(value[:-1]) * 1_000
            return float(value)

        # Regex pattern to capture stock ticker, volume, and float
        pattern = re.compile(
            r"\b([A-Z]{4})\b\s*[\s\w\W]*?(\d+\.?\d*[MK])\s*[\s\w\W]*?(\d+\.?\d*[MK])"
        )

        matches = pattern.findall(extracted_text)

        # Debug: Print raw matches
        print("[DEBUG] Raw Matches from OCR:")
        print(matches)

        # Filter stocks meeting the criteria (Volume > Float)
        validated_stocks = []
        for match in matches:
            stock_ticker, volume, float_value = match
            if is_valid_volume_or_float(volume) and is_valid_volume_or_float(float_value) and is_valid_stock_ticker(stock_ticker):
                volume_num = convert_to_number(volume)
                float_num = convert_to_number(float_value)
                if volume_num > float_num and stock_ticker not in existing_stocks:
                    validated_stocks.append((stock_ticker, volume, float_value))

        # Debug: Print validated stocks
        print("[DEBUG] Validated Stocks:")
        for stock in validated_stocks:
            print(stock)

        # Final re-validation step for missing first rows/columns
        if matches and matches[0] not in validated_stocks:
            validated_stocks.insert(0, matches[0])
            print(f"[DEBUG] Re-included first row: {matches[0]}")

        return validated_stocks
    except Exception as e:
        print(f"Error processing image: {e}")
        return []

def get_image_timestamp(file_path):
    """Retrieve the timestamp (date and time) of the uploaded image."""
    try:
        # Get the file's creation or modification time
        timestamp = os.path.getmtime(file_path)
        # Convert to human-readable date and time format
        readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return readable_time
    except Exception as e:
        print(f"Error retrieving timestamp: {e}")
        return "Unknown"

def display_stocks_in_window(stocks):
    """Display the stocks meeting the criteria in the Tkinter Treeview."""
    for stock in stocks:
        if stock[0] not in existing_stocks:
            tree.insert("", tk.END, values=(stock[0], stock[1], stock[2]))
            existing_stocks.add(stock[0])
    total_label.config(text=f"Total Stocks: {len(existing_stocks)}")

def upload_image():
    """Handle image upload and process it."""
    file_path = filedialog.askopenfilename(
        title="Select Image File",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")],
    )
    if file_path:
        # Get the image timestamp
        timestamp = get_image_timestamp(file_path)
        timestamp_label.config(text=f"Image Timestamp: {timestamp}")

        # Process the image and display stocks
        stocks = process_image_from_path(file_path)
        display_stocks_in_window(stocks)



# Tkinter GUI setup
root = tk.Tk()
root.title("Stocks with Volume Greater Than Float")

tree = ttk.Treeview(root, columns=("Stock", "Volume", "Float"), show="headings", height=10)
tree.pack(fill=tk.BOTH, expand=True)

tree.heading("Stock", text="Stock Ticker")
tree.heading("Volume", text="Volume")
tree.heading("Float", text="Float")

tree.column("Stock", width=150, anchor="center")
tree.column("Volume", width=150, anchor="center")
tree.column("Float", width=150, anchor="center")

total_label = tk.Label(root, text="Total Stocks: 0")
total_label.pack(pady=10)

# Add the timestamp label
timestamp_label = tk.Label(root, text="Image Timestamp: Unknown")
timestamp_label.pack(pady=5)

upload_button = tk.Button(root, text="Upload Image", command=upload_image)
upload_button.pack(pady=10)

root.mainloop()
