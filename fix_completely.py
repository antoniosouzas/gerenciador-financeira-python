import sys

def main():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find where the CSS starts right after --r: 12px;
    css_start_idx = content.find("@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');")
    
    css_end_idx = content.find(".block-container {")
    
    if css_start_idx != -1 and css_end_idx != -1:
        new_css = """/* ── BASE BACKGROUND & LAYOUT ── */
html, body {
    color: var(--t1);
}

.stApp { background-color: var(--bg) !important; }

footer { visibility: hidden !important; }
.stAppDeployButton { display: none !important; }

"""
        content = content[:css_start_idx] + new_css + content[css_end_idx:]
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    main()
