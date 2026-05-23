import sys

def main():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Sometimes setting the .stApp background blocks the header if the header is transparent.
    # Let's add explicit CSS to ensure the collapsed sidebar button is visible and on top.
    
    old_css = """[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }"""

    new_css = """[data-testid="stToolbar"] { visibility: hidden !important; }
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
}"""
    
    content = content.replace(old_css, new_css)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
