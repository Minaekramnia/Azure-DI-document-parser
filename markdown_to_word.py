"""
Convert Markdown Files to Word Documents

This script converts existing .md files to .docx format.
Uses pypandoc for conversion.
"""

import glob
import os
import subprocess


def convert_markdown_to_word(md_filepath, output_filepath):
    """
    Convert a single Markdown file to Word document using pandoc.
    
    Args:
        md_filepath: Path to the .md file
        output_filepath: Path for the output .docx file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use pandoc command line tool
        subprocess.run([
            'pandoc',
            md_filepath,
            '-o', output_filepath,
            '--from', 'markdown',
            '--to', 'docx'
        ], check=True, capture_output=True, text=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Pandoc error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"   ❌ Pandoc not found. Please install: pip install pypandoc")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def convert_all_markdown_files(data_path, output_folder_name='word_reports'):
    """
    Convert all Markdown files to Word documents.
    
    Args:
        data_path: Directory containing the Markdown files
        output_folder_name: Name of the output folder to create
    """
    # Find all Markdown analysis files
    md_files = glob.glob(f"{data_path}*_WORKING_analysis.md")
    
    if not md_files:
        print(f"❌ No *_WORKING_analysis.md files found in {data_path}")
        return
    
    # Create output folder
    output_path = os.path.join(data_path, output_folder_name)
    try:
        os.makedirs(output_path, exist_ok=True)
        print(f"✅ Output folder created: {output_path}")
    except Exception as e:
        print(f"❌ Could not create output folder: {e}")
        return
    
    print("\n🔄 Markdown to Word Converter")
    print("="*60)
    print(f"Input: {data_path}")
    print(f"Output: {output_path}/")
    print(f"Found {len(md_files)} Markdown files to convert")
    print("="*60)
    
    converted_count = 0
    error_count = 0
    
    for md_file in sorted(md_files):
        print(f"\n📄 Converting: {os.path.basename(md_file)}")
        
        try:
            # Create Word filename
            base_name = os.path.basename(md_file).replace('.md', '.docx')
            docx_filepath = os.path.join(output_path, base_name)
            
            # Convert
            success = convert_markdown_to_word(md_file, docx_filepath)
            
            if success:
                print(f"   ✅ Created: {base_name}")
                converted_count += 1
            else:
                error_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1
    
    print("\n" + "="*60)
    print("🎯 Conversion Complete!")
    print("="*60)
    print(f"✅ Successfully converted: {converted_count} files")
    if error_count > 0:
        print(f"❌ Errors: {error_count} files")
    print(f"\n📁 Output folder: {output_path}/")
    print(f"📄 Word files: *_WORKING_analysis.docx")
    print("="*60)


if __name__ == '__main__':
    # Path to the directory containing Markdown files
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    
    print("\n" + "="*60)
    print("🚀 MARKDOWN TO WORD CONVERTER")
    print("="*60)
    print(f"Source: {data_path}")
    print(f"Looking for: *_WORKING_analysis.md")
    print(f"Output: word_reports/ folder")
    print("="*60)
    
    convert_all_markdown_files(data_path)
    
    print("\n✅ All Markdown files converted to Word!")
    print("   📄 Open the .docx files in Microsoft Word")
    print("\n💡 Note: Requires pandoc to be installed")
    print("   Install: pip install pypandoc")


