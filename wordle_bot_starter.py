import json
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from math import log2
from pathlib import Path

from wordle import feedback, load_words


def baseline_guess(candidates, used):
    # Working baseline: choose the alphabetically first remaining answer.
    for word in candidates:
        if word not in used:
            return word

def frequency_guess(candidates, used):
    """Favor guesses covering letters shared by many possible answers."""
    frequencies = Counter(letter for word in candidates for letter in set(word))
    return max(sorted(set(candidates) - set(used)),
               key=lambda word: sum(frequencies[letter] for letter in set(word)))

def entropy_guess(candidates, used):
    """Choose the remaining answer with the highest feedback entropy."""
    answers = tuple(sorted(candidates))
    return _entropy_guess(answers, tuple(sorted(set(used).intersection(answers))))


@lru_cache(maxsize=256)
def _entropy_guess(answers, used):
    choices = tuple(word for word in answers if word not in used)
    if len(choices) == 1:
        return choices[0]
    weights = [0] + [count * log2(count) for count in range(1, len(answers) + 1)]

    def cost(guess):
        groups = Counter(feedback(guess, answer) for answer in answers)
        # Minimizing sum(k log2 k) is equivalent to maximizing entropy.
        return sum(weights[count] for count in sorted(groups.values()))

    return min(choices, key=cost)


def make_guess(words=None):
    """Build a solver for the supplied dictionary (default: words.txt)."""
    dictionary = tuple(load_words()) if words is None else tuple(sorted(set(words)))
    policy_path = Path(__file__).with_name('wordle_policy.json')
    if not policy_path.is_file():
        return entropy_guess
    policy = json.loads(policy_path.read_text(encoding='utf-8'))
    fingerprint = sha256('\n'.join(dictionary).encode('utf-8')).hexdigest()
    if fingerprint != policy['dictionary_sha256']:
        return entropy_guess

    def choose_guess(candidates, used):
        if len(candidates) == 1 and candidates[0] not in used:
            return candidates[0]
        answers = tuple(sorted(candidates))
        if not used and answers == dictionary:
            return policy['opening']
        guess = policy['guesses'].get(','.join(answers))
        if guess is not None and guess not in used:
            return guess
        return entropy_guess(candidates, used)

    return choose_guess


@lru_cache(maxsize=1)
def _default_strategy():
    return make_guess()

def my_guess(candidates, used):
    """Play the bundled dictionary using its precomputed optimal policy."""
    return _default_strategy()(candidates, used)
