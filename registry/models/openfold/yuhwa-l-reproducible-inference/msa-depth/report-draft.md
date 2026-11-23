# Assignment 5: Research Proof of Concept
## How much does OpenFold depend on its multiple sequence alignment?

**GitHub (experiment branch):** https://github.com/Yuhwa-L/cybershuttle-ai4science-foundry/tree/openfold-msa-depth/registry/models/openfold/yuhwa-l-reproducible-inference/msa-depth
**CyberShuttle contribution (PR #41):** https://github.com/cyber-shuttle/cybershuttle-ai4science-foundry/pull/41
**Presentation (unlisted YouTube):** YOUTUBE_LINK

## 1. Research objective

My CyberShuttle contribution is a reproducible OpenFold inference recipe on PACE/ICE for six proteins (159–1,125 residues), with baseline time, GPU memory, and accuracy measurements. OpenFold, like AlphaFold2, uses two kinds of input besides the sequence: a multiple sequence alignment (MSA) of related sequences from other organisms, and templates (known structures of similar proteins). Building the MSA is by far the most expensive step of the workflow: 2–6 hours of CPU time per protein in my recipe, compared with 6–350 seconds for the prediction itself.

**Question:** how much prediction accuracy is lost as the MSA shrinks, down to the single input sequence, when everything else stays the same? And does OpenFold's own confidence (pLDDT) notice the loss?

**Why it is useful:**
- If a few dozen sequences are enough, a much cheaper alignment search could be used.
- Proteins with few known relatives (orphan or newly discovered proteins) are exactly where MSA-based models are expected to fail. Measuring this failure motivates combining OpenFold with MSA-free protein language models such as ESM2/ESMFold, which are already in the Foundry.

**Approach:** cut the precomputed alignments of five proteins to the first 1, 8, 32, and 128 sequences, rerun OpenFold with everything else unchanged, and score each prediction against the experimental structure.

**Anticipated challenges:** OpenFold pads every input to 512 MSA rows in prediction mode, so the cut has to be done on the alignment files themselves; templates are a second information source that can hide the effect of the MSA (6KWC has near-identical templates); and limited GPU time on the shared `coc-gpu` partition.

## 2. Implementation

All new code is in the experiment branch (link above):

| File | What it does |
|---|---|
| `scripts/cut_msa.py` | Copies a precomputed alignment folder and keeps only the first N sequences of each MSA file (`bfd_uniref_hits.a3m`, `uniref90_hits.sto`, `mgnify_hits.sto`), query included. Template hits (`hhsearch_output.hhr`) are copied unchanged, so only the MSA changes. N = 1 is single-sequence input. |
| `scripts/run_msa_depth.sh` | For each protein and each N in 1, 8, 32, 128, cuts the alignments and runs the recipe's existing `measure_inference.py` (same model, seed, and template date cutoff as the baseline). |
| `scripts/summarize_msa_depth.py` | Joins all runs with the committed full-MSA baseline into `summary.md`, `summary.csv`, and the plot `msa_depth.png`. |

The experiment reuses the CyberShuttle recipe's environment, alignments, accuracy metrics (`structure_metrics.py`: TM-score, C-alpha lDDT, C-alpha RMSD), and baseline results unchanged. The full-MSA control is the committed baseline from job 6886502.

## 3. Environment and procedure

- **Cluster:** Georgia Tech PACE/ICE, `coc-gpu` partition, one NVIDIA L40S 46 GB (job 7247593; an A100 was requested but not assigned before the deadline). Baseline: NVIDIA A100-PCIE-40GB.
- **Software:** OpenFold commit `be2ec18`, PyTorch 2.5.1 / CUDA 12.4, `model_1_ptm` AlphaFold parameters, environment from the recipe's `environment.yml`.
- **Steps** (after the recipe's setup, sections 1 and 2.1):

```bash
salloc --account=coc --partition=coc-gpu --gres=gpu:l40s:1 --cpus-per-task=8 --mem=64G --time=02:00:00
cd "$RECIPE"
./scripts/run_msa_depth.sh 9OUF_A 6KWC_1 9Q5U_A 9NXH_A 9LB7_A > msa-depth/run.log 2>&1
python scripts/summarize_msa_depth.py
```

8P5S (1,125 residues) was left out because of time: about 6 minutes per forward pass.

## 4. Experimental evidence

All 20 runs (5 proteins x 4 depths) finished with status `ok`; "full" is the committed A100 baseline.

| Protein | Residues | MSA depth | Time (s) | Mean pLDDT | pTM | TM-score | lDDT | RMSD (Å) |
|---|---|---|---|---|---|---|---|---|
| 9OUF_A | 159 | 1 | 23.4 | 77.8 | 0.71 | 0.87 | 0.83 | 6.18 |
| 9OUF_A | 159 | 8 | 8.8 | 86.9 | 0.79 | 0.92 | 0.89 | 3.59 |
| 9OUF_A | 159 | 32 | 8.9 | 89.9 | 0.80 | 0.95 | 0.94 | 3.16 |
| 9OUF_A | 159 | 128 | 8.8 | 90.4 | 0.81 | 0.95 | 0.94 | 3.16 |
| 9OUF_A | 159 | full | 6.1 | 87.5 | 0.77 | 0.95 | 0.92 | 2.98 |
| 6KWC_1 | 191 | 1 | 11.7 | 96.6 | 0.92 | 0.99 | 0.98 | 1.00 |
| 6KWC_1 | 191 | 8 | 11.5 | 97.4 | 0.93 | 0.99 | 0.98 | 0.94 |
| 6KWC_1 | 191 | 32 | 11.7 | 97.8 | 0.93 | 0.99 | 0.98 | 0.95 |
| 6KWC_1 | 191 | 128 | 11.5 | 97.4 | 0.93 | 0.99 | 0.98 | 0.96 |
| 6KWC_1 | 191 | full | 7.8 | 97.7 | 0.93 | 0.99 | 0.98 | 0.96 |
| 9Q5U_A | 325 | 1 | 27.0 | 34.9 | 0.31 | 0.32 | 0.29 | 19.64 |
| 9Q5U_A | 325 | 8 | 27.0 | 72.1 | 0.72 | 0.77 | 0.75 | 4.23 |
| 9Q5U_A | 325 | 32 | 27.0 | 86.4 | 0.83 | 0.86 | 0.84 | 2.94 |
| 9Q5U_A | 325 | 128 | 27.0 | 88.7 | 0.86 | 0.93 | 0.87 | 2.11 |
| 9Q5U_A | 325 | full | 18.8 | 91.7 | 0.88 | 0.88 | 0.87 | 2.67 |
| 9NXH_A | 500 | 1 | 60.3 | 70.8 | 0.68 | 0.70 | 0.72 | 16.08 |
| 9NXH_A | 500 | 8 | 60.3 | 73.3 | 0.69 | 0.70 | 0.78 | 17.25 |
| 9NXH_A | 500 | 32 | 61.0 | 90.5 | 0.71 | 0.71 | 0.94 | 14.51 |
| 9NXH_A | 500 | 128 | 60.3 | 91.5 | 0.70 | 0.72 | 0.94 | 11.24 |
| 9NXH_A | 500 | full | 39.8 | 91.5 | 0.69 | 0.72 | 0.94 | 12.85 |
| 9LB7_A | 777 | 1 | 160.9 | 91.6 | 0.93 | 0.98 | 0.92 | 1.58 |
| 9LB7_A | 777 | 8 | 160.0 | 94.5 | 0.94 | 0.98 | 0.96 | 1.38 |
| 9LB7_A | 777 | 32 | 160.3 | 95.7 | 0.94 | 0.99 | 0.97 | 1.34 |
| 9LB7_A | 777 | 128 | 160.0 | 95.5 | 0.94 | 0.99 | 0.97 | 1.05 |
| 9LB7_A | 777 | full | 110.2 | 95.7 | 0.94 | 0.99 | 0.97 | 1.12 |

Best template found by the template search (`hhsearch_output.hhr`, top hit), which explains most of the pattern:

| Protein | Best template | Probability | Aligned length |
|---|---|---|---|
| 6KWC_1 | 2DFB_A, xylanase | 100% | 189 of 191 residues |
| 9LB7_A | 4KTP_A, glycoside hydrolase | 100% | 730 of 777 residues |
| 9NXH_A | 3AKH_A, alpha-L-arabinofuranosidase | 100% | 318 of 500 residues (one domain) |
| 9OUF_A | 3GC6_A, ecto-NAD+ glycohydrolase | 99.6% | 122 of 159 residues |
| 9Q5U_A | 1V8H_A, SoxZ protein | 33.5% | 45 of 325 residues (no real template) |


Figure: `msa-depth/msa_depth.png` (TM-score and pLDDT against MSA depth, one line per protein).

Log: `msa-depth/run-7247593.log`. Per-run predictions, superposed structures, and `result.json` files: `msa-depth/results/depth-<N>/<protein>/`.

## 5. Observations and next steps

- **Without a good template, the MSA is essential.** 9Q5U, the only protein with no real template, collapses with the single sequence (TM-score 0.32, RMSD 19.6 Å: the wrong fold) and recovers step by step as sequences are added (0.77 at 8, 0.86 at 32, 0.93 at 128).
- **With a full-length template, the MSA hardly matters.** 6KWC (TM-score 0.99 at every depth) and 9LB7 (0.98 with the single sequence) are predicted almost as well from the sequence alone.
- **Partial templates need a modest MSA.** 9OUF (template covers 77% of the chain) reaches its full accuracy at 32 sequences. For 9NXH, the template covers one domain; the per-domain accuracy (lDDT) needs 32 sequences to reach 0.94, and the whole-chain TM-score stays near 0.72 at every depth because the relative placement of the two domains is never recovered.
- **Confidence tracks accuracy.** Mean pLDDT falls with accuracy (9Q5U: 35 at depth 1, 72 at depth 8), so OpenFold flags its own failures here.
- **Depth does not change speed.** Each protein's time is the same at every depth, because OpenFold pads the MSA to a fixed size in prediction mode. On the L40S, single passes without warm-up were about 1.4–1.5 times slower than the A100 baseline.
- 9Q5U at depth 128 scored higher than with the full MSA (TM-score 0.93 compared with 0.88). This is one run per setting; OpenFold samples MSA rows at random (fixed seed), so a single comparison between close values is not conclusive.

**What I learned:** OpenFold's dependence on the MSA is not a property of protein length but of how much other information is available. When a close template exists, a single sequence is nearly enough, so the hours-long alignment search could be skipped or shortened; when no template exists (9Q5U), the alignment is the main source of structural information and a few dozen sequences recover most of the accuracy. pLDDT reliably flagged the failures, which makes a cheap first pass with a shallow MSA plus a confidence check a practical workflow.

**Unresolved:** one run per setting (no repeats with different seeds); only five proteins, with only one that lacks a template; templates were not turned off, so their contribution is inferred from the template search output rather than measured directly.

**Next steps:**
1. Replace the MSA with a protein language model: run ESMFold (built on ESM2, already in the Foundry) on the same proteins and compare with OpenFold at depth 1 and at full depth.
2. Separate the two information sources: repeat the sweep with templates turned off, to see how much of the accuracy at low depth comes from templates.
3. Extend to 8P5S and to the planned 40-protein set, and test smarter subsampling (for example most diverse sequences rather than the top hits).
4. Repeat each setting with several seeds to measure run-to-run spread.
5. Use the result for the optimization project: if accuracy holds at moderate depth, a faster alignment search is a larger end-to-end speed-up than any GPU-side change.
