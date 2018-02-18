from collections import Counter

def partition(predicate, sequence):
    """
    Takes a predicate & a sequence of items, and
    applies the predicate to each of them.

    Returns a tuple with the first item being the
    list of matched items, and the second being
    the list of not matched items.
    """
    match, nomatch = [], []
    for item in sequence:
        if predicate(item):
            match.append(item)
        else:
            nomatch.append(item)
    return match, nomatch


ENGLISH_FREQUENCIES = {
    'E': .1202,
    'T': .0910,
    'A': .0812,
    'O': .0768,
    'I': .0731,
    'N': .0695,
    'S': .0628,
    'R': .0602,
    'H': .0592,
    'D': .0432,
    'L': .0398,
    'U': .0288,
    'C': .0271,
    'M': .0261,
    'F': .0230,
    'Y': .0211,
    'W': .0209,
    'G': .0203,
    'P': .0182,
    'B': .0149,
    'V': .0111,
    'K': .0069,
    'X': .0017,
    'Q': .0011,
    'J': .0010,
    'Z': .0007,
}

PORTUGUESE_FREQUENCIES = {
    'A': .1463,
    'E': .1257,
    'O': .1073,
    'S': .0781,
    'R': .0653,
    'I': .0618,
    'N': .0505,
    'D': .0499,
    'M': .0474,
    'U': .0463,
    'T': .0434,
    'C': .0388,
    'L': .0278,
    'P': .0252,
    'V': .0167,
    'G': .0130,
    'H': .0128,
    'Q': .0120,
    'B': .0104,
    'F': .0102,
    'Z': .0047,
    'J': .0040,
    'X': .0021,
    'K': .0002,
    'W': .0001,
    'Y': .0001,
}

# improving this to ngrams or even markov chains, using some seed text.
def english_probability(text):
    """
    Returns a float representing the likelihood that the given text is a
    plaintext written in English. Range: (0.0 - 1.0), higher is better.
    """
    # Ignore whitespace (revisit this later).
    text = text.upper()
    letters, other = partition(lambda c: c in ENGLISH_FREQUENCIES, text)
    if not letters: return 0.0
    # Expect roughly 15% of text to be spaces.
    spaces, other = partition(lambda c: c.isspace(), other)
    space_error = abs(float(len(spaces))/len(text) - 0.15)
    # As a rough approximation, expect 2% of characters to be punctuation.
    punc_error = abs(float(len(other))/len(text) - 0.02)
    counts = Counter(text)
    letter_error = 0.0
    for c, target_freq in ENGLISH_FREQUENCIES.items():
        letter_error += (target_freq *
                        abs(float(counts.get(c, 0))/len(letters) - target_freq))
    return max(1.0 - (punc_error + letter_error + space_error), 0.0)

# copy from english_probability
def portuguese_probability(text):
    """
    Returns a float representing the likelihood that the given text is a
    plaintext written in Portuguese. Range: (0.0 - 1.0), higher is better.
    """
    text = text.upper()
    letters, other = partition(lambda c: c in PORTUGUESE_FREQUENCIES, text)
    if not letters: return 0.0
    # Expect roughly 15% of text to be spaces.
    spaces, other = partition(lambda c: c.isspace(), other)
    space_error = abs(float(len(spaces))/len(text) - 0.15)
    # As a rough approximation, expect 2% of characters to be punctuation.
    punc_error = abs(float(len(other))/len(text) - 0.02)
    counts = Counter(text)
    letter_error = 0.0
    for c, target_freq in PORTUGUESE_FREQUENCIES.items():
        letter_error += (target_freq *
                        abs(float(counts.get(c, 0))/len(letters) - target_freq))
    return max(1.0 - (punc_error + letter_error + space_error), 0.0)

def hamming_weight(value):
    "Compute the Hamming weight of an integer (number of set bits)."
    # Cheesy but effective.
    return bin(value)[2:].count('1')

def hamming_distance(a, b):
    "Compute the eponymous distance function between the two given byte arrays."
    if len(a) != len(b):
        raise Exception('I thought you could only compare equal lengths.')
    return sum([hamming_weight(ord(x)^ord(y)) for x, y in zip(a, b)])
