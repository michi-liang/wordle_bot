'use strict';

// Offline exact optimizer. Run with: node optimize_wordle.js
const {readFileSync, writeFileSync} = require('node:fs');
const {createHash} = require('node:crypto');
const {join} = require('node:path');
const words = [...new Set(readFileSync(join(__dirname, 'words.txt'), 'utf8')
  .split(/\r?\n/).map(s => s.trim().toLowerCase())
  .filter(s => s && !s.startsWith('#')))].sort();
if (!words.length || words.some(w => !/^[a-z]{5}$/.test(w))) {
  throw new Error('Expected a list of five-letter words');
}

const n = words.length;
// Encode gray/yellow/green as ternary digits 0/1/2, one byte per pattern.
const ALL_GREEN = 242;
const letters = words.map(w => [...w].map(c => c.charCodeAt(0) - 97));
const counts = new Uint8Array(26);
const powers = [1, 3, 9, 27, 81];
const feedback = letters.map(guess => Uint8Array.from(letters, answer => {
  counts.fill(0);
  let code = 0;
  for (let i = 0; i < 5; i++) {
    if (guess[i] === answer[i]) code += 2 * powers[i];
    else counts[answer[i]]++;
  }
  for (let i = 0; i < 5; i++) {
    if (guess[i] !== answer[i] && counts[guess[i]]) {
      counts[guess[i]]--;
      code += powers[i];
    }
  }
  return code;
}));

const IMPOSSIBLE = Infinity;
const memo = Array.from({length: 7}, () => new Map());
const marks = new Uint32Array(243);
let stamp = 0;

function partition(guess, answers) {
  const buckets = new Map();
  const row = feedback[guess];
  for (const answer of answers) {
    const pattern = row[answer];
    if (pattern === ALL_GREEN) continue;
    let bucket = buckets.get(pattern);
    if (!bucket) buckets.set(pattern, bucket = []);
    bucket.push(answer);
  }
  return [...buckets.values()].sort((a, b) => b.length - a.length);
}

// Each candidate pays one turn now. A non-winning bucket of size k needs
// at least 2k-1 more turns in total: at most one answer can win next turn.
// Score every legal, informative guess by this optimistic total.
function options(answers, depth, limit = IMPOSSIBLE) {
  const size = answers.length;
  const result = [];
  const seen = new Uint32Array(243);
  for (let guess = 0; guess < n; guess++) {
    // Tag counters with the guess index to avoid clearing them each pass.
    const tag = (guess + 1) * (n + 1);
    const row = feedback[guess];
    let groups = 0;
    let largest = 0;
    let hit = 0;
    for (let i = 0; i < size; i++) {
      const pattern = row[answers[i]];
      if (pattern === ALL_GREEN) {
        hit = 1;
        continue;
      }
      let count = seen[pattern] - tag;
      if (count < 0) {
        count = 0;
        groups++;
      }
      seen[pattern] = tag + ++count;
      if (count > largest) largest = count;
    }
    if (largest === size || (depth === 2 && largest > 1)) continue;
    const bound = 3 * size - 2 * hit - groups;
    if (bound < limit) result.push({guess, bound, largest});
  }
  result.sort((a, b) => a.bound - b.bound || a.largest - b.largest || a.guess - b.guess);
  return result;
}

function easyCandidate(answers, depth) {
  // A perfect candidate costs 2k-1. A candidate that leaves just one
  // pair costs 2k, which is optimal if there is no perfect candidate.
  let near = -1;
  for (const guess of answers) {
    stamp++;
    const row = feedback[guess];
    let pair = false;
    let extra = 0;
    for (const answer of answers) {
      const pattern = row[answer];
      if (marks[pattern] === stamp) {
        extra++;
        if (depth < 3 || pair) break;
        pair = true;
      }
      marks[pattern] = stamp;
    }
    if (extra === 0) return {guess, cost: 2 * answers.length - 1};
    if (depth >= 3 && extra === 1) near = guess;
  }
  return near === -1 ? null : {guess: near, cost: 2 * answers.length};
}

function lowerBound(answers) {
  const size = answers.length;
  if (size <= 2) return 2 * size - 1;
  const easy = easyCandidate(answers, 5);
  if (easy) return easy.cost;
  if (size === 3) return 6;

  // The ideal 2k-1 cost cannot occur without a perfect candidate split.
  // Count the best possible split to bound costs for larger buckets.
  let coverage = 0;
  for (let guess = 0; guess < n; guess++) {
    const row = feedback[guess];
    const mark = ++stamp;
    let score = 0;
    for (let i = 0; i < size; i++) {
      const pattern = row[answers[i]];
      if (marks[pattern] === mark) continue;
      marks[pattern] = mark;
      score += pattern === ALL_GREEN ? 2 : 1;
    }
    if (score === size) return 2 * size;
    if (score > coverage) coverage = score;
  }
  return 3 * size - coverage;
}

