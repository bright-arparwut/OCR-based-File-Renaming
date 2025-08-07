import os
import glob
import re
import shutil
import easyocr
import argparse
from typing import List, Optional

# --- Configuration (Default Subdirectory Names) ---
INPUT_SUBDIR = "input_images"
OUTPUT_SUBDIR = "output_images"
ERROR_SUBDIR = "error_images"
ALLOWED_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")
REGEX_PATTERN = r"(MT_PM_[\w_]+)"

def setup_directories(project_path: str):
    """Creates output and error directories inside the given project path."""
    output_path = os.path.join(project_path, OUTPUT_SUBDIR)
    error_path = os.path.join(project_path, ERROR_SUBDIR)
    
    print(f"Initializing directory structure for '{project_path}'...")
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(error_path, exist_ok=True)
    print(f"  - Output directory: '{output_path}'")
    print(f"  - Error directory: '{error_path}'")

def find_image_files(project_path: str) -> List[str]:
    """Finds all image files in the input subdirectory of the project path."""
    input_path = os.path.join(project_path, INPUT_SUBDIR)
    if not os.path.isdir(input_path):
        return []
        
    image_files = []
    for ext in ALLOWED_EXTENSIONS:
        search_path = os.path.join(input_path, ext)
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
    - Replaces 'I', 'i', 'l' with '1'.
    - Replaces 'O', 'o' with '0'.
    """
    # Regex to capture three parts:
    # 1. The static prefix ("MT_PM_V")
    # 2. The version part to be normalized (one or more characters until the next underscore)
    # 3. The rest of the string (from the underscore onwards)
    match = re.match(r"(MT_PM_V)([^_]+)(_.*)", pattern)

    if match:
        prefix = match.group(1)
        version_part = match.group(2)
        suffix = match.group(3)

        # Apply normalization only to the version part
        corrections = str.maketrans("IiLlOo", "111100")
        normalized_version = version_part.translate(corrections)

        # Reconstruct the pattern
        return f"{prefix}{normalized_version}{suffix}"
    
    # If the pattern doesn't match the expected structure (e.g., doesn't start with "MT_PM_V"),
    # return it unchanged.
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

def process_project_folder(project_path: str, reader: easyocr.Reader):
    """
    Orchestrates the OCR-based file renaming process for a single project folder.
    """
    print(f"\n{'='*20} Processing Project: {project_path} {'='*20}")
    
    if not os.path.isdir(project_path):
        print(f"Error: Project path not found or is not a directory: '{project_path}'")
        return

    input_dir = os.path.join(project_path, INPUT_SUBDIR)
    output_dir = os.path.join(project_path, OUTPUT_SUBDIR)
    error_dir = os.path.join(project_path, ERROR_SUBDIR)

    setup_directories(project_path)
    image_files = find_image_files(project_path)
    total_files = len(image_files)

    if total_files == 0:
        print(f"\nNo image files found in '{input_dir}'. Skipping.")
        return

    print(f"\nFound {total_files} images to process.")
    
    success_count = 0
    fail_count = 0

    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        print(f"\n[{i}/{total_files}] Processing '{filename}'...")

        try:
            # Step 1: Extract text from the image
            extracted_text = extract_text_from_image(image_path, reader)
            
            # Step 2: Find the initial pattern from the raw text
            initial_pattern = find_pattern_in_text(extracted_text)

            if initial_pattern:
                # Step 3: NEW - Normalize only the found pattern string
                new_name_base = normalize_pattern(initial_pattern)
                
                original_extension = os.path.splitext(filename)[1]
                destination_path = get_unique_destination_path(output_dir, new_name_base, original_extension)
                new_filename = os.path.basename(destination_path)
                
                shutil.copy2(image_path, destination_path)
                
                if new_filename != f"{new_name_base}{original_extension}":
                    print(f"   SUCCESS: Found pattern '{new_name_base}'. File already exists. Renaming to '{new_filename}'.")
                else:
                    print(f"   SUCCESS: Found pattern '{new_name_base}'. Renaming to '{new_filename}'.")
                
                success_count += 1
            else:
                error_destination = os.path.join(error_dir, filename)
                shutil.move(image_path, error_destination)
                print(f"   FAILED: Pattern not found. Moving file to '{error_dir}'.")
                fail_count += 1

        except Exception as e:
            print(f"   ERROR: An unexpected error occurred: {e}")
            error_destination = os.path.join(error_dir, filename)
            if os.path.exists(image_path):
                shutil.move(image_path, error_destination)
            fail_count += 1
            
    print("\n-------------------------------------------")
    print(f"Processing for '{project_path}' complete. Successful: {success_count}, Failed: {fail_count}.")
    print("-------------------------------------------")

def main():
    """
    Main entry point. Parses command-line arguments and processes project folders.
    """
    parser = argparse.ArgumentParser(
        description="OCR-based File Renamer. Processes one or more project folders."
    )
    parser.add_argument(
        "project_paths",
        metavar="PROJECT_PATH",
        type=str,
        nargs="+",
        help="One or more paths to project folders. Each folder must contain an 'input_images' subdirectory."
    )
    args = parser.parse_args()

    print("Loading OCR model (this may take a moment)...")
    try:
        reader = easyocr.Reader(['en'])
        print("OCR model loaded successfully.")
    except Exception as e:
        print(f"Fatal Error: Could not load OCR model. Please check your EasyOCR installation. Details: {e}")
        return

    for project_path in args.project_paths:
        process_project_folder(project_path.strip(), reader)

if __name__ == "__main__":
    main()
