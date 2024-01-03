# Getting Started
```sh
# To get started you will need a python env. You can use conda to create one. 
conda create -n cdb-test
conda install python

# Install deps 
pip install selenium 
pip install pytest
```

You will also need a chrome driver. This process was automated when running `make test` from $LOGR_ROOT_DIR. 

It is currently broken but a link to one version is hardcoded which may or may not work. This should get fixed in the future. In the meantime if this link needs to be replaced, one can be found on [This Link](https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json). Find one with version closes to output of `google-chrome --version`. The architecture of `linux64`, the filename would end in `linux64/chrome-linux64.zip`.


# Running tests 
A prerequisite to running the test is to run logr application, I recommend running it from netbeans this makes it easier to fix any issues. 

The tests can be run using multiple methods:
- CLI:
```sh
cd $LOGR_ROOT_DIR 
make test
```
- IDE:
Use your favorite IDE such as vscode to open up `$LOGR_ROOT_DIR/tools/developer_tools/portal_testing/PythonSeleniumTest/`. Running the `gui-test.py` would start up the test suite. 
When using this method you may need to run `make test-db` from `$LOGR_ROOT_DIR`. 

Also you may need to add `$LOGR_ROOT_DIR/tools/developer_tools/portal_testing/PythonSeleniumTest/support_bin` to enviornment path.

# Updating test-db for additional sample data
```sh
cd $LOGR_ROOT_DIR
make test-db

# Start up logr portal. 
# Make the changes and add sample data 

make backup
cp $LOGR_INSTALL_DIR/backup/logr/`date +%Y%m%d`/populate* $LOGR_ROOT_DIR/db/sql/test
```



