import json
import unittest
from pathlib import Path

from wordle import evaluate, load_words
from wordle_bot_starter import entropy_guess, frequency_guess, make_guess, my_guess


class WordleBotTests(unittest.TestCase):
    def test_policy_solves_every_answer_with_the_reported_cost(self):
        words = load_words()
        policy = json.loads(Path(__file__).with_name('wordle_policy.json')
                            .read_text(encoding='utf-8'))
        self.assertEqual(my_guess(words, []), policy['opening'])
        results = evaluate(my_guess, words)
        self.assertEqual(results['wins'], len(words))
        self.assertLessEqual(results['worst_turns'], 6)
        self.assertEqual(results['average_turns'], policy['total_guesses'] / len(words))

    def test_custom_dictionary_uses_entropy(self):
        words = ['crane', 'crate', 'trace']
        choose_guess = make_guess(words)
        self.assertIs(choose_guess, entropy_guess)
        self.assertEqual(evaluate(choose_guess, words)['wins'], len(words))

    def test_heuristics_skip_used_guesses(self):
        for choose_guess in (frequency_guess, entropy_guess):
            self.assertEqual(choose_guess(['belle', 'eerie'], ['belle']), 'eerie')


if __name__ == '__main__':
    unittest.main()
