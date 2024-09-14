#!/usr/bin/bash

python -m venv ~/Venvs/fiber_env

source ~/Venvs/fiber_env/bin/activate

pip install --user ipykernel

python -m ipykernel install --user --name=fiber_env

pip install google
pip install google-api-core
pip install

#####
mkdir Downloads
cd Downloads
wget https://github.com/conda-forge/miniforge/releases/download/24.3.0-0/Mambaforge-24.3.0-0-Linux-x86_64.sh

bash Mambaforge-*

conda create -n cfiber

# Conda environment created in /home/jam/mambaforge/envs/cfiber/bin/python

conda activate cfiber

conda install ipykernel

python -m ipykernel install --user --name=cfiber

conda install conda-forge::google-colab

conda install conda-forge::google-api-core

conda install conda-forge::google-cloud-sdk

conda install conda-forge::imp


