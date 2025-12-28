#!/usr/bin/env python3
"""
Flask backend for Victoria House Photos web application.
Extracts addresses from .mhtml filenames and serves them via API.
"""

import os
import re
import json
import email
from email import policy
from flask import Flask, send_file, jsonify, send_from_directory, Response
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Base directory for mhtml files
BASE_DIR = Path(__file__).parent


def extract_address_from_filename(filename):
    """
    Extract address from filename pattern: "For sale_ <address> - <number>"
    Returns the address string or None if pattern doesn't match.
    """
    # Pattern: "For sale_" followed by address until the next " - "
    pattern = r'For sale_\s*(.+?)\s*-\s*\d+'
    match = re.search(pattern, filename)
    if match:
        return match.group(1).strip()
    return None


def scan_mhtml_files():
    """
    Scan the directory for .mhtml files and extract addresses.
    Returns a list of dictionaries with filename and address.
    Returns ALL files, even if addresses are duplicated.
    """
    properties = []
    
    for file_path in BASE_DIR.glob('*.mhtml'):
        filename = file_path.name
        address = extract_address_from_filename(filename)
        
        if address:
            properties.append({
                'filename': filename,
                'address': address,
                'filepath': str(file_path)
            })
    
    return properties


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_file('index.html')


@app.route('/api/properties')
def get_properties():
    """
    API endpoint to get all properties with addresses.
    Returns JSON array of properties.
    """
    properties = scan_mhtml_files()
    return jsonify(properties)


def extract_html_from_mhtml(file_path):
    """
    Extract HTML content from mhtml file and convert embedded resources to data URLs.
    Returns the HTML content as a string with cid: URLs replaced with data URLs, or None if extraction fails.
    """
    try:
        import base64
        
        with open(file_path, 'rb') as f:
            msg = email.message_from_bytes(f.read(), policy=policy.default)
        
        # Store all parts by Content-ID and Content-Location for lookup
        parts_by_cid = {}
        parts_by_location = {}  # Index by Content-Location URL
        html_content = None
        html_charset = 'utf-8'
        
        # First pass: extract all parts
        for part in msg.walk():
            content_id = part.get('Content-ID', '')
            content_location = part.get('Content-Location', '')
            content_type = part.get_content_type()
            
            # Clean Content-ID (remove < >)
            if content_id:
                content_id = content_id.strip('<>')
                parts_by_cid[content_id] = part
                # Also store without cid: prefix if present
                if content_id.startswith('cid:'):
                    parts_by_cid[content_id[4:]] = part
            
            # Index by Content-Location URL (for matching external URLs)
            if content_location:
                # Store full URL
                parts_by_location[content_location] = part
                # Also store URL without query parameters (some URLs have ?v=...)
                if '?' in content_location:
                    base_url = content_location.split('?')[0]
                    parts_by_location[base_url] = part
                # Remove cid: prefix if present and store
                if content_location.startswith('cid:'):
                    loc_key = content_location[4:]
                    parts_by_cid[loc_key] = part
                else:
                    # Also store in cid dict for backward compatibility
                    parts_by_cid[content_location] = part
            
            # Find HTML part
            if content_type == 'text/html' and html_content is None:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    html_charset = charset
                    try:
                        html_content = payload.decode(charset)
                    except UnicodeDecodeError:
                        html_content = payload.decode('utf-8', errors='ignore')
                    
                    # If content still has quoted-printable encoding markers, decode them
                    # The email library should handle this, but sometimes =3D remains
                    import quopri
                    try:
                        # Try to decode any remaining quoted-printable
                        html_content = quopri.decodestring(html_content.encode('utf-8')).decode('utf-8', errors='ignore')
                    except:
                        pass
        
        if not html_content:
            return None
        
        # Clean up any remaining quoted-printable artifacts
        html_content = html_content.replace('=3D', '=').replace('=\n', '')
        
        # Second pass: replace cid: URLs with data URLs or inline content
        import re
        
        def get_part_content(cid):
            """Get content for a Content-ID"""
            # Try exact match first
            if cid in parts_by_cid:
                part = parts_by_cid[cid]
                payload = part.get_payload(decode=True)
                content_type = part.get_content_type()
                return part, payload, content_type
            
            # Try with cid: prefix removed
            if cid.startswith('cid:'):
                cid_clean = cid[4:]
                if cid_clean in parts_by_cid:
                    part = parts_by_cid[cid_clean]
                    payload = part.get_payload(decode=True)
                    content_type = part.get_content_type()
                    return part, payload, content_type
            
            # Try adding cid: prefix
            cid_with_prefix = f'cid:{cid}'
            if cid_with_prefix in parts_by_cid:
                part = parts_by_cid[cid_with_prefix]
                payload = part.get_payload(decode=True)
                content_type = part.get_content_type()
                return part, payload, content_type
            
            return None, None, None
        
        # Collect CSS content to inject
        css_injections = []
        css_cids_processed = set()
        
        def replace_css_link(match):
            """Replace CSS link tag with cid: URL"""
            full_match = match.group(0)
            cid_url = match.group(1)  # Content-ID from href
            
            part, payload, content_type = get_part_content(cid_url)
            if part and payload and content_type == 'text/css':
                if cid_url not in css_cids_processed:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        css_content = payload.decode(charset)
                        css_injections.append(f'<style type="text/css">{css_content}</style>')
                        css_cids_processed.add(cid_url)
                    except Exception as e:
                        print(f"Error decoding CSS for {cid_url}: {e}")
                # Remove the link tag
                return ''
            return full_match
        
        def replace_cid_src(match):
            """Replace cid: URL in src attribute"""
            attr_name = match.group(1)  # src
            cid_url = match.group(2)  # Content-ID
            
            part, payload, content_type = get_part_content(cid_url)
            if part and payload:
                # For images and other resources, use data URL
                base64_data = base64.b64encode(payload).decode('utf-8')
                return f'{attr_name}="data:{content_type};base64,{base64_data}"'
            
            return match.group(0)
        
        def replace_external_url(match):
            """Replace external URL with data URL if it's embedded in mhtml"""
            attr_name = match.group(1)  # src or href
            url = match.group(2)  # External URL
            
            # Check if this URL is embedded in the mhtml file
            part = None
            if url in parts_by_location:
                part = parts_by_location[url]
            elif '?' in url:
                # Try without query parameters
                base_url = url.split('?')[0]
                if base_url in parts_by_location:
                    part = parts_by_location[base_url]
            
            if part:
                payload = part.get_payload(decode=True)
                content_type = part.get_content_type()
                if payload:
                    base64_data = base64.b64encode(payload).decode('utf-8')
                    return f'{attr_name}="data:{content_type};base64,{base64_data}"'
            
            # Not found in mhtml, return original URL
            return match.group(0)
        
        # Replace CSS link tags with cid: URLs (handle quoted-printable encoding =3D)
        # Pattern matches: href="cid:..." or href=3D"cid:..." (quoted-printable)
        html_content = re.sub(
            r'<link[^>]*href=3?D?["\']cid:([^"\']+)["\'][^>]*>',
            replace_css_link,
            html_content,
            flags=re.IGNORECASE
        )
        
        # Replace cid: URLs in img src and other src attributes
        # Handle both normal and quoted-printable encoded (=3D)
        html_content = re.sub(
            r'(src)=3?D?["\']cid:([^"\']+)["\']',
            replace_cid_src,
            html_content,
            flags=re.IGNORECASE
        )
        
        # Replace external image URLs that are embedded in mhtml (by Content-Location)
        # Match src="https://..." URLs
        html_content = re.sub(
            r'(src)=3?D?["\'](https?://[^"\']+)["\']',
            replace_external_url,
            html_content,
            flags=re.IGNORECASE
        )
        
        # Also handle background-image in style attributes
        def replace_cid_in_style(match):
            style_content = match.group(1)
            # Find cid: URLs in style content
            def replace_style_cid(m):
                cid_url = m.group(1)
                part, payload, content_type = get_part_content(cid_url)
                if part and payload:
                    base64_data = base64.b64encode(payload).decode('utf-8')
                    return f'url(data:{content_type};base64,{base64_data})'
                return m.group(0)
            
            style_content = re.sub(
                r'url\(cid:([^)]+)\)',
                replace_style_cid,
                style_content,
                flags=re.IGNORECASE
            )
            return f'style="{style_content}"'
        
        html_content = re.sub(
            r'style=3?D?["\']([^"\']*cid:[^"\']*)["\']',
            replace_cid_in_style,
            html_content,
            flags=re.IGNORECASE
        )
        
        # Inject all CSS before </head>
        if css_injections:
            html_content = html_content.replace('</head>', '\n'.join(css_injections) + '\n</head>', 1)
        
        return html_content
    except Exception as e:
        import traceback
        print(f"Error extracting HTML from mhtml: {e}")
        traceback.print_exc()
        return None


