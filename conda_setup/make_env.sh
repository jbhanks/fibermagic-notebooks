#!/usr/bin/bash

python -m venv ~/Venvs/fiber_env

source ~/Venvs/fiber_env/bin/activate

pip install ipykernel

python -m ipykernel install --user --name=fiber_env
