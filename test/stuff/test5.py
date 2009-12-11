class A:
	def foo(self, x):
		y = x + 1
		print(y)
		return y

	@staticmethod
	def zar():
		print("l o l")

class B(A):
	def bar(self, x):
		y = self.foo(x) + 3
		print(y)
		return y

class C():
	def foo(self, x):
		y = x - 1
		print(y)
		return y

a = C()
A.foo(a, 5)

B.zar()
