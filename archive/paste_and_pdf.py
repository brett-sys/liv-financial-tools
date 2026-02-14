#!/usr/bin/env python3
"""
Simple Paste & PDF Generator
Paste your data, click Generate, PDF opens in Chrome
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import subprocess
import re

# API Configuration
API_KEY = "1aa8NDg0MDM6NDU2MzE6RnI0YTZVaUFiVVQ4TlVhTQ="
API_ENDPOINT = "https://rest.apitemplate.io/v2/create-pdf-from-html"


def parse_data_to_html(data_text):
    """Parse pasted data and convert to formatted HTML - optimized for consistent format"""
    lines = [line.rstrip() for line in data_text.strip().split('\n')]
    html_parts = []
    
    i = 0
    in_values_table = False
    headers = []
    
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        
        # Detect Values table header - look for "Policy Year" and "Age" together
        if 'Policy Year' in line and 'Age' in line:
            if in_values_table:
                html_parts.append('</tbody></table></div>')
            
            html_parts.append('<div class="section"><h2>Policy Values</h2>')
            html_parts.append('<table class="data-table"><thead><tr>')
            
            # Parse headers - prioritize tabs, fallback to 2+ spaces
            if '\t' in line:
                headers = [h.strip() for h in line.split('\t') if h.strip()]
            else:
                headers = re.split(r'\s{2,}', line)
                headers = [h.strip() for h in headers if h.strip()]
            
            for h in headers:
                html_parts.append(f'<th>{h}</th>')
            
            html_parts.append('</tr></thead><tbody>')
            in_values_table = True
            i += 1
            continue
        
        # Process data rows in values table
        if in_values_table:
            # Check if line starts with a number (policy year)
            stripped = line.strip()
            if re.match(r'^\d+', stripped):
                # Parse cells - prioritize tabs, fallback to 2+ spaces
                if '\t' in line:
                    cells = [c.strip() for c in line.split('\t') if c.strip()]
                else:
                    cells = re.split(r'\s{2,}', line)
                    cells = [c.strip() for c in cells if c.strip()]
                
                # Ensure we have the right number of cells
                if len(cells) >= len(headers):
                    html_parts.append('<tr>')
                    for cell in cells[:len(headers)]:
                        # Right-align numeric columns (except first two)
                        if cell and (cell.startswith('$') or cell.endswith('%') or re.match(r'^\d+', cell)):
                            html_parts.append(f'<td class="num">{cell}</td>')
                        else:
                            html_parts.append(f'<td>{cell}</td>')
                    html_parts.append('</tr>')
            else:
                # End of table - close it
                html_parts.append('</tbody></table></div>')
                in_values_table = False
                # Process this line as regular content
                if line.strip() and 'Policy Year' not in line:
                    html_parts.append(f'<p class="note">{line}</p>')
            i += 1
            continue
        
        # Process Initial Policy Information section
        if 'Initial Policy Information' in line:
            html_parts.append('<div class="section"><h2>Initial Policy Information</h2>')
            html_parts.append('<div class="info-grid">')
            i += 1
            # Process next lines as info items until we hit Values section
            while i < len(lines):
                info_line = lines[i].strip()
                if not info_line:
                    i += 1
                    continue
                if 'Policy Year' in info_line:
                    html_parts.append('</div></div>')
                    break
                # Parse tab or space-separated key-value pairs
                if '\t' in info_line:
                    parts = [p.strip() for p in info_line.split('\t') if p.strip()]
                else:
                    parts = re.split(r'\s{2,}', info_line)
                    parts = [p.strip() for p in parts if p.strip()]
                
                if len(parts) >= 2:
                    html_parts.append('<div class="info-item">')
                    html_parts.append(f'<strong>{parts[0]}</strong>')
                    html_parts.append(f'<span>{" ".join(parts[1:])}</span>')
                    html_parts.append('</div>')
                else:
                    html_parts.append(f'<p>{info_line}</p>')
                i += 1
            continue
        
        # Other headers
        if 'Display Information' in line:
            html_parts.append(f'<div class="section"><h2>{line}</h2></div>')
        elif line.strip():
            html_parts.append(f'<p>{line}</p>')
        i += 1
    
    # Close any open table
    if in_values_table:
        html_parts.append('</tbody></table></div>')
    
    return ''.join(html_parts)


def generate_pdf_html(html_body):
    """Create complete HTML document"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 40px;
            color: #333;
            line-height: 1.6;
        }}
        .section {{
            margin: 30px 0;
            page-break-inside: avoid;
        }}
        h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.85em;
        }}
        table.data-table thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        table.data-table th {{
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #ddd;
        }}
        table.data-table td {{
            padding: 10px 8px;
            border: 1px solid #ddd;
        }}
        table.data-table td.num {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        table.data-table tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        table.data-table tbody tr:hover {{
            background-color: #e8f4f8;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 5px;
            border-left: 3px solid #3498db;
        }}
        .info-item strong {{
            display: block;
            color: #2c3e50;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}
        .info-item span {{
            color: #555;
            font-size: 1.1em;
            font-weight: 500;
        }}
        p {{
            margin: 10px 0;
        }}
        p.note {{
            color: #666;
            font-style: italic;
            font-size: 0.9em;
            margin-top: 15px;
        }}
        @media print {{
            body {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""


def generate_pdf(html_content):
    """Generate PDF using API"""
    payload = {
        "body": html_content,
        "css": "",
        "data": {},
        "settings": {
            "paper_size": "A4",
            "orientation": "1",
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
    
    response = requests.post(API_ENDPOINT, json=payload, headers=headers, timeout=100)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            return result.get("download_url")
        else:
            raise Exception(f"API error: {result.get('message', 'Unknown error')}")
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")


def open_chrome(url):
    """Open URL in Chrome"""
    try:
        subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', url])
        return True
    except:
        try:
            subprocess.Popen(['open', '-a', 'Google Chrome', url])
            return True
        except:
            subprocess.Popen(['open', url])
            return False


class SimplePDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Generator")
        self.root.geometry("900x700")
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
        
        # Text area - fills most of window
        self.text_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("Courier", 11),
            padx=15,
            pady=15,
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.text_area.focus()
        
        # Button at bottom
        self.generate_btn = tk.Button(
            root,
            text="Generate PDF",
            command=self.generate,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=40,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.generate_btn.pack(fill=tk.X, side=tk.BOTTOM)
    
    def generate(self):
        data = self.text_area.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please paste some data first!")
            return
        
        self.generate_btn.config(state=tk.DISABLED, text="Generating...")
        self.root.update()
        
        try:
            # Parse and format HTML
            html_body = parse_data_to_html(data)
            html_content = generate_pdf_html(html_body)
            
            # Generate PDF
            url = generate_pdf(html_content)
            
            # Open in Chrome
            open_chrome(url)
            
            messagebox.showinfo("Success", "PDF generated and opened in Chrome!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")
        finally:
            self.generate_btn.config(state=tk.NORMAL, text="Generate PDF")


def main():
    root = tk.Tk()
    app = SimplePDFApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