// For a fixed candidate set and turn budget, minimize the sum of guesses
// over all answers. Winning feedback costs nothing after the current turn.
// An earlier guess is always uninformative in any surviving candidate set,
// so the state does not need to track used guesses.
function solve(answers, depth, limit = IMPOSSIBLE) {
  const size = answers.length;
  if (size === 1) return {cost: 1, guess: answers[0]};
  if (depth === 1) return {cost: IMPOSSIBLE};
  if (size === 2) return {cost: 3, guess: answers[0]};
  if (2 * size - 1 >= limit) return {cost: limit};

  const key = answers.join(',');
  const cache = memo[depth];
  const previous = cache.get(key);
  if (previous && (previous.exact || previous.cost >= limit)) return previous;

  const easy = easyCandidate(answers, depth);
  if (easy) return easy;
  if (size === 3 && depth >= 3) {
    // A probe cannot score below 6, and guessing candidates achieves 6.
    return {cost: 6, guess: answers[0]};
  }

  let best = {cost: limit};
  for (const {guess, bound} of options(answers, depth, limit)) {
    if (bound >= best.cost) break;
    const buckets = partition(guess, answers);
    let cost = bound;
    for (const bucket of buckets) {
      if (bucket.length > 1) {
        const optimistic = 2 * bucket.length - 1;
        cost += solve(bucket, depth - 1, best.cost - cost + optimistic).cost - optimistic;
        if (cost >= best.cost) break;
      }
    }
    if (cost < best.cost) {
      best = {guess, cost};
      if (cost === bound) break;
    }
  }
  // Without a winning guess below the limit, cache only a lower bound.
  best.exact = best.guess !== undefined || limit === IMPOSSIBLE;
  cache.set(key, best);
  return best;
}

const answers = words.map((_, i) => i);
function entropyCost(buckets) {
  return buckets.reduce((sum, bucket) => sum + bucket.length * Math.log2(bucket.length), 0);
}
const openings = options(answers, 6);
for (const option of openings) option.entropyCost = entropyCost(partition(option.guess, answers));
openings.sort((a, b) => a.entropyCost - b.entropyCost || a.guess - b.guess);
let best = {cost: IMPOSSIBLE};
let tested = 0;
for (const {guess, bound} of openings) {
  if (bound >= best.cost) continue;
  const buckets = partition(guess, answers).filter(b => b.length > 1);
  let cost = bound;
  const bounds = [];
  for (const bucket of buckets) {
    if (best.cost === IMPOSSIBLE) {
      bounds.push(2 * bucket.length - 1);
    } else {
      const cached = memo[5].get(bucket.join(','));
      bounds.push(cached?.exact ? cached.cost : Math.max(cached?.cost ?? 0, lowerBound(bucket)));
      cost += bounds.at(-1) - (2 * bucket.length - 1);
      if (cost >= best.cost) break;
    }
  }
  if (cost < best.cost) {
    for (let i = 0; i < buckets.length; i++) {
      const optimistic = bounds[i];
      cost += solve(buckets[i], 5, best.cost - cost + optimistic).cost - optimistic;
      if (cost >= best.cost) break;
    }
  }
  tested++;
  if (cost < best.cost) {
    best = {guess, cost};
    console.log(`Best after ${tested} openings: ${words[guess]} (${cost} turns)`);
  }
  if (tested % 25 === 0) console.log(`Checked ${tested} openings`);
}
if (best.cost === IMPOSSIBLE) throw new Error('No strategy wins within six turns');

const guesses = {};
function record(answers, depth, guess) {
  if (answers.length === 1) return;
  guesses[answers.map(i => words[i]).join(',')] = words[guess];
  for (const bucket of partition(guess, answers)) {
    if (bucket.length > 1) record(bucket, depth - 1, solve(bucket, depth - 1).guess);
  }
}
record(answers, 6, best.guess);
const policy = {
  dictionary_sha256: createHash('sha256').update(words.join('\n')).digest('hex'),
  opening: words[best.guess],
  total_guesses: best.cost,
  guesses,
};
delete guesses[words.join(',')]; // The opening is already stored separately.
writeFileSync(join(__dirname, 'wordle_policy.json'), JSON.stringify(policy, null, 2) + '\n');
console.log(`Optimal: ${policy.opening}, ${best.cost}/${n} = ${(best.cost / n).toFixed(6)} guesses`);
