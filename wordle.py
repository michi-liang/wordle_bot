from collections import Counter
from functools import lru_cache
from pathlib import Path

GREEN, YELLOW, GRAY = 'G', 'Y', '-'


def load_words(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name('words.txt')
    words = []
    for line in path.read_text(encoding='utf-8').splitlines():
        word = line.strip().lower()
        if word and not word.startswith('#'):
            if len(word) != 5 or not word.isascii() or not word.isalpha():
                raise ValueError(f'Invalid five-letter word: {word!r}')
            words.append(word)
    return sorted(set(words))


@lru_cache(maxsize=400000)
def feedback(guess, answer):
    # Return 5-character G/Y/- pattern, correctly accounting for duplicates.
    guess, answer = guess.lower(), answer.lower()
    if len(guess) != 5 or len(answer) != 5:
        raise ValueError('Guess and answer must have five letters')
    result = ['-'] * 5
    remaining = Counter()
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = 'G'
        else:
            remaining[answer[i]] += 1
    for i in range(5):
        if result[i] != 'G' and remaining[guess[i]] > 0:
            result[i] = 'Y'
            remaining[guess[i]] -= 1
    return ''.join(result)


def filter_candidates(candidates, guess, pattern):
    # Retain answers that would produce exactly this feedback.
    if len(pattern) != 5 or any(c not in 'GY-' for c in pattern):
        raise ValueError('Pattern must be five characters from G, Y, -')
    return [word for word in candidates if feedback(guess, word) == pattern]


def play(answer, choose_guess, words=None, max_turns=6):
    # Run a solver; return (won, history). choose_guess(candidates, used).
    words = load_words() if words is None else list(words)
    if answer not in words:
        raise ValueError('Answer must belong to dataset')
    allowed = set(words)
    candidates, used, history = words[:], [], []
    for _ in range(max_turns):
        guess = choose_guess(candidates[:], used[:])
        if guess not in allowed or guess in used:
            raise ValueError(f'Invalid or repeated solver guess: {guess!r}')
        pattern = feedback(guess, answer)
        used.append(guess)
        candidates = filter_candidates(candidates, guess, pattern)
        history.append((guess, pattern, len(candidates)))
        if guess == answer:
            return True, history
    return False, history


def evaluate(choose_guess, words=None, limit=None):
    # Evaluate same deterministic answer set; report failures as 7 turns for averages.
    words = load_words() if words is None else list(words)
    answers = words if limit is None else words[:limit]
    if not answers:
        raise ValueError('No answers to evaluate')
    outcomes = [play(answer, choose_guess, words) for answer in answers]
    wins = sum(won for won, _ in outcomes)
    counts = [len(history) if won else 7 for won, history in outcomes]
    return {'games': len(answers), 'wins': wins, 'win_rate': wins / len(answers),
            'average_turns': sum(counts) / len(counts), 'worst_turns': max(counts)}
