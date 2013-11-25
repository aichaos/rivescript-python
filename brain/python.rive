// Example of a Python object macro.

! version = 2.0

> object base64 python
    import base64 as b64
    mess = " ".join(args)

    # Make this function work in Python3 as well.
    import sys
    if sys.version_info[0] == 3:
        # Python3's Base64 requires bytes, not a str,
        # so encode the str into bytes.
        mess = mess.encode()
        base = b64.b64encode(mess)

        # Return the base64 result, decoded back into a str.
        return base.decode()
    else:
        # Python2 is simple.
        return b64.b64encode(mess)
< object

> object add python
    # This function returns an int, and shows that the results
    # from python object macros are always casted to str.
    a, b = args
    return int(a) + int(b)
< object

> object setvar python
    # This function demonstrates using rs.current_user() to get
    # the current user ID, to set a variable for them.
    uid   = rs.current_user()
    var   = args[0]
    value = " ".join(args[1:])
    rs.set_uservar(uid, var, value)
< object

+ encode * in base64
- OK: <call>base64 <star></call>

+ what is # plus #
- <star1> + <star2> = <call>add <star1> <star2></call>

+ python set * to *
- Setting user variable <star1> to <star2>.<call>setvar <star1> <star2></call>
