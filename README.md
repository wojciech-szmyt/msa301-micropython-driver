# msa301-micropython-driver
Homebrew micropython driver for msa301 3-axis accelerometer. Tested on Raspberry Pico.
All functionality described in the msa301 datasheet is implemented (https://download.kamami.pl/p585252-MSA301.pdf)

As a starting point, I used a simple 3-axis accelerometer driver "MicroPython LIS2HH12 driver, Copyright (c) 2017-2018 Mika Tuupola" (MIT License) and built-up from there.

I am a physicist, not a professional programmer. This is my first driver, so there might be some bugs! My goal was to program the driver so that it is as memory-efficient and computation-efficient as I can make it, while retaining all the functionality of the msa301 device. there surely can be some improvements to be made, which would be most welcome! The msa301 has a lot of functionality with plenty of settings for various types of motion interrupts etc. If you are sure you are not going to use some of the functionality, you can delete specific dictionaries, functions, properties and addresses to save memory.

The files include:
- msa301.py - the main driver lib to import
- msa301extras.py - some extra functionality, such as flash-stored software calibration and automatic calibration function
- test.py - the script that presents all functionality and discusses each one in detail in the comments

I would like to highlight the auto-calibration function. It relies on detection of acceleration at 4 orientations. The acceleration vectors point at vertices of a tetrahedron. Since only 1 sphere crosses all tetrahedron vertices, we can find a center of the sphere and this center is the offset to be corrected for. Moreover, the uncertainty of the calibration is estimated and a score is given as a feedback. The score corresponds to the cutoff-fraction of all ranked possible orientations, where the best case is a regular tetrahedron. For example, a score of 0.21 means that your chosen 4 orientations are at 21% of all possible orientations ranked from best to worst in terms of how much they magnify the calibration uncertainty. A factor of by how much the calibration uncertainty is magnified due to the chosen orientations is calculated. I performed monte-carlo simulations and fit a curve to the data of culminative probability of normalized calibration uncertainty given completely random orientations of the accelerometer. The function is:
CulminProb = Score = 2/(1/uQ+uQ)
where uQ is the uncertainty of the calibration normalized by the uncertainty of acceleration measurement. The function fits very well to the data, so I used it to give the score in terms of culminative probability. There might be a mathematical proof of it, but I have not found it nor could I obtain it. It surely works though.
