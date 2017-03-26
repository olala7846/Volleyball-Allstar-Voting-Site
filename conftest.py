import sys
import os

# Set GOOGLE_CLoud_Sdk_PATH to your sdk
SDK_PATH = os.environ['GOOGLE_CLOUD_SDK_PATH']

# add GAE library for testing
sys.path.insert(1, SDK_PATH + 'platform/google_appengine')
sys.path.insert(1, SDK_PATH + 'platform/google_appengine/lib/yaml/lib')
sys.path.insert(1, SDK_PATH + 'platform/google_appengine/lib/protorpc-1.0')
