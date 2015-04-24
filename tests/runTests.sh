#!/bin/sh

TEST_DIR=$(dirname $0)
BASE_DIR=$(readlink -f "$TEST_DIR/..")

PYTHONPATH="$BASE_DIR:$TEST_DIR/xbmcstubs"

cd $(dirname $0)

MODULES=""
for test in $(find -name "*Test.py"); do
    MODULE=$(basename ${test} | sed 's/\.py$//g')
    MODULES="$MODULES $MODULE"
done

python -m unittest $@ ${MODULES}