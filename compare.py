import argparse
import random
import math
import time
from collections import Counter

from wordle import feedback, load_words, play
from wordle_bot_starter import baseline_guess, my_guess


def worst_feedback_group(guess, candidates):
    # Largest group of possible answers sharing feedback for this guess.
    groups = Counter(feedback(guess, answer) for answer in candidates)
    return max(groups.values())


def benchmark(strategy, answers, words, seed):
    wins = 0
    turns = []
    first_worst = []
    first_observed = []
    first_entropy = []
    for index, answer in enumerate(answers):
        # Each strategy gets the same deterministic random state for this answer.
        # This does NOT guarantee equal guesses, only reproducible runs.
        random.seed(seed + index)
        won, history = play(answer, strategy, words)
        wins += won
        turns.append(len(history) if won else 7)  # 7 = failed within six turns
        first_guess, _, remaining = history[0]
        first_worst.append(worst_feedback_group(first_guess, words))
        first_observed.append(remaining)
        first_entropy.append(guess_entropy(first_guess, words))
    n = len(answers)
    return (wins, sum(turns) / n, max(turns),
            sum(first_worst) / n, sum(first_observed) / n,
            sum(first_entropy) / n)

def guess_entropy(guess, candidates):
    groups = Counter(feedback(guess, answer) for answer in candidates)
    total = len(candidates)
    entropy = 0
    for count in groups.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=20,
                        help='Number of answer words to test (default: 20)')
    parser.add_argument('--seed', type=int, default=112)
    args = parser.parse_args()
    words = load_words()
    if not 1 <= args.limit <= len(words):
        parser.error(f'--limit must be between 1 and {len(words)}')
    # A reproducible spread through the dictionary, not just the first N words.
    answers = random.Random(args.seed).sample(words, args.limit)
    print(f'Testing {len(answers)} identical answers from {len(words)} words; seed={args.seed}')
    print('Average turns counts an unsolved puzzle as 7.')
    print('First worst = largest possible feedback group after opening guess (lower is better).')
    print('First actual = candidates remaining after opening guess on tested answers.')

    print(
        f'{"Strategy":<12} {"Wins":>7} {"Avg turns":>11} '
        f'{"Worst turns":>12} {"First worst":>13} '
        f'{"First actual":>13} {"First entropy":>14} {"Runtime":>10}'
    )

    strategies = [
        ('baseline', baseline_guess),
        ('my_guess', my_guess),
    ]

    for name, strategy in strategies:
        start = time.perf_counter()
        wins, avg, worst, first_worst, first_actual, first_entropy = benchmark(
            strategy, answers, words, args.seed
        )
        elapsed = time.perf_counter() - start
        print(
            f'{name:<12} {wins:>3}/{len(answers):<3} '
            f'{avg:>11.2f} {worst:>12} '
            f'{first_worst:>13.2f} {first_actual:>13.2f} '
            f'{first_entropy:>14.2f}  {elapsed:>8.2f}s'
        )

    print('\nFirst-guess entropy measures information gain; average turns measures the full strategy.')


if __name__ == '__main__':
    main()
