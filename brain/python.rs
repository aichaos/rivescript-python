// Example of a Python object macro.

! version = 2.0

> object base64 python
	import base64 as b64
	return b64.b64encode(" ".join(args))
< object

+ encode * in base64
- OK: <call>base64 <star></call>
