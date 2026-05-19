"""Tests for the Coder agent."""

from mimo_agents.agents.coder import CoderAgent


def test_extract_code_blocks_single():
    text = '''Here is the code:

```python
# main.py
def hello():
    return "Hello, World!"
```
'''
    blocks = CoderAgent._extract_code_blocks(text)
    assert "main.py" in blocks
    assert 'def hello()' in blocks["main.py"]


def test_extract_code_blocks_multiple():
    text = '''File 1:

```python
# utils.py
def add(a, b):
    return a + b
```

File 2:

```python
# tests.py
def test_add():
    assert add(1, 2) == 3
```
'''
    blocks = CoderAgent._extract_code_blocks(text)
    assert len(blocks) == 2
    assert "utils.py" in blocks
    assert "tests.py" in blocks


def test_extract_code_blocks_no_filename():
    text = '''```python
x = 1
y = 2
```'''
    blocks = CoderAgent._extract_code_blocks(text)
    assert len(blocks) == 0


def test_extract_code_blocks_empty():
    blocks = CoderAgent._extract_code_blocks("No code here")
    assert len(blocks) == 0
