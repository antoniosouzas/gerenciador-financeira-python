import sys

def main():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue: the title is cut off at the top. This is because we set:
    # .block-container { padding: 1.5rem 2rem 2rem 2rem !important; }
    # but Streamlit's new versions sometimes need margin-top or we might have hidden the header in a way that shifts content up under the hidden header.
    # We also need to restore default header behavior to let the sidebar button work organically.
    
    old_css = """footer { visibility: hidden !important; }
[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }

/* Garante que o botão de expandir a sidebar sempre apareça */
[data-testid="collapsedControl"] { 
    display: flex !important; 
    z-index: 999999 !important; 
    color: var(--cyan) !important;
    background: var(--card) !important;
    border-radius: 50% !important;
    border: 1px solid var(--cyan) !important;
    box-shadow: 0 0 10px rgba(0,212,232,0.2) !important;
}
.block-container { 
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 100% !important;
}"""

    # We will remove all the hacky CSS we tried for the header and toolbar.
    # We will just hide the footer and the deploy button (stAppDeployButton).
    # And we'll increase the top padding of block-container so the title doesn't get cut off.
    
    new_css = """footer { visibility: hidden !important; }
.stAppDeployButton { display: none !important; }
[data-testid="stToolbar"] { visibility: hidden !important; }

.block-container { 
    padding-top: 4rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}"""
    
    content = content.replace(old_css, new_css)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
