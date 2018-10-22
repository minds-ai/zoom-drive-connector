#!/usr/bin/env bash

#######################################
# Runs pycodestyle and pylint against a
# specified file.
# Globals:
#   None
# Arguments:
#   file_name: name of file to run checks
#              on.
# Returns:
#   None
#######################################
check_file () {
  # Function arguments.
  local file_name="$1"

  echo "File: $file_name"
  echo "PYCODESTYLE:"
  pycodestyle --config=.pycodestyle "$file_name"

  echo "PYLINT:"
  pylint --rcfile=".pylintrc" --output-format=parseable "$file_name"

  echo "MYPY:"
  mypy --ignore-missing-imports "$file_name"  
}

#######################################
# Gets an array of files in the given
# directory and in all subdirectories
# and runs check_file against them.
# Globals:
#   None
# Arguments:
#   folder: name of folder to check files
#           in.
# Returns:
#   None
#######################################
check_files_in_dir () {
  # Function arguments.
  local folder="$1"

  # Get array of files.
  IFS=" " read -ra PY_FILES <<< "$(find "$folder" -type f -iname "*.py" -exec echo {} +)"

  # Run checks against all files in array.
  for file in "${PY_FILES[@]}"; do
    check_file "$file"
  done
 }

if [[ $# -lt 1 ]]; then
  # If no argument is provided then check all files in all directories.
  check_files_in_dir .
else
  if [[ -f $1 ]]; then
    # Check specific file.
    check_file "$1"
  else
    # Check specific folder.
    check_files_in_dir "$1"
  fi
fi
