#!/bin/sh

PYTHONPATH=$(dirname $0) python -c 'from simuleds.loader import main ; main()'
