def split(text:str,before:str,after:str) -> str|None:
    try:
        return text.split(before)[1].split(after)[0]
    except IndexError:
        return