# This is needed for ty. See https://github.com/astral-sh/ty/issues/2384 and https://github.com/astral-sh/ty/issues/2068.
export VIRTUAL_ENV=venv
PATH=$(pwd)/venv/Scripts:$PATH
export PATH
export BETTY_TEST_SKIP_ESLINT=true
export BETTY_TEST_SKIP_PLAYWRIGHT=true
export BETTY_TEST_SKIP_STYLELINT=true
export BETTY_TEST_SKIP_TSC=true
export BETTY_TEST_SKIP_WEBPACK_ENTRY_POINT_PROVIDER=true
