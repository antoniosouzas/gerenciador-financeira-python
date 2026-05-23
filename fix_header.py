import sys

def main():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue is likely that making the header background transparent or hiding parts of it
    # made the button invisible or Streamlit's new version handles it differently.
    # Let's revert header hiding completely and only hide the deploy button, the hamburger menu and the footer.
    
    old_css = """footer { visibility: hidden !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stHeader"] .stAppDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }"""

    # We will hide:
    # - footer (bottom watermark)
    # - The hamburger menu at the top right: [data-testid="stToolbar"]
    # We will NOT touch the header background or visibility, which contains the sidebar toggle button
    new_css = """footer { visibility: hidden !important; }
[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }"""
    
    content = content.replace(old_css, new_css)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
