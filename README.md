Flexible OCR-based File Renamer
This project provides a Python script (rename_images_flexible.py) that can be executed from any location to automatically rename image files based on text content found within them. It is designed to process multiple project folders in a single run.

The script's primary function is to find a specific code pattern (e.g., MT_PM_...), extract it, and use it as the new filename.

✨ Features
Run From Anywhere: The script is decoupled from the project data. You can store it centrally and point it to any project directory.

Batch Processing: Process multiple project folders sequentially in a single command.

File Scanning: Scans for .jpg, .jpeg, and .png files within a designated input_images subdirectory in each project folder.

OCR Text Extraction: Utilizes easyocr to accurately extract English text from images.

Smart Renaming: Renames files using the discovered pattern and saves them to an output_images subdirectory.

Conflict Resolution: Automatically handles filename collisions by appending a numerical suffix (e.g., CODE_1.jpg, CODE_2.jpg).

Error Handling: Moves any files where the pattern is not found to an error_images subdirectory for easy review.

📂 Required Directory Structure
For the script to function correctly, each project folder you wish to process must adhere to the following structure:

/path/to/your/project_folder/
|
|-- /input_images/           <-- Place your source images here
|   |-- IMG_001.jpg
|   |-- photo_ABC.png
|
|-- /output_images/          <-- (This will be created automatically)
|
|-- /error_images/           <-- (This will be created automatically)

🚀 How to Use
1. Setup
First, place the script files (rename_images_flexible.py, requirements.txt) in a convenient, centralized location (e.g., C:\scripts\).

Next, install the necessary libraries. It is highly recommended to use a Python virtual environment.

# Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies from the requirements file
pip install -r requirements.txt

Note: The first time you run the script, easyocr will download the required language models, which may take a few moments. An internet connection is required for this initial setup.

2. Prepare Project Folders
Organize your images according to the directory structure specified above, placing all images for a given project inside its input_images subdirectory.

3. Run the Script
Open your terminal (Command Prompt, PowerShell, or other) and execute the script, providing the path(s) to your project folder(s) as arguments.

Example 1: Processing a single project

python C:\scripts\rename_images_flexible.py D:\Work\Project_A

Example 2: Processing multiple projects at once

python C:\scripts\rename_images_flexible.py D:\Work\Project_A E:\Photos\Project_B

Example 3: Handling paths with spaces
Ensure that any path containing spaces is enclosed in double quotes (" ").

python C:\scripts\rename_images_flexible.py "D:\My Work\Project Alpha"

The script will then iterate through each specified project, creating the output_images and error_images directories as needed.

🧪 Running Tests
You can verify the core logic of the script by running the included tests with pytest.

# Navigate to the directory containing test_rename_logic.py
pytest
