from flask import escape


def html_escape(text):
    if not text:
        return text
    return escape(text)


def split_escaped_text(line):
    res = []

    escaped_opened = False
    for c in line:
        if escaped_opened:
            res[-1] += c
            if c == ";":
                escaped_opened = False
        else:
            res.append(c)
            if c == "&":
                escaped_opened = True

    return res
