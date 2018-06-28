pycodestyle --config=.pycodestyle $1
pylint --rcfile=".pylintrc" --output-format=parseable $1

