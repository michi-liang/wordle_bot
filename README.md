# Wordle bot

`wordle_bot_starter.my_guess` uses the strategy in `wordle_policy.json`.
The strategy treats every word in `words.txt` as equally likely and allows
any word in that list as a guess, including words ruled out as answers.
It minimizes the average number of guesses among strategies that solve
every answer within six turns.

Run the full benchmark and tests from this directory:

```sh
python compare.py --limit 2315
python -m unittest -v
```

To watch the bot play in the local browser, install `requirements.txt`, run
`python local_server.py`, then run `python wordle_browser.py --answer crane`
in another terminal.

The bot needs only Python. To regenerate the policy, run
`node optimize_wordle.js` with Node.js. This is an offline search; playing
and benchmarking use the saved policy.

The optimizer groups answers by the feedback for each legal guess. Each
guess costs one turn for every possible answer, plus the optimal cost of
solving each nonwinning group with one fewer turn. To skip a guess safely,
the search uses a lower bound: a group of `k` answers needs at least
`2k - 1` more guesses in total, since at most one can be solved on the next
turn. It skips guesses whose lower bound cannot improve the best known cost.

For a custom dictionary, pass `make_guess(words)` to `wordle.play` or
`wordle.evaluate`. When the dictionary does not match the saved policy,
the solver chooses the remaining answer with the highest feedback entropy.
