import pytest
from app.model.unified_diff.unified_diff import UnifiedDiff, Hunk, LineRange

def test_line_range():
  lr = LineRange('12', '2')
  assert lr.line == 12
  assert lr.count == 2

def test_line_range_error_1():
  lr = LineRange('12', '2x')
  assert lr.line == 12
  assert lr.count == 1

def test_line_range_error_2():
  lr = LineRange('', '')
  assert lr.line == 1
  assert lr.count == 1

def test_hunk():
  data = [
    ("@@ -1,9 +1,9 @@", 1, 9, 1 ,9),
    ("@@ -0,0 +1,27 @@", 0, 0, 1, 27),
    ("@@ -32,6 +32,7 @@", 32, 6, 32, 7), 
    ("@@ -454,6 +454,11 @@ Some text", 454, 6, 454, 11),
    ("@@ -18, +18, @@", 18, 1, 18, 1),
  ]
  for item in data:
    hunk = Hunk(item[0])
    assert hunk.old.line == item[1]
    assert hunk.old.count == item[2]
    assert hunk.new.line == item[3]
    assert hunk.new.count == item[4]

def test_hunk_error(caplog):
  hunk = Hunk("@@ 1,xxx 1,9 @@")
  assert hunk.old == None
  assert hunk.new == None
  assert error_logged(caplog, "Failed to decode hunk header '@@ 1,xxx 1,9 @@'")

def test_unified_diff_1(caplog):
  old_lines = [
    'line 1',
    'line 2',
    'line 3',
    'line 4',
    'line 5',
    'line 6',
    'line 7',
    'line 8',
    'line 9',
    'line 10',
  ]
  new_lines = [
    'line 1',
    'line 2 plus',
    'line 3',
    'line 4',
    'line 5',
    'line 6',
    'line 8',
    'line 9',
    'line 10',
    'New line 11'
  ]
  ud = UnifiedDiff(old_lines, new_lines)
  assert len(caplog.records) == 0
  assert len(ud._hunks) == 1
  #assert ud.to_html() == "xxx"
  print(f"HTML: {ud.to_html()}")

def error_logged(caplog, text):
  correct_level = caplog.records[-1].levelname == "ERROR"
  return text in caplog.records[-1].message and correct_level

