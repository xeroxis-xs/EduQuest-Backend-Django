def split_full_name(full_name):
    """
    Splits a full name into first and last names.
    Assumes last name is the last word.
    """
    parts = full_name.strip().split()

    if len(parts) == 1:
        first_name = parts[0]
        last_name = ""
    elif len(parts) > 1:
        last_name = parts[-1]
        first_name = " ".join(parts[:-1])
    else:
        first_name = ""
        last_name = ""

    return first_name, last_name
