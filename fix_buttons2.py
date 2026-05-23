import sys

def main():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    old_btn_css = """/* ── BUTTONS ── */
.stButton > button {
    background: transparent !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.9rem !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.2px;
    transition: all 0.2s;
    width: 100%;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    background: rgba(0,212,232,0.1) !important;
    color: var(--cyan) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 12px rgba(0,212,232,0.2) !important;
}
.stButton > button[kind="primary"] {
    background: rgba(0,212,232,0.05) !important;
    color: var(--cyan) !important; font-weight: 700 !important;
    border: 2px solid var(--cyan) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(0,212,232,0.15) !important;
    box-shadow: 0 0 20px rgba(0,212,232,0.4) !important;
    transform: translateY(-1px);
}"""

    new_btn_css = """/* ── BUTTONS ── */
.stButton > button {
    background: #1e2640 !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(0,212,232,0.25) !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.9rem !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.2px;
    transition: all 0.2s;
    width: 100%;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    background: var(--cyan) !important;
    color: #0e1117 !important;
    border-color: transparent !important;
    box-shadow: 0 0 16px rgba(0,212,232,0.3) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3b8beb, #00d4e8) !important;
    color: #0e1117 !important; font-weight: 700 !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 20px rgba(0,212,232,0.4) !important;
    transform: translateY(-1px);
}"""
    
    if old_btn_css in content:
        content = content.replace(old_btn_css, new_btn_css)
    else:
        print("Button CSS not found exactly.")
        
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
