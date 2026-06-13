# Prompts

Every human prompt used across Claude Code sessions in this repository, in chronological order — the full build history of DensityGen as a sequence of instructions. Exported from the local Claude Code session transcripts.

**9 prompts across 2 sessions** (the two sessions ran concurrently on 2026-06-13: one built the screening engine + deploys, the other integrated the visualization).


---

## Session 1 — 2026-06-13 20:58 UTC

`76787893-f4ba-4c3f-a1ca-07643b3d863a` · 8 prompts


### 1.1 — 2026-06-13 20:58 UTC

~~~text
build the end to end tool for  the chemists; propose some sample ueries regarding possible questions they might have for their ald or surface chem questions especially things that are unknown or require a lot of super computing queries normally that new ai models exist for more rapid screening, then standup the best models to do this on replicate. use the known recipes i.e. wf6 -> w as the test cases, and have it work to help chemists determine which precursors to prioritize for new materials for ald
~~~


### 1.2 — 2026-06-13 21:12 UTC

~~~text
can you not put the weights on the gpu image on replicate? say more about the test case, how did it decide which precursors to even run precursor discovery on? does it work? find the most important groups of ~10 lines of code and tell me what it is so i can analyze it
~~~


### 1.3 — 2026-06-13 21:15 UTC

~~~text
can we get uma to actually run? so do both of these: (a) build the actual discovery/inverse-design loop, (b) wire the ASE structure bridge so --uma computes real energies, and make sure we can do this too: True discovery (the model proposing novel precursors you didn't list) is query #13 in SAMPLE_QUERIES.md — inverse design over ligand space — and is not implemented. It would be a generative loop wrapped around the cheap UMA evaluations.
~~~


### 1.4 — 2026-06-13 21:38 UTC

~~~text
ok so then deploy the website for me that people can try, and give a little modal that explains the importance succinctly (discovering the core materials needed for the enxt generation of semiconductors, the last time thishappened and when usa won, and the mb china race, and why this problem is important
~~~


### 1.5 — 2026-06-13 21:48 UTC

~~~text
deploy to fly io, and commit all of this directly to main
~~~


### 1.6 — 2026-06-13 22:02 UTC

~~~text
explain more about what our specific Discovery tool adds on top of uma -- do we automate precursor selection? if so, why do we Ask the user to input them? What even is a co-reactant? Can we just have that select the best one by default? What happened to the nice chemical rendering that was in the imported zip file? Can you make sure to add that to this repo and ensure that that's shown for our final results?
~~~


### 1.7 — 2026-06-13 22:38 UTC

~~~text
commit to github
~~~


### 1.8 — 2026-06-13 22:46 UTC

~~~text
ok and Export all of the prompts that I use in all of the Claude Code sessions in this repository into a prompts.md and note it in the readme
~~~


---

## Session 2 — 2026-06-13 21:26 UTC

`95fc5097-62c1-4ce4-bf65-cef12b67941b` · 1 prompts


### 2.1 — 2026-06-13 21:26 UTC

~~~text
i have soe visualizatio code at hackathonfable-opus-shack-june13-2026-20260613T212412Z-3-001  in downloads, Integrate that with the pipeline I have here so that the results we have are interpretable and viewable and also scan it for bugs and make sure to fix any especially in the connection between our caluclations and its display. include an input field with some suggestios for people to suggest new precursors
~~~
