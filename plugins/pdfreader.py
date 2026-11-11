import re
from datetime import datetime
from pathlib import Path
from shutil import copy2
from urllib.parse import quote
import pymupdf
import markdown
from pelican import signals
from pelican.readers import BaseReader


class PdfReader(BaseReader):
    enabled = True
    file_extensions = ['pdf']

    def _parse_pdf_date(self, pdf_date_str, fallback_ts):
        """Convert PDF date format (e.g. D:20261111153000+01'00') to datetime."""
        if pdf_date_str:
            # Extract the first 14 digits (YYYYMMDDHHMMSS)
            match = re.search(r'(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?', pdf_date_str)
            if match:
                parts = [int(p) if p is not None else 0 for p in match.groups()]
                # Ensure month and day default to 1 if zeroed out
                year, month, day, hour, minute, second = parts
                month = max(1, min(12, month))
                day = max(1, min(31, day))
                try:
                    return datetime(year, month, day, hour, minute, second)
                except ValueError:
                    pass
        return datetime.fromtimestamp(fallback_ts)

    def _pdf_to_markdown(self, document, image_dir, slug):
        pages = []
        image_index = 0
        for page_number, page in enumerate(document, start=1):
            blocks = []
            for block in page.get_text('dict')['blocks']:
                if block['type'] == 0:
                    text = '\n'.join(
                        ''.join(span['text'] for span in line['spans'])
                        for line in block['lines']
                    ).strip()
                    if text:
                        blocks.append(text)
                elif block['type'] == 1:
                    image_index += 1
                    extension = block.get('ext', 'png')
                    if not re.fullmatch(r'[A-Za-z0-9]+', extension):
                        extension = 'bin'
                    filename = f'page-{page_number}-image-{image_index}.{extension}'
                    image_dir.mkdir(parents=True, exist_ok=True)
                    (image_dir / filename).write_bytes(block['image'])
                    blocks.append(
                        f'![PDF image]({{static}}/documents/{slug}/{filename})'
                    )
            if blocks:
                pages.append('\n\n'.join(blocks))
        return '\n\n'.join(pages)

    def read(self, filename):
        content_dir = Path(self.settings.get('PATH', 'content')).resolve()
        documents_dir = (content_dir / 'documents').resolve()
        pdf_path = Path(filename).resolve()
        try:
            pdf_path.relative_to(documents_dir)
        except ValueError:
            return "", {'status': 'skip'}
        if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
            return "", {'status': 'skip'}

        # Open the PDF with PyMuPDF to inspect metadata and extract page content.
        with pymupdf.open(str(pdf_path)) as doc:
            pdf_meta = doc.metadata or {}

            fallback_title = pdf_path.stem.replace('-', ' ').replace('_', ' ').title()
            raw_title = (pdf_meta.get('title') or '').strip()
            title = raw_title if raw_title else fallback_title
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

            pdf_date_str = pdf_meta.get('creationDate') or pdf_meta.get('modDate')
            article_date = self._parse_pdf_date(pdf_date_str, pdf_path.stat().st_mtime)

            author = (pdf_meta.get('author') or '').strip()
            keywords = (pdf_meta.get('keywords') or '').strip()
            subject = (pdf_meta.get('subject') or '').strip()
            image_dir = documents_dir / slug
            md_text = self._pdf_to_markdown(doc, image_dir, slug)

        md_text += (
            f"\n\n---\n*[Download original PDF]({quote(pdf_path.name)})*"
        )
        md_extensions = self.settings.get('MARKDOWN', {}).get('extensions', ['extra', 'meta'])
        html_content = markdown.markdown(md_text, extensions=md_extensions)

        article_path = f'articles/documents/{slug}.html'
        output_dir = Path(self.settings.get('OUTPUT_PATH', 'output')).resolve()
        pdf_destination = output_dir / Path(article_path).parent / pdf_path.name
        pdf_destination.parent.mkdir(parents=True, exist_ok=True)
        if pdf_destination != pdf_path:
            copy2(pdf_path, pdf_destination)

        raw_metadata = {
            'title': title,
            'date': article_date.isoformat(sep=' '),
            'category': self.settings.get('PDF_DEFAULT_CATEGORY', 'Documents'),
            'slug': slug,
            'url': article_path,
            'save_as': article_path,
        }
        if author:
            raw_metadata['author'] = author
        if keywords:
            # Normalize semicolon or comma-separated PDF keywords into comma-separated tags
            raw_metadata['tags'] = keywords.replace(';', ',')
        if subject:
            raw_metadata['summary'] = subject

        parsed_metadata = {}
        for key, value in raw_metadata.items():
            parsed_metadata[key] = self.process_metadata(key, value)

        return html_content, parsed_metadata


def add_reader(readers):
    readers.reader_classes['pdf'] = PdfReader


def register():
    signals.readers_init.connect(add_reader)
