import pytest
import hashlib
# testing functions in ublib.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ublib as ub

print (hash)

def test_add_speech_bubble_static():
    # test if function will work on a static image link
    image_output_path = ub.add_speech_bubble("https://raw.githubusercontent.com/CLAW1200/utilBot/master/tests/test_assets/solid_test_image_JPG_1.jpg", 0.2)
    image = open(image_output_path, "rb").read()
    hash = hashlib.md5(image).hexdigest()
    assert hash == "853833d76f7311e0504e261dbbeff1fa"

if __name__ == "__main__":
    test_add_speech_bubble_static()
    pytest.main()
