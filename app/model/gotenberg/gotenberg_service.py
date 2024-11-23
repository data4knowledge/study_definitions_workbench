from pathlib import Path
from typing import Optional, Union
from d4kms_generic.service import Service, httpx
from d4kms_generic.service_environment import ServiceEnvironment

class GotenbergService(Service):

    def __init__(self):
      """
      Initialize the Gotenberg converter.

      Args:
          base_url (str): The base URL of the Gotenberg service
      """
      se = ServiceEnvironment()
      url = se.get('GOTENBERG_SERVER_URL')
      self.convert_endpoint = f"{url}"
      super().__init__(url)

    async def convert_docx_to_pdf(
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
        docx_path = Path(docx_path)
        if not docx_path.exists():
            raise FileNotFoundError(f"Input file not found: {docx_path}")
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
        response = await self.file_post('/forms/libreoffice/convert', files, data)
        if 'data' in response and output_path:
            output_path = Path(output_path)
            output_path.write_bytes(response['data'])
            return True
        else:
            try:
                files['files'][1].close()
            except Exception as e:
                pass
            return response

    def health_check(self) -> bool:
        """
        Check if the Gotenberg service is available.

        Returns:
            bool: True if service is healthy, False otherwise
        """
        return self.get('/health')

    async def file_post(self, url, files, data={}):
      try:
        full_url = self._full_url(url)
        response = await self._client.post(full_url, files=files, data=data) if data else await self._client.post(full_url, files=files)
        return {'data': response.content} if response.status_code in [200, 201] else self._bad_response(response)
      except httpx.HTTPError as e:
        return self._exception("POST (file)", e)
