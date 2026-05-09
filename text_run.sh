#!/bin/bash
#SBATCH --partition=cpu-48h
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=t.ranasinghe@lancaster.ac.uk

pip install -q huggingface_hub pytesseract pdf2image tqdm
apt-get -qq install poppler-utils tesseract-ocr tesseract-ocr-sin

export HF_HOME=/mnt/nfs/homes/ranasint/hf_home
huggingface-cli login --token

python -m pdf_to_text



