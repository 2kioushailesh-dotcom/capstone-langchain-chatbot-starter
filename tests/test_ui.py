import os

def test_index_template_exists():
    path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
    assert os.path.exists(path), f"Missing template: {path}"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'SageBot' in content or 'SageBot' in content, 'Expected SageBot title in index.html'

def test_static_files_exist():
    root = os.path.join(os.path.dirname(__file__), '..')
    assert os.path.exists(os.path.join(root, 'static', 'style.css'))
    assert os.path.exists(os.path.join(root, 'static', 'main.js'))
