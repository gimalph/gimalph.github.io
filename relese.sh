#!/bin/bash

python3 papers.py

docker run --rm -it \
  -v $(pwd):/src \
  -p 1313:1313 \
  klakegg/hugo 

cd public 
git add .