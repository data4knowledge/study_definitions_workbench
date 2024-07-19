import pytest

class KlassA():
  a: str
  b: str
  c: str

class KlassB():
  a: str
  b: KlassA

class KlassC():
  a: str
  b: KlassB

class Wrapper():
  a: str
  b: int
  c: list[KlassA]
  d: KlassC

a1 = KlassA()
a1.a = "Hello Klass A 1"
a1.b = 14
a1.c = "X"
a2 = KlassA()
a2.a = "Hello Klass A 2"
a2.b = 21
a2.c = "Y"
a3 = KlassA()
a3.a = "Hello Klass A 3"
a3.b = 100
a3.c = "Z"
a4 = KlassA()
a4.a = "Hello Klass A 4"
a4.b = 1000
a4.c = "W"
b1 = KlassB()
b1.a = "Klass B"
b1.b = a2
c1 = KlassC
c1.a = "Klass C"
c1.b = b1
wrapper = Wrapper()
wrapper.a = "Wrapper"
wrapper.b = 6543
wrapper.c = [a1, a3, a4]
wrapper.d = c1


x = USDMPath(wrapper)
print("\n\n")
print(f"1: {x.get('b')}\n\n")
print(f"2: {x.get('d/a')}\n\n")
print(f"3: {x.get('c[1]/a')}\n\n")
print(f"4: {x.get('d/b/b/a')}\n\n")
r = x.get("c[@c='W']/a")
print(f"5: {r}\n\n")
