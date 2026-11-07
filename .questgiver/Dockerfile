# The workshop image Questgiver's agents and checks run in. Questgiver's base
# image already carries uv and Python 3.12, which is all this project needs; the
# label tells Questgiver which caches to keep between lanes and checks.
ARG QG_BASE
FROM ${QG_BASE}

LABEL questgiver.caches="/home/agent/.cache/uv"
