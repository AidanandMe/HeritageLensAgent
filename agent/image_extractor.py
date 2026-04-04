import os
from pathlib import Path
try:
    from pypdf import PdfReader
except ImportError:
    print("WARNING: pypdf not installed.")

def extract_image_for_keyword(keyword: str) -> str:
    """
    Scans internal PDFs for the specified keyword. 
    If a page contains the keyword AND an image, it extracts the first image 
    and saves it to the ui/assets folder, returning the relative path.
    Returns None if no image is found.
    """
    if not keyword or len(keyword.strip()) < 3:
        return None
        
    keyword = keyword.lower().strip()
    
    # Setup paths
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(workspace_dir, "ui", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Path to save the extracted image
    # Always overwrite the same file to save space
    save_path = os.path.join(assets_dir, "extracted_context_image.png")
    
    # Scan all local PDFs
    for filepath in Path(workspace_dir).glob("*.pdf"):
        try:
            reader = PdfReader(str(filepath))
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and keyword in text.lower():
                    # Found the keyword on this page! Check for images.
                    if len(page.images) > 0:
                        image_obj = page.images[0]
                        # Extract and save
                        with open(save_path, "wb") as f:
                            f.write(image_obj.data)
                        
                        print(f"Extracted image from {filepath.name} page {page_num} for keyword '{keyword}'")
                        return save_path
        except Exception as e:
            print(f"Error reading {filepath.name}: {e}")
            continue
            
    # No image found containing the keyword
    return None

if __name__ == "__main__":
    # Internal test
    res = extract_image_for_keyword("ossidiana")
    print(f"Result: {res}")
