# Quick Start Guide

## ✅ Setup Complete!

Your Mac already has everything needed:
- ✅ Python 3.14.3 installed
- ✅ `requests` library installed
- ✅ `tkinter` GUI library available

## 🚀 Run the GUI Application

Simply double-click `pdf_generator.py` or run in Terminal:

```bash
cd /Users/dunham/Desktop/python
python3 pdf_generator.py
```

## 📝 How to Use

1. **Paste your HTML** into the large text box at the top
2. **Add CSS** (optional) in the middle box if you have custom styles
3. **Add JSON data** (optional) in the bottom box if your HTML uses Jinja2 variables like `{{website}}`
4. **Click "Generate PDF"**
5. **Choose where to save** the PDF file

## 🧪 Test It Out

Try pasting this HTML:

```html
<h1 style="text-align: center; color: #4CAF50;">Hello World!</h1>
<p>This is a test PDF generated from HTML.</p>
<table border="1" style="width: 100%;">
    <tr>
        <th>Name</th>
        <th>Value</th>
    </tr>
    <tr>
        <td>Test</td>
        <td>123</td>
    </tr>
</table>
```

Or use the example files:
- `example.html` - Sample HTML template
- `example_data.json` - Sample JSON data for Jinja2 variables

## 💻 Command Line Alternative

If you prefer command line:

```bash
python3 pdf_generator_cli.py example.html output.pdf
```

## 📋 Your API Details

- **Template ID**: `58777b23c9701b0e`
- **API Key**: Already configured in the scripts
- **Endpoint**: `https://rest.apitemplate.io/v2/create-pdf-from-html`

## 🎯 Next Steps

1. Run `python3 pdf_generator.py`
2. Paste your HTML content
3. Generate your PDF!

That's it! You're ready to generate PDFs. 🎉