@app.route('/mhtml/<path:filename>')
def serve_mhtml(filename):
    """
    Serve mhtml files by extracting HTML content.
    Chrome doesn't support mhtml files served via HTTP, so we extract and serve the HTML.
    """
    try:
        file_path = os.path.join(BASE_DIR, filename)
        # Security check: ensure file is in base directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(BASE_DIR)):
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Extract HTML content from mhtml file
        html_content = extract_html_from_mhtml(file_path)
        
        if html_content:
            # Serve the extracted HTML content
            return Response(
                html_content,
                mimetype='text/html; charset=utf-8',
                headers={
                    'Content-Type': 'text/html; charset=utf-8',
                    'Content-Disposition': 'inline',
                    'X-Content-Type-Options': 'nosniff',
                    'Cache-Control': 'no-cache'
                }
            )
        else:
            # Fallback: try to serve raw mhtml (may prompt download)
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Try to extract boundary for proper Content-Type
            content_str = content[:2000].decode('utf-8', errors='ignore')
            boundary = None
            import re
            for line in content_str.split('\n'):
                if 'boundary=' in line.lower():
                    match = re.search(r'boundary=["\']?([^"\'\s;]+)', line, re.IGNORECASE)
                    if match:
                        boundary = match.group(1)
                        break
            
            content_type = f'multipart/related; boundary="{boundary}"' if boundary else 'multipart/related'
            
            return Response(
                content,
                mimetype=content_type,
                headers={
                    'Content-Type': content_type,
                    'Content-Disposition': 'inline',
                    'X-Content-Type-Options': 'nosniff'
                }
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

