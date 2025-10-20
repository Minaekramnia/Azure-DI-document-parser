"""
Convert PageNumbers JSON Analysis to Markdown and Word Documents

This script:
1. Finds all *_WORKING_PageNumbers_analysis.json files
2. Converts them to Markdown format (with page number tracking)
3. Converts Markdown to Word documents
4. Saves outputs in organized folders
"""

import json
import glob
import os
import subprocess
from datetime import datetime


def convert_json_to_markdown(json_filepath, output_filepath):
    """
    Convert JSON analysis to human-readable Markdown format.
    Includes page number information for each classification.
    
    Args:
        json_filepath: Path to the JSON file
        output_filepath: Path for the output .md file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load JSON
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Start building Markdown
        md_content = []
        
        # Header
        md_content.append("# Document Analysis Report (with Page Numbers)\n")
        md_content.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_content.append(f"**Source Document**: `{os.path.basename(data.get('document_path', 'Unknown'))}`\n")
        md_content.append(f"**Total Pages**: {data.get('total_pages', 'Unknown')}\n")
        md_content.append(f"**Total Segments**: {data.get('total_segments', 'Unknown')}\n")
        md_content.append("\n---\n\n")
        
        # Process each segment
        segments = data.get('segments', [])
        
        if not segments:
            md_content.append("*No segments found in this document.*\n")
        
        for segment in segments:
            segment_id = segment.get('segment_id', 'Unknown')
            page_range = segment.get('page_range', 'Unknown')
            
            md_content.append(f"## Segment: {segment_id}\n")
            md_content.append(f"**Pages**: {page_range}\n\n")
            
            # Extracted Names
            extracted_names = segment.get('extracted_names', [])
            md_content.append("### 📋 Extracted Names\n")
            if extracted_names:
                for name in extracted_names:
                    md_content.append(f"- {name}\n")
            else:
                md_content.append("*No names extracted*\n")
            md_content.append("\n")
            
            # Classifications
            classifications = segment.get('classifications', [])
            md_content.append("### 🔍 Sensitive Content Classifications\n")
            
            if not classifications:
                md_content.append("*No sensitive content identified*\n\n")
            else:
                md_content.append(f"**Total Classifications**: {len(classifications)}\n\n")
                
                for i, classification in enumerate(classifications, 1):
                    category = classification.get('category', 'Unknown')
                    text = classification.get('text', 'N/A')
                    page_number = classification.get('page_number', 'N/A')
                    page_range_cv = classification.get('page_range', None)
                    confidence = classification.get('confidence_score', 'N/A')
                    reason = classification.get('reason', 'N/A')
                    bounding_box = classification.get('bounding_box', [])
                    
                    md_content.append(f"#### Classification {i}\n")
                    md_content.append(f"**Category**: `{category}`\n\n")
                    
                    # Page information (with special handling for CVs)
                    if page_range_cv:
                        md_content.append(f"**Page**: {page_number} (Full range: {page_range_cv})\n\n")
                    else:
                        md_content.append(f"**Page**: {page_number}\n\n")
                    
                    md_content.append(f"**Confidence Score**: {confidence}\n\n")
                    
                    md_content.append(f"**Content**:\n")
                    md_content.append(f"> {text}\n\n")
                    
                    md_content.append(f"**Reason**:\n")
                    md_content.append(f"> {reason}\n\n")
                    
                    if bounding_box:
                        bbox_str = ", ".join(map(str, bounding_box))
                        md_content.append(f"**Bounding Box**: `[{bbox_str}]`\n\n")
                    
                    md_content.append("---\n\n")
            
            md_content.append("\n")
        
        # Summary Statistics
        md_content.append("## 📊 Summary Statistics\n\n")
        
        total_names = sum(len(seg.get('extracted_names', [])) for seg in segments)
        total_classifications = sum(len(seg.get('classifications', [])) for seg in segments)
        
        md_content.append(f"- **Total Names Extracted**: {total_names}\n")
        md_content.append(f"- **Total Classifications**: {total_classifications}\n")
        md_content.append(f"- **Total Segments**: {len(segments)}\n")
        md_content.append(f"- **Total Pages**: {data.get('total_pages', 'Unknown')}\n\n")
        
        # Category breakdown
        category_counts = {}
        for segment in segments:
            for classification in segment.get('classifications', []):
                category = classification.get('category', 'Unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
        
        if category_counts:
            md_content.append("### Classification Breakdown by Category\n\n")
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                md_content.append(f"- **{category}**: {count}\n")
        
        md_content.append("\n---\n\n")
        md_content.append("*Report generated by Azure DI Output Parser (PageNumbers Version)*\n")
        
        # Write to file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(md_content))
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error converting to Markdown: {e}")
        return False


def convert_markdown_to_word(md_filepath, output_filepath):
    """
    Convert a Markdown file to Word document using pandoc.
    
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
        print(f"   ❌ Pandoc not found. Install with: pip install pypandoc")
        print(f"   Or install pandoc directly: https://pandoc.org/installing.html")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def process_all_files(data_path):
    """
    Process all PageNumbers JSON files to create Markdown and Word reports.
    
    Args:
        data_path: Directory containing the JSON files
    """
    # Find all PageNumbers JSON files
    json_files = glob.glob(f"{data_path}*_WORKING_PageNumbers_analysis.json")
    
    if not json_files:
        print(f"❌ No *_WORKING_PageNumbers_analysis.json files found in {data_path}")
        return
    
    # Create output folders
    markdown_folder = os.path.join(data_path, 'markdown_reports_PageNumbers')
    word_folder = os.path.join(data_path, 'word_reports_PageNumbers')
    
    try:
        os.makedirs(markdown_folder, exist_ok=True)
        print(f"✅ Markdown folder: {markdown_folder}")
    except Exception as e:
        print(f"❌ Could not create markdown folder: {e}")
        return
    
    try:
        os.makedirs(word_folder, exist_ok=True)
        print(f"✅ Word folder: {word_folder}")
    except Exception as e:
        print(f"❌ Could not create word folder: {e}")
        return
    
    print("\n" + "="*80)
    print("🚀 CONVERTING PAGENUMBERS JSON TO MARKDOWN AND WORD")
    print("="*80)
    print(f"Input: {data_path}")
    print(f"Markdown Output: {markdown_folder}/")
    print(f"Word Output: {word_folder}/")
    print(f"Found {len(json_files)} JSON files to convert")
    print("="*80 + "\n")
    
    markdown_success = 0
    word_success = 0
    errors = 0
    
    for json_file in sorted(json_files):
        print(f"📄 Processing: {os.path.basename(json_file)}")
        
        try:
            # Create output filenames
            base_name = os.path.basename(json_file).replace('_WORKING_PageNumbers_analysis.json', '')
            md_filename = f"{base_name}_PageNumbers_report.md"
            docx_filename = f"{base_name}_PageNumbers_report.docx"
            
            md_filepath = os.path.join(markdown_folder, md_filename)
            docx_filepath = os.path.join(word_folder, docx_filename)
            
            # Step 1: Convert to Markdown
            print(f"   📝 Converting to Markdown...")
            if convert_json_to_markdown(json_file, md_filepath):
                print(f"   ✅ Markdown created: {md_filename}")
                markdown_success += 1
                
                # Step 2: Convert to Word
                print(f"   📄 Converting to Word...")
                if convert_markdown_to_word(md_filepath, docx_filepath):
                    print(f"   ✅ Word created: {docx_filename}")
                    word_success += 1
                else:
                    print(f"   ⚠️  Word conversion failed")
                    errors += 1
            else:
                print(f"   ❌ Markdown conversion failed")
                errors += 1
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            errors += 1
    
    # Summary
    print("="*80)
    print("🎯 CONVERSION COMPLETE!")
    print("="*80)
    print(f"✅ Markdown files created: {markdown_success}")
    print(f"✅ Word files created: {word_success}")
    if errors > 0:
        print(f"❌ Errors: {errors}")
    print()
    print(f"📁 Markdown reports: {markdown_folder}/")
    print(f"📁 Word reports: {word_folder}/")
    print("="*80)


if __name__ == '__main__':
    # Path to the directory containing JSON files
    data_path = '/Volumes/qa_datascience_convaiqa/volumes/dataanalyticslake_convai/PRISMArchives/PI/'
    
    print("\n" + "="*80)
    print("🚀 PAGENUMBERS JSON TO MARKDOWN & WORD CONVERTER")
    print("="*80)
    print(f"Source: {data_path}")
    print(f"Looking for: *_WORKING_PageNumbers_analysis.json")
    print(f"Output: markdown_reports_PageNumbers/ and word_reports_PageNumbers/ folders")
    print("="*80 + "\n")
    
    process_all_files(data_path)
    
    print("\n✅ All files converted!")
    print("   📝 Markdown files: markdown_reports_PageNumbers/")
    print("   📄 Word files: word_reports_PageNumbers/")
    print("\n💡 Note: Requires pandoc for Word conversion")
    print("   Install: pip install pypandoc")
    print("   Or: https://pandoc.org/installing.html\n")

