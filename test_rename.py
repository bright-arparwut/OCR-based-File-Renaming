import pytest
from pathlib import Path

# Import functions from the main script
from rename_image import (
    find_pattern_in_text,
    get_unique_destination_path,
)

# --- Test find_pattern_in_text ---

def test_find_pattern_success():
    """Test that the regex correctly finds a valid pattern."""
    text = "Some random text before MT_PM_V1_TEST_CODE and some after."
    assert find_pattern_in_text(text) == "MT_PM_V1_TEST_CODE"

def test_find_pattern_at_start():
    """Test that the regex works when the pattern is at the beginning."""
    text = "MT_PM_START_01 is the code."
    assert find_pattern_in_text(text) == "MT_PM_START_01"

def test_find_pattern_failure():
    """Test that None is returned when no pattern is found."""
    text = "This text does not contain the required MT PM format."
    assert find_pattern_in_text(text) is None

def test_find_pattern_with_multiple_choices():
    """Test that it returns the first match found."""
    text = "First code is MT_PM_FIRST_A and second is MT_PM_SECOND_B"
    assert find_pattern_in_text(text) == "MT_PM_FIRST_A"

# --- Test get_unique_destination_path ---

# The `tmp_path` fixture provides a temporary directory unique to the test function
def test_get_unique_path_no_conflict(tmp_path: Path):
    """Test that the original filename is returned when there is no conflict."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    new_name = "MT_PM_UNIQUE_CODE"
    extension = ".jpg"
    
    expected_path = output_dir / "MT_PM_UNIQUE_CODE.jpg"
    
    assert get_unique_destination_path(str(output_dir), new_name, extension) == str(expected_path)

def test_get_unique_path_with_one_conflict(tmp_path: Path):
    """Test that '_1' is appended when one file with the same name exists."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create a conflicting file
    (output_dir / "MT_PM_CONFLICT.png").touch()
    
    new_name = "MT_PM_CONFLICT"
    extension = ".png"
    
    expected_path = output_dir / "MT_PM_CONFLICT_1.png"
    
    assert get_unique_destination_path(str(output_dir), new_name, extension) == str(expected_path)

def test_get_unique_path_with_multiple_conflicts(tmp_path: Path):
    """Test that it correctly finds the next available number suffix."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create conflicting files
    (output_dir / "MT_PM_MULTI.jpeg").touch()
    (output_dir / "MT_PM_MULTI_1.jpeg").touch()
    (output_dir / "MT_PM_MULTI_2.jpeg").touch()
    
    new_name = "MT_PM_MULTI"
    extension = ".jpeg"
    
    # The next available slot should be '_3'
    expected_path = output_dir / "MT_PM_MULTI_3.jpeg"
    
    assert get_unique_destination_path(str(output_dir), new_name, extension) == str(expected_path)
