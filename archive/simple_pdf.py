#!/usr/bin/env python3
"""
Simple PDF Generator - Paste data, get PDF, opens in Chrome
"""

import requests
import json
import subprocess
import sys
import re

# API Configuration
API_KEY = "1aa8NDg0MDM6NDU2MzE6RnI0YTZVaUFiVVQ4TlVhTQ="
API_ENDPOINT = "https://rest.apitemplate.io/v2/create-pdf-from-html"


def format_data_as_html(data_text):
    """Convert pasted text data into clean HTML table"""
    
    lines = [line.rstrip() for line in data_text.strip().split('\n')]
    html_parts = []
    
    i = 0
    in_initial_info = False
    in_values_table = False
    
    # Process lines
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Detect Initial Policy Information section
        if 'Initial Policy Information' in line:
            html_parts.append('<div class="section">')
            html_parts.append('<h2>Initial Policy Information</h2>')
            in_initial_info = True
            i += 1
            continue
        
        # Detect Values section
        if 'Policy Year' in line and 'Age' in line and 'Premium Outlay' in line:
            if in_initial_info:
                html_parts.append('</div>')
                in_initial_info = False
            
            html_parts.append('<div class="section">')
            html_parts.append('<h2>Policy Values</h2>')
            
            # Parse header row - split by tabs or multiple spaces
            headers = re.split(r'\t+|\s{2,}', line)
            headers = [h.strip() for h in headers if h.strip()]
            
            html_parts.append('<table class="data-table">')
            html_parts.append('<thead><tr>')
            for header in headers:
                html_parts.append(f'<th>{header}</th>')
            html_parts.append('</tr></thead><tbody>')
            in_values_table = True
            i += 1
            continue
        
        # Process Initial Policy Information table
        if in_initial_info:
            # Check if next line starts Values section
            if i + 1 < len(lines) and 'Policy Year' in lines[i + 1]:
                html_parts.append('</div>')  # Close policy-info if open
                html_parts.append('</div>')  # Close section
                in_initial_info = False
                continue
            
            # Check if this is a table row (has tabs or multiple spaces)
            if '\t' in line or re.search(r'\s{2,}', line):
                parts = re.split(r'\t+|\s{2,}', line)
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) >= 2:
                    # Format as key-value pairs
                    if not html_parts or not html_parts[-1].startswith('<div class="policy-info">'):
                        if html_parts and html_parts[-1] != '</div>':
                            html_parts.append('<div class="policy-info">')
                        elif not html_parts:
                            html_parts.append('<div class="policy-info">')
                    html_parts.append('<div class="info-item">')
                    html_parts.append(f'<strong>{parts[0]}</strong>')
                    html_parts.append(f'<span>{" ".join(parts[1:])}</span>')
                    html_parts.append('</div>')
            else:
                # Regular text line - close policy-info first if open
                if html_parts and html_parts[-1].endswith('</div>') and html_parts[-2].endswith('</div>'):
                    html_parts.append('</div>')  # Close policy-info
                html_parts.append(f'<div class="info"><p>{line}</p></div>')
            i += 1
            continue
        
        # Process Values table rows
        if in_values_table:
            # Check if line starts with a number (policy year)
            if re.match(r'^\d+', line):
                # Split by tabs or multiple spaces
                cells = re.split(r'\t+|\s{2,}', line)
                cells = [c.strip() for c in cells if c.strip()]
                if len(cells) >= 6:  # Valid data row
                    html_parts.append('<tr>')
                    for cell in cells:
                        html_parts.append(f'<td>{cell}</td>')
                    html_parts.append('</tr>')
            elif line and 'Policy Year' not in line:
                # End of table, add any remaining info
                html_parts.append('</tbody></table></div>')
                in_values_table = False
                if line and not line.startswith('This information'):
                    html_parts.append(f'<div class="info"><p>{line}</p></div>')
            i += 1
            continue
        
        # Other lines (headers, info, etc.)
        if line and not in_initial_info and not in_values_table:
            if 'Display Information' in line or 'View Option' in line:
                html_parts.append(f'<div class="section"><h2>{line}</h2></div>')
            else:
                html_parts.append(f'<div class="info"><p>{line}</p></div>')
        i += 1
    
    # Close any open sections
    if in_initial_info:
        if html_parts and html_parts[-1].endswith('</div>'):
            html_parts.append('</div>')  # Close policy-info
        html_parts.append('</div>')  # Close section
    if in_values_table:
        html_parts.append('</tbody></table></div>')
    
    # Build complete HTML
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 40px;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin: 30px 0 15px 0;
            font-size: 1.5em;
        }}
        .section {{
            margin: 30px 0;
        }}
        .info {{
            background: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
        }}
        .info p {{
            margin: 0;
            color: #555;
        }}
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        table.data-table thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        table.data-table th {{
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #ddd;
        }}
        table.data-table td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        table.data-table tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        table.data-table tbody tr:hover {{
            background-color: #e8f4f8;
        }}
        .policy-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #3498db;
        }}
        .info-item strong {{
            display: block;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .info-item span {{
            color: #555;
            font-size: 1.1em;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Policy Illustration</h1>
        {''.join(html_parts)}
    </div>
</body>
</html>
"""
    return html_content


def generate_pdf(html_content):
    """Generate PDF from HTML using APITemplate.io"""
    
    payload = {
        "body": html_content,
        "css": "",
        "data": {},
        "settings": {
            "paper_size": "A4",
            "orientation": "1",  # Portrait
            "margin_top": "20",
            "margin_right": "20",
            "margin_bottom": "20",
            "margin_left": "20",
            "print_background": "1"
        }
    }
    
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("Generating PDF...")
    response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=100)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            download_url = result.get("download_url")
            print(f"✓ PDF generated successfully!")
            print(f"  URL: {download_url}")
            return download_url
        else:
            raise Exception(f"API error: {result.get('message', 'Unknown error')}")
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")


def open_in_chrome(url):
    """Open URL in Chrome browser"""
    try:
        # Try different Chrome paths on Mac
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium'
        ]
        
        for chrome_path in chrome_paths:
            try:
                subprocess.Popen([chrome_path, url])
                print(f"✓ Opened in Chrome")
                return True
            except FileNotFoundError:
                continue
        
        # Fallback: use open command (default browser)
        subprocess.Popen(['open', url])
        print(f"✓ Opened in default browser")
        return True
    except Exception as e:
        print(f"⚠ Could not open browser automatically: {e}")
        print(f"  Please open this URL manually: {url}")
        return False


def main():
    print("=" * 60)
    print("Simple PDF Generator")
    print("=" * 60)
    print("\nPaste your data below (press Ctrl+D or Ctrl+Z then Enter when done):\n")
    
    # Read input from stdin
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    if not lines:
        print("No data provided!")
        return
    
    data_text = '\n'.join(lines)
    
    # Format as HTML
    print("\nFormatting data...")
    html_content = format_data_as_html(data_text)
    
    # Generate PDF
    try:
        download_url = generate_pdf(html_content)
        
        # Open in Chrome
        open_in_chrome(download_url)
        
        print("\n✓ Done!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
