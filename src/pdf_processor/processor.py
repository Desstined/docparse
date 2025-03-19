from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import io
import os
import tempfile

import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import numpy as np

from src.config import settings

class PDFProcessor:
    def __init__(self):
        self.supported_versions = settings.SUPPORTED_PDF_VERSIONS
        self.max_size_mb = settings.MAX_PDF_SIZE_MB
        self.ocr_language = settings.OCR_LANGUAGE
        self.ocr_timeout = settings.OCR_TIMEOUT
        self.temp_dir = tempfile.mkdtemp()

    def __del__(self):
        """Clean up temporary files."""
        try:
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
        except:
            pass

    def validate_pdf(self, file_path: Union[str, Path]) -> bool:
        """Validate PDF file size and version."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise ValueError(f"PDF file too large. Maximum size is {self.max_size_mb}MB")

        # Check PDF version
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            version = pdf.metadata.get('/Version', '') if pdf.metadata else ''
            if version not in self.supported_versions:
                raise ValueError(f"Unsupported PDF version: {version}")

        return True

    def extract_text(self, file_path: Union[str, Path]) -> str:
        """Extract text from PDF file using multiple methods."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        # Try digital text extraction first
        digital_text = self._extract_digital_text(file_path)
        if digital_text.strip():
            return digital_text

        # If no digital text, try OCR on the whole document
        return self.extract_text_with_ocr(file_path)

    def _extract_digital_text(self, file_path: Path) -> str:
        """Extract digital text from PDF."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text.strip()

    def extract_text_with_ocr(self, file_path: Union[str, Path]) -> str:
        """Extract text from PDF using OCR for scanned documents."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        # Convert PDF to images
        images = convert_from_path(file_path)
        
        text = ""
        for image in images:
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Perform OCR
            text += pytesseract.image_to_string(
                Image.open(io.BytesIO(img_byte_arr)),
                lang=self.ocr_language,
                timeout=self.ocr_timeout
            ) + "\n"

        return text.strip()

    def extract_images(self, file_path: Union[str, Path]) -> List[Dict[str, Union[str, Image.Image]]]:
        """Extract images from PDF with their metadata."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        images = []
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Extract image metadata
                metadata = {
                    'page': page_num + 1,
                    'index': img_index,
                    'width': image.width,
                    'height': image.height,
                    'format': image.format,
                    'mode': image.mode,
                    'size_bytes': len(image_bytes)
                }
                
                # Perform OCR on the image
                try:
                    image_text = pytesseract.image_to_string(
                        image,
                        lang=self.ocr_language,
                        timeout=self.ocr_timeout
                    ).strip()
                    metadata['text'] = image_text
                except Exception as e:
                    metadata['text'] = f"OCR failed: {str(e)}"
                
                images.append({
                    'metadata': metadata,
                    'image': image
                })
        
        doc.close()
        return images

    def extract_images_to_files(self, file_path: Union[str, Path]) -> List[Dict[str, str]]:
        """Extract images from PDF and save them to files."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        image_files = []
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Generate unique filename
                filename = f"page_{page_num + 1}_img_{img_index}.png"
                filepath = os.path.join(self.temp_dir, filename)
                
                # Save image to file
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                # Convert to PIL Image for metadata
                image = Image.open(filepath)
                
                # Extract metadata
                metadata = {
                    'page': page_num + 1,
                    'index': img_index,
                    'width': image.width,
                    'height': image.height,
                    'format': image.format,
                    'mode': image.mode,
                    'size_bytes': len(image_bytes),
                    'filepath': filepath
                }
                
                # Perform OCR on the image
                try:
                    image_text = pytesseract.image_to_string(
                        image,
                        lang=self.ocr_language,
                        timeout=self.ocr_timeout
                    ).strip()
                    metadata['text'] = image_text
                except Exception as e:
                    metadata['text'] = f"OCR failed: {str(e)}"
                
                image_files.append(metadata)
        
        doc.close()
        return image_files

    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """Extract metadata from PDF file."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            metadata = pdf.metadata

        return {
            'title': metadata.get('/Title', ''),
            'author': metadata.get('/Author', ''),
            'subject': metadata.get('/Subject', ''),
            'keywords': metadata.get('/Keywords', ''),
            'creator': metadata.get('/Creator', ''),
            'producer': metadata.get('/Producer', ''),
            'creation_date': metadata.get('/CreationDate', ''),
            'modification_date': metadata.get('/ModDate', '')
        }

    def get_page_count(self, file_path: Union[str, Path]) -> int:
        """Get the number of pages in the PDF."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            return len(pdf.pages)

    def is_scanned(self, file_path: Union[str, Path]) -> bool:
        """Check if the PDF is a scanned document."""
        file_path = Path(file_path)
        self.validate_pdf(file_path)

        # Try to extract digital text
        digital_text = self._extract_digital_text(file_path)
        
        # If no digital text is found, it's likely scanned
        return not bool(digital_text.strip()) 