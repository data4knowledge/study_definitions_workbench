import pytest
from model.object_path import ObjectPath

class KlassA():
  a_a: str
  a_b: str
  a_c: str

class KlassB():
  b_a: str
  b_b: KlassA

class KlassC():
  c_a: str
  c_b: KlassB

class Root():
  r_a: str
  r_b: int
  r_c: list[KlassA]
  r_d: KlassC

a1 = KlassA()
a1.a_a = "Hello Klass A 1"
a1.a_b = 14
a1.a_c = "X"
a2 = KlassA()
a2.a_a = "Hello Klass A 2"
a2.a_b = 21
a2.a_c = "Y"
a3 = KlassA()
a3.a_a = "Hello Klass A 3"
a3.a_b = 100
a3.a_c = "Z"
a4 = KlassA()
a4.a_a = "Hello Klass A 4"
a4.a_b = 1000
a4.a_c = "W"
b1 = KlassB()
b1.b_a = "Klass B"
b1.b_b = a2
c1 = KlassC
c1.c_a = "Klass C"
c1.c_b = b1
root = Root()
root.r_a = "root"
root.r_b = 6543
root.r_c = [a1, a3, a4]
root.r_d = c1

def test_1():
  x = ObjectPath(root)
  assert x.get('r_b') == 6543

def test_2():
  x = ObjectPath(root)
  assert x.get('r_d/c_a') == "Klass C"

def test_3():
  x = ObjectPath(root)
  assert x.get('r_c[1]/a_a') == "Hello Klass A 3"

def test_4():
  x = ObjectPath(root)
  assert x.get('r_d/c_b/b_b/a_a') == "Hello Klass A 2"

def test_5():
  x = ObjectPath(root)
  assert x.get("r_c[@a_c='W']/a_b") == 1000

