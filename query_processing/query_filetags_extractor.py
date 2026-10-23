import re
import os

class FileNameExtractor:
    """Extracts valid filenames enclosed in [[ ]] tags with extension/name validation."""
    
    VALID_EXTENSIONS = {"pdf", "docx", "txt", "xlsx", "pptx", "py", "sh", "csv"}
    VALID_NAMES = {"README", "LICENSE"}  # Files without extensions

    @staticmethod
    def extract(text):
        """Extracts and validates filenames from [[ ]] tags."""
        extracted = re.findall(r'\[\[(.*?)\]\]', text)
        valid_filenames = []
        
        for file in extracted:
            # Check for valid extensionless filenames first
            if file in FileNameExtractor.VALID_NAMES:
                valid_filenames.append(file)
                continue
                
            # Split filename and extension
            name_part, ext = os.path.splitext(file)
            ext = ext.lstrip('.').lower()  # Normalize extension
            
            # Validate extensions
            if ext in FileNameExtractor.VALID_EXTENSIONS:
                valid_filenames.append(file)
                
        return tuple(valid_filenames)

# # Example usage
# text = """
# Analyze [[data.xlsx]], compare with [[Q3_report.PDF]], 
# check [[README]] and [[CONFIG]], ignore [[temp.txt.old]].
# """

# result = FileNameExtractor.extract(text)
# print(result)  # Output: ('data.xlsx', 'Q3_report.PDF', 'README')