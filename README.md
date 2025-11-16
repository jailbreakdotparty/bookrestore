# bookrestore
patched in iOS 26.2 beta 2 (23C5033h)

**what is this?** arbitrary file overwrite exploit for iOS versions lower than 26.2 beta 2 (23C5033h)

**how does it work?** path escape involving some database files. this is mainly supposed to be just some exploit code, you can read a decent writeup on the vulnerability [here](https://hanakim3945.github.io/posts/download28_sbx_escape/).

**how do i use this?** clone this repo, and run `bookrestore.py`. enter the destination path and your input data and do what it says.

# credits
- [Skadz](https://github.com/skadz108) for developing this exploit tool
- [Duy Tran](https://github.com/khanhduytran0) for the initial PoC code
- [hanakim3945](https://github.com/hanakim3945) for publishing the first public writeup which this exploit is based off
- exploit initially used in some iCloud bypass tools, actively sold and utilized in-the-wild
