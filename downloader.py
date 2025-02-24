import arxiv
import os
import subprocess
from ebooklib import epub
import requests
import shutil

def epub_from_latex(paper, paper_dir):
    """
    Convert LaTeX source files to EPUB format
    
    Args:
        paper: arxiv.Result object containing paper metadata
        paper_dir: Path to directory containing paper files
        source_subdir: Path to directory containing extracted LaTeX source
        
    Returns:
        str: Path to generated EPUB file
    """
    source_url = f"https://arxiv.org/src/{paper.get_short_id()}"
    response = requests.get(source_url)
    if response.status_code == 200 and response.headers.get('content-type') == 'application/gzip':
        source_path = os.path.join(paper_dir, "latex.tar.gz")
        with open(source_path, 'wb') as f:
            f.write(response.content)
        # Extract LaTeX source
        source_subdir = os.path.join(paper_dir, "latex_extracted")
        os.makedirs(source_subdir, exist_ok=True)
        subprocess.run(['tar', '-xvf', "latex.tar.gz", '-C', "latex_extracted"], cwd=paper_dir)

    # Find the main tex file
    tex_files = [f for f in os.listdir(source_subdir) if f.endswith('.tex')]
    main_tex = 'templateArxiv.tex'
    if 'templateArxiv.tex' not in tex_files and tex_files:
        main_tex = tex_files[0]  # Use the first tex file if main.tex not found
    
    # Convert directly from LaTeX to EPUB using pandoc
    tex_path = os.path.join(source_subdir, main_tex)
    epub_path = os.path.join(paper_dir, f"{paper.get_short_id()}.epub")
    
    print(f"Starting conversion of {os.path.basename(tex_path)} to EPUB...")
    subprocess.run([
        'pandoc',
        main_tex,
        '-f', 'latex',
        '-t', 'epub',
        '-o', f"{paper.get_short_id()}.epub",
        '--toc',
        '--standalone'
    ], check=True, cwd=source_subdir)
    print(f"Conversion complete: {os.path.basename(epub_path)}")
    
    return epub_path

# def epub_from_pdf(paper, paper_dir):
#     """Convert PDF to EPUB format"""
#     # Download PDF
#     pdf_path = os.path.join(paper_dir, f"{paper.get_short_id()}.pdf")
#     paper.download_pdf(filename=pdf_path)
    
#     # Convert to EPUB
#     epub_path = os.path.join(paper_dir, f"{paper.get_short_id()}.epub")
    
#     try:
#         convert(pdf_path, epub_path)
#     except Exception as e:
#         print(f"PDF conversion failed: {e}")
#         # Optionally fall back to ebook-convert if available
#         subprocess.run(['ebook-convert', pdf_path, epub_path], check=True)
#     return epub_path

def download_and_convert_papers(search_query, output_dir="papers", kobo_path="/path/to/kobo"):
    """
    Download papers from Arxiv and convert them to Kobo-compatible ePub format
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize Arxiv client and determine if input is ID or search
    client = arxiv.Client()
    
    # Check if input is an Arxiv ID
    if search_query.replace('.','').isdigit() or (len(search_query.split('/')) == 2 and search_query.split('/')[1].replace('.','').isdigit()):
        # Handle single paper case
        paper_id = search_query.split('/')[-1] if '/' in search_query else search_query
        search = arxiv.Search(id_list=[paper_id])
        results = list(client.results(search))
        if not results:
            raise ValueError(f"No paper found with ID {paper_id}")
        paper = results[0]
    else:
        # Handle search case - let user choose from results
        search = arxiv.Search(query=search_query, max_results=10)
        results = list(client.results(search))
        if not results:
            raise ValueError(f"No papers found matching '{search_query}'")
        
        print("\nFound papers:")
        for i, paper in enumerate(results):
            print(f"[{i}] {paper.title} ({paper.get_short_id()})")
            
        while True:
            try:
                choice = int(input("\nEnter number of paper to download: "))
                if 0 <= choice < len(results):
                    paper = results[choice]
                    break
                print("Invalid choice, try again")
            except ValueError:
                print("Please enter a number")
    
    print(f"Processing: {paper.title}")
    
    paper_dir = os.path.join(output_dir, paper.get_short_id())
    os.makedirs(paper_dir, exist_ok=True)
    
    # Try to get LaTeX source first
    try:
        paper_id = paper.get_short_id()

        # epub_path = epub_from_latex(paper, paper_dir)
        # Download PDF and convert to ePub
        epub_path = epub_from_latex(paper, paper_dir)
        
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
    search_query = "2308.06721"  # Replace with your search terms
    download_and_convert_papers(search_query, kobo_path="media/kobo")  # Adjust Kobo path
