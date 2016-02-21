# NTU Volley Allstar Voting Site
Python GAE voting webapp
To start your own GAE project, please reference https://github.com/olala7846/GAE-template

## Requirements
1. Python 2.7, Pypi, virtualenv
2. Bower


## Setup
1. install python packages under virtual environment
  `virtualenv venv`
  `source venv/bin/activate` or `source vb`
  `pip install -r packages.txt`

## API server
1. we use Google Cloud Endpoint as BE server, it comes with
  a free API explorer at `/_ah/api/explorer`
2. but you cannot test explorer on dev server
   reference [Google Developer](https://developers.google.com/explorer-help/#hitting_local_api) So I cerated a convenient script under `/script/open_chrome.sh`
3. launch insecure chrome to test api explorer `sh ./script/open_chrome.sh`