import os
import glob
import re
import shutil
import easyocr
import argparse
import logging
from typing import List, Optional

# --- Configuration ---
ALLOWED_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")
REGEX_PATTERN = r"(MT_PM_[\w_]+)"

def setup_logging():
    """Configures the logging system to output to both console and a file."""
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set the lowest level to capture all messages

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler('renamer.log', mode='w')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Create a console handler to display logs on the screen
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def setup_directories(output_path: str, error_path: str):
    """Creates the specified output and error directories if they don't exist."""
    logging.info("Initializing output directories...")
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(error_path, exist_ok=True)
    logging.info(f"  - Output directory: '{output_path}'")
    logging.info(f"  - Error directory: '{error_path}'")

def find_image_files(source_path: str) -> List[str]:
    """Finds all image files with allowed extensions directly in the source path."""
    if not os.path.isdir(source_path):
        logging.error(f"Source directory not found at '{source_path}'")
        return []
        
    image_files = []
    for ext in ALLOWED_EXTENSIONS:
        search_path = os.path.join(source_path, ext)
        image_files.extend(glob.glob(search_path))
    return image_files

def extract_text_from_image(image_path: str, reader: easyocr.Reader) -> str:
    """Extracts all text from an image and returns it as a single string."""
    results = reader.readtext(image_path, detail=0, paragraph=True)
    return " ".join(results)

def normalize_pattern(pattern: str) -> str:
    """
    Corrects common OCR errors specifically in the version part of a found pattern.
    Example: "MT_PM_VI_..." -> "MT_PM_V1_..."
    """
    match = re.match(r"(MT_PM_V)([^_]+)(_.*)", pattern)
    if match:
        prefix, version_part, suffix = match.groups()
        corrections = str.maketrans("IiLlOo", "111100")
        normalized_version = version_part.translate(corrections)
        return f"{prefix}{normalized_version}{suffix}"
    return pattern

def find_pattern_in_text(text: str) -> Optional[str]:
    """Searches for the specific regex pattern in the extracted text."""
    match = re.search(REGEX_PATTERN, text)
    if match:
        return match.group(1)
    return None

def get_unique_destination_path(base_path: str, new_name: str, extension: str) -> str:
    """Checks for filename collisions and returns a unique path."""
    filename = f"{new_name}{extension}"
    destination_path = os.path.join(base_path, filename)
    counter = 1
    while os.path.exists(destination_path):
        unique_filename = f"{new_name}_{counter}{extension}"
        destination_path = os.path.join(base_path, unique_filename)
        counter += 1
    return destination_path

def process_images(source_path: str, output_path: str, error_path: str, reader: easyocr.Reader):
    """
    Main processing logic for the specified source folder.
    """
    image_files = find_image_files(source_path)
    total_files = len(image_files)

    if total_files == 0:
        logging.info(f"No image files found in '{source_path}'. Exiting.")
        return

    logging.info(f"Found {total_files} images to process in '{source_path}'.")
    
    success_count = 0
    fail_count = 0

    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        logging.info(f"[{i}/{total_files}] Processing '{filename}'...")

        try:
            extracted_text = extract_text_from_image(image_path, reader)
            initial_pattern = find_pattern_in_text(extracted_text)

            if initial_pattern:
                new_name_base = normalize_pattern(initial_pattern)
                original_extension = os.path.splitext(filename)[1]
                
                destination_path = get_unique_destination_path(output_path, new_name_base, original_extension)
                shutil.copy2(image_path, destination_path)
                
                logging.info(f"  SUCCESS: Found pattern '{new_name_base}'. Copied to '{output_path}'.")
                success_count += 1
            else:
                error_destination = os.path.join(error_path, filename)
                shutil.move(image_path, error_destination)
                logging.warning(f"  FAILED: Pattern not found. Moved '{filename}' to '{error_path}'.")
                fail_count += 1

        except Exception as e:
            logging.error(f"An unexpected error occurred while processing '{filename}'.", exc_info=True)
            try:
                error_destination = os.path.join(error_path, filename)
                if os.path.exists(image_path):
                    shutil.move(image_path, error_destination)
            except Exception as move_e:
                logging.error(f"Could not move file '{filename}' to error directory: {move_e}")
            fail_count += 1
            
    logging.info("-------------------------------------------")
    logging.info(f"Processing complete. Successful: {success_count}, Failed: {fail_count}.")
    logging.info("-------------------------------------------")

def main():
    """
    Main entry point. Parses command-line arguments and processes images.
    """
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="OCR-based File Renamer with flexible source and destination paths."
    )
    parser.add_argument('--source', required=True, help='Path to the folder with source images.')
    parser.add_argument('--output', required=True, help='Path to the folder for successfully renamed images.')
    parser.add_argument('--error', required=True, help='Path to the folder for images where the pattern was not found.')
    args = parser.parse_args()

    setup_directories(args.output, args.error)

    logging.info("Loading OCR model (this may take a moment)...")
    try:
        reader = easyocr.Reader(['en'])
        logging.info("OCR model loaded successfully.")
    except Exception as e:
        logging.critical("Fatal Error: Could not load OCR model. Please check your EasyOCR installation.", exc_info=True)
        return

    process_images(args.source, args.output, args.error, reader)

if __name__ == "__main__":
    main()
