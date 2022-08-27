def is_match(pattern, text):
    """Fuzzy search.

    Assumptions:
        pattern is not None
        pattern is lower case
        text is lower case

    Returns:
        indexes (set) of matched indexes
            if pattern is "fuzzy" contained in
            one of the lines of the text
        None otherwise
    """
    for line in text.splitlines():
        indexes = set()
        pattern_index = 0
        for i, letter in enumerate(line):
            if pattern[pattern_index] == letter:
                indexes.add(i)
                pattern_index += 1
                if len(pattern) == pattern_index:
                    return indexes

    return None
