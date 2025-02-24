import arxiv
import os
import subprocess
from ebooklib import epub
import requests
import shutil

def download_and_convert_papers(search_query, output_dir="papers", kobo_path="/path/to/kobo"):
    """
    Download papers from Arxiv and convert them to Kobo-compatible ePub format
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize Arxiv client
    client = arxiv.Client()
    
    # Search for papers
    search = arxiv.Search(query=search_query)
    
    for paper in client.results(search):
        print(f"Processing: {paper.title}")
        
        paper_dir = os.path.join(output_dir, paper.get_short_id())
        os.makedirs(paper_dir, exist_ok=True)
        
        # Try to get LaTeX source first
        try:
            source_url = paper.get_source_url()
            if source_url and source_url.endswith('.tar.gz'):
                source_path = os.path.join(paper_dir, "source.tar.gz")
                response = requests.get(source_url)
                with open(source_path, 'wb') as f:
                    f.write(response.content)
                # Extract and compile LaTeX (you'll need latex installed)
                subprocess.run(['tar', 'xzf', source_path], cwd=paper_dir)
                subprocess.run(['pdflatex', 'main.tex'], cwd=paper_dir)
                pdf_path = os.path.join(paper_dir, 'main.pdf')
            else:
                # If LaTeX not available, download PDF
                pdf_path = os.path.join(paper_dir, "paper.pdf")
                paper.download_pdf(pdf_path)
            
            # Convert PDF to ePub using Calibre (needs to be installed)
            epub_path = os.path.join(paper_dir, f"{paper.get_short_id()}.epub")
            subprocess.run(['ebook-convert', pdf_path, epub_path])
            
            # Create Kobo-compatible ePub
            book = epub.EpubBook()
            book.set_title(paper.title)
            book.set_language('en')
            book.add_author(', '.join(paper.authors))
            
            # Copy to Kobo device
            kobo_dest = os.path.join(kobo_path, os.path.basename(epub_path))
            shutil.copy2(epub_path, kobo_dest)
            
            print(f"Successfully processed and copied to Kobo: {paper.title}")
            
        except Exception as e:
            print(f"Error processing {paper.title}: {str(e)}")

# Example usage
if __name__ == "__main__":
    search_query = "quantum computing"  # Replace with your search terms
    download_and_convert_papers(search_query, kobo_path="media/kobo")  # Adjust Kobo path
