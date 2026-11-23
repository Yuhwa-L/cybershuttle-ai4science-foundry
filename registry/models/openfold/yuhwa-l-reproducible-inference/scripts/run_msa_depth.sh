#!/bin/bash
# MSA-depth experiment: rerun OpenFold with only the first N sequences of each
# alignment file, everything else as in the baseline (README section 7).
# Run on a GPU node from the recipe directory:
#   ./scripts/run_msa_depth.sh 9OUF_A 6KWC_1 9Q5U_A 9NXH_A
# Depths default to "1 8 32 128" (set DEPTHS to change). Results go to
# msa-depth/results/depth-<N>/; the full-MSA control is results/measurements/.
set -eo pipefail
cd "$(dirname "$0")/.."
export CONDA_ENVS_PATH="${CONDA_ENVS_PATH:-$HOME/scratch/.conda/envs}"
command -v conda >/dev/null 2>&1 || module load miniforge
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${OPENFOLD_ENV:-openfold-env}"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-$HOME/scratch/.triton-cache}"
DEPTHS="${DEPTHS:-1 8 32 128}"

echo "Date: $(date -Is)  Job: ${SLURM_JOB_ID:-none}  Node: $(hostname)"
nvidia-smi --query-gpu=name,memory.total --format=csv

for target in "$@"; do
  if [[ $target == 6KWC_1 ]]; then
    fasta=inputs/6KWC.fasta; src=alignments/6KWC_1; ref=reference/6KWC.pdb; released=2021-01-27
  else
    id=${target%_A}
    fasta=length-series/inputs/$target.fasta; src=length-series/alignments/$target
    ref=length-series/reference/$id.cif
    released=$(awk -F'\t' -v id="$id" '$1==id {print $4}' length-series/targets.tsv)
  fi
  for n in $DEPTHS; do
    python scripts/cut_msa.py "$src" "msa-depth/alignments-$n/$target" "$n"
    python scripts/measure_inference.py --fasta "$fasta" \
      --alignment-dir "msa-depth/alignments-$n" --reference "$ref" --reference-chain A \
      --max-template-date "$(date -d "$released -1 day" +%F)" \
      --warmup 0 --repeats 1 --output-dir "msa-depth/results/depth-$n" || echo "FAILED: $target depth $n"
  done
done
