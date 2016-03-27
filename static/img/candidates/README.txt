Candidate image name is the md8 hash of chinese Candidate name

Example:
``` python
import hashlib

img_name = hashlib.md5('巫仰哲').hexdigest()
# image_name == 'd4361d848be50549a274d235b0774acf'
```

the image of 巫仰哲 should be at
static/img/candidate/d4361d848be50549a274d235b0774acf.jpg
