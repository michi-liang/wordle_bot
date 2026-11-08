'use strict';
// The Python game engine is authoritative for solver tests; this local browser
// implementation mirrors its two-pass duplicate-letter feedback rule.
const WORDS = ['crane','slate','trace','stare','cigar','array','allee','apple','level','eerie','belle','sassy','cacao','robot','civic','serve','speed','stone','adieu'];
const params = new URLSearchParams(location.search);
const requested = (params.get('answer') || '').toLowerCase();
const answer = /^[a-z]{5}$/.test(requested) ? requested : WORDS[Math.floor(Math.random()*WORDS.length)];
const board = document.getElementById('board');
const input = document.getElementById('guess-input');
const status = document.getElementById('status');
const history = document.getElementById('history');
let turns = 0;
let finished = false;
for (let i = 0; i < 30; i++) {const tile=document.createElement('div');tile.className='tile';tile.id=`tile-${Math.floor(i/5)}-${i%5}`;board.appendChild(tile);}
function feedback(guess, target) {
  const result=Array(5).fill('-'), counts={};
  for(let i=0;i<5;i++) {if(guess[i]===target[i]) result[i]='G';else counts[target[i]]=(counts[target[i]]||0)+1;}
  for(let i=0;i<5;i++) {if(result[i]!=='G' && (counts[guess[i]]||0)>0){result[i]='Y';counts[guess[i]]--;}}
  return result.join('');
}
document.getElementById('guess-form').addEventListener('submit', e=>{
  e.preventDefault(); if(finished) return;
  const guess=input.value.trim().toLowerCase();
  if(!/^[a-z]{5}$/.test(guess)){status.textContent='Enter exactly five letters.';return;}
  const pattern=feedback(guess,answer);
  for(let i=0;i<5;i++){const tile=document.getElementById(`tile-${turns}-${i}`);tile.textContent=guess[i].toUpperCase();tile.classList.add(pattern[i]==='G'?'green':pattern[i]==='Y'?'yellow':'gray');tile.dataset.feedback=pattern[i];}
  const record=document.createElement('div');record.className='result';record.dataset.guess=guess;record.dataset.pattern=pattern;record.textContent=`${guess.toUpperCase()} : ${pattern}`;history.appendChild(record);
  turns++; input.value='';
  if(guess===answer){finished=true;status.dataset.state='won';status.textContent=`Solved in ${turns} guesses!`;}
  else if(turns===6){finished=true;status.dataset.state='lost';status.textContent=`Out of guesses. Answer: ${answer.toUpperCase()}`;}
  else{status.dataset.state='playing';status.textContent=`${6-turns} guesses left.`;}
  if(finished){input.disabled=true;document.getElementById('submit-guess').disabled=true;}
});
