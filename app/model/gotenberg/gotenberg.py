import requests
from pathlib import Path
from typing import Optional, Union


class GotenbergConverter:
    """A class to interface with Gotenberg API for document conversions."""

    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize the Gotenberg converter.

        Args:
            base_url (str): The base URL of the Gotenberg service
        """
        self.base_url = base_url.rstrip('/')
        self.convert_endpoint = f"{self.base_url}/forms/libreoffice/convert"

    def convert_docx_to_pdf(
        self,
        docx_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        landscape: bool = False,
        page_ranges: str = "",
        pdf_format: str = "A4"
    ) -> Union[bytes, bool]:
        """
        Convert a DOCX file to PDF using Gotenberg.

        Args:
            docx_path (Union[str, Path]): Path to the input DOCX file
            output_path (Optional[Union[str, Path]]): Path to save the output PDF
            landscape (bool): Whether to use landscape orientation
            page_ranges (str): Page ranges to include (e.g., "1-3,5,7-9")
            pdf_format (str): PDF page format (e.g., "A4", "Letter")

        Returns:
            Union[bytes, bool]: PDF content as bytes if no output_path is specified,
                              True if file was saved successfully, False otherwise
        """
        # Validate input file
        docx_path = Path(docx_path)
        if not docx_path.exists():
            raise FileNotFoundError(f"Input file not found: {docx_path}")

        # Prepare the files and data for the request
        files = {
            'files': (docx_path.name, open(docx_path, 'rb'), 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }

        data = {
            'landscape': str(landscape).lower(),
            'paperWidth': 8.27,  # A4 width in inches
            'paperHeight': 11.7,  # A4 height in inches
        }

        if page_ranges:
            data['pageRanges'] = page_ranges

        try:
            # Make the conversion request
            response = requests.post(
                self.convert_endpoint,
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()

            # Handle the response
            if output_path:
                output_path = Path(output_path)
                output_path.write_bytes(response.content)
                return True
            else:
                return response.content

        except requests.exceptions.RequestException as e:
            print(f"Error during conversion: {e}")
            return False

        finally:
            files['files'][1].close()

    def health_check(self) -> bool:
        """
        Check if the Gotenberg service is available.

        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


# Example usage:
if __name__ == "__main__":
    converter = GotenbergConverter("http://localhost:3000")
    
    # Check if service is available
    if converter.health_check():
        # Convert a document
        result = converter.convert_docx_to_pdf(
            docx_path="document.docx",
            output_path="output.pdf",
            landscape=False,
            page_ranges="1-5"
        )
        
        if result:
            print("Conversion successful!")
        else:
            print("Conversion failed!")
    else:
        print("Gotenberg service is not available!")