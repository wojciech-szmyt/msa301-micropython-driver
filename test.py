"""
This is an example script showing all the implemented properties and functions of the driver.
All of the aspects of the MSA301 described in the datasheet are implemented.
In the comments there are instructions on using of each function.
More information is also in the comments within the msa301.py driver file.
Refer to the MSA301 datasheet for more information.

"""

from machine import I2C, Pin
import msa301, utime
# for extra functionalities:
import msa301extras


######################
### BASIC FUNCTION ###
######################

# Initialize the I2C according to the GPIO pins
# that you connect your MSA301 to your microcontroller
# 400kHz is the maximum I2C frequency of MSA301
i2c = I2C(0,scl=Pin(1), sda=Pin(0),freq=400000)

# Create the sensor object and initialize
# Name it as you like, in this example it is "sensor"
sensor = msa301.MSA301(i2c) # initialization with default parameters
sensor.powerMode = 'Normal' # factory default is 'Suspnd', which does not give an acceleration reading
print(sensor.acceleration)  # acceleration is a tuple of (a_x, a_y, a_z)

"""
During the initialization you can optionally give any number of keyword parameters that correspond
to properties of MSA301 in order to quickly initialize the sensor in one line. Follow the syntax:
"""
#sensor = msa301.MSA301(i2c, property1 = value1, property2 = value2, ...)
"""
Properties can also be set after the initialization like this:
"""
#sensor.property = value
"""
Properties can be later accessed like this:
"""
#retrievedProperty = sensor.property
"""
The MSA301 object has several multi-argument functions that take any number of keyword arguments.
The functions follow the syntax: 
"""
#sensor.configFunctionName(keyword1 = value1, keyword2 = value2, ...)
"""
If no arguments are given, the function returns an object with attributes
currently set on MSA301 corresponding to the keywords:
"""
#retrievedState = sensor.configFunctionName()
#print('keyword1 currently set on MSA301 is',retrievedState.keyword1)

"""
>>> ALL PROPERTIES AND FUNCTIONS ARE LISTED BELOW
>>> EXAMPLE USAGE FURTHER BELOW

####################################################################
List of read/write properties, their allowed values and description:
####################################################################

‣ units            : 'G' (acceleration given in g's) or 'SI' (acceleration given in m/s^2)
‣ sampleAveraging  : positive integers corresponding to the number of samples to average to get 1 output
‣ resolution       : 8, 10, 12, 14 - measurement resolution in bits
‣ range            : 2, 4, 8, 16 - range of sensor in g's, e.g. range=2 means sensor range ±2g
‣ outputDataRate   : 1, 2, 4, ... , 1024 - powers of 2 correspond to miliseconds of output data rate
‣ powerMode        : 'Normal', 'LowPwr', 'Suspnd' - self-explanatory. WARNING: factory setting of MSA301 is Suspnd!
‣ outputDataRateLP : 2, 4, 8, ... , 512 - powers of 2 correspond to miliseconds of output data rate at low power
‣ intLatchConfig   : 'NoLatch', '250ms', '500ms', '1s', '2s', '4s', '8s', 'Latch','1ms', '2ms', '25ms',
                     '50ms', '100ms' - sets latching, no latching or temporaty latching of the interrupts
‣ fallDuration     : 0<=fallDuration<514 - duration of freefall detection in miliseconds
‣ fallThreshold    : 0<=fallThreshold<2000 fall threshold in mili-g's
‣ fallMode         : 'SumMode', 'SingleMode' - sets freefall detection mode
‣ fallHyst         : 0, 125, 250, 375 - freefall hysteresis, multiple of 125 given in mili-g's
‣ activeDur        : 1, 2, 3, 4 - duration of activity detection given in miliseconds
‣ activeThr        : 0<=activeThr<0.5, corresponding to the fraction of the set range
                     (e.g. ) activeThr=0.25 at a range=2 means active threshold equal 0.5g
‣ tapQuietDur      : 20, 30 - duration of tap quiet in miliseconds (see: MSA301 manual)
‣ tapShockDur      : 70, 50 - duration of tap shock in miliseconds (see: MSA301 manual)
‣ tapDur           : 50, 100, 150, 200, 250, 375, 500, 700 - duration of tap detection in ms
‣ tapThr           : 0<=tapThr<1 - tap threshold corresponding to the fraction of the set range
‣ orientHyst       : 0<=orientHyst<500 - orientation hysteresis in mili=g's
‣ zBlockMode       : 'NoBlock', 'ZaxBlock', 'ZaxSlopeBlock' - z-block mode (see: MSA301 manual)
‣ orientMode       : 'Symmetric', 'HSymmetric', 'LSymmetric' - orientation detection mode (see: MSA301 manual)
‣ zBlockThreshold  : 0<=zBlockThreshold<1000 - z-block threshold in mili-g's (see: MSA301 manual)

##################################################
List of read-only properties and their description
##################################################

‣ acceleration      : value of acceleration, according to the units defined with .units property
‣ motionInterrupts  : returns an object with information about the current state of interrupts (see: example below)
‣ tapActivityStatus : as above, for tap activity status
‣ orientationStatus : as above, for orientation status
‣ newDataReady      : returns boolean, to be used if newDataIntEnable=True, otherwise always gives False
‣ whoAmI            : returns a value of Part ID (for MSA301 it should be equal 0x13)

#######################################
Multi-parameter configuration functions
#######################################

‣ axesConfig()         : configuration of reversing axes, swapping x-y axes and disabling individual axes.
‣ interruptConfig()    : to turn individual interrupts on/off
‣ mapInterruptsToPin() : to map individual interrupts to the hardware interrupt pin
‣ intPinConfig()       : setup of behavior of the interrupt pin: open-drain or push-pull, high/low when active
‣ offsetCalibration()  : setup of offsets of individual axes

"""


#Optional configurtation of the hardware interrupt pin.
#Set it according to your GPIO pin number.
#Essential for asynchronous handling of interrupts.

sensorIntPin = Pin(2, mode=Pin.IN, pull=Pin.PULL_UP)

######################################
### ACCESSING READ-ONLY PROPERTIES ###
######################################

# Check if the PART_ID is correct (should be 0x13)
print("msa301 id: " + hex(sensor.whoAmI))

# Getting the acceleration reading as a tuple (a_x, a_y, a_z)
print(sensor.acceleration)

# Accessing the current state of interrupts (boolean True or False)
"""
The functions below will always give all "False" if interrupts
are not configured. The lines below show the syntax
for accessing the interrupts, but for proper use
configure the interrupts first using the property
"interruptsEnable" described below in this file
"""
print('Orientation change interrupt is active:',sensor.motionInterrupts.orientIntStatus)
print('Single tap interrupt is active:',        sensor.motionInterrupts.singleTapIntStatus)
print('Double tap interrupt is active:',        sensor.motionInterrupts.doubleTapIntStatus)
print('Activity interrupt is active:',          sensor.motionInterrupts.activeIntStatus)
print('Freefall interrupt is active:',          sensor.motionInterrupts.fallIntStatus)
"""
With the approach above, interrupts status is checked on the MSA301 with every call.
If multiple interrupts are to be checked, it is more efficient to store
the motion interrupts status in an object and check.
"""
motionInterruptStatus = sensor.motionInterrupts
print('Orientation change interrupt is active:',motionInterruptStatus.orientIntStatus)
print('Single tap interrupt is active:',        motionInterruptStatus.singleTapIntStatus)
print('Double tap interrupt is active:',        motionInterruptStatus.doubleTapIntStatus)
print('Activity interrupt is active:',          motionInterruptStatus.activeIntStatus)
print('Freefall interrupt is active:',          motionInterruptStatus.fallIntStatus)

# Accessing the details of tap and activity interrupt (boolean True or False)
print('The sign of tap trigger was negative:',      sensor.tapActivityStatus.tapSign)
print('Tap interrupt was triggered by x axis:',     sensor.tapActivityStatus.tapFirstX)
print('Tap interrupt was triggered by y axis:',     sensor.tapActivityStatus.tapFirstY)
print('Tap interrupt was triggered by z axis:',     sensor.tapActivityStatus.tapFirstZ)
print('The sign of activity trigger was negative:', sensor.tapActivityStatus.activeSign)
print('Activity interrupt was triggered by x axis:',sensor.tapActivityStatus.activeFirstX)
print('Activity interrupt was triggered by y axis:',sensor.tapActivityStatus.activeFirstY)
print('Activity interrupt was triggered by z axis:',sensor.tapActivityStatus.activeFirstZ)
"""
The tap activity status can be stored in a variable analogously as motion interrupts above
"""
tapActivityStatus = sensor.tapActivityStatus
print('The sign of tap trigger was negative:',      tapActivityStatus.tapSign)
print('Tap interrupt was triggered by x axis:',     tapActivityStatus.tapFirstX)
print('Tap interrupt was triggered by y axis:',     tapActivityStatus.tapFirstY)
print('Tap interrupt was triggered by z axis:',     tapActivityStatus.tapFirstZ)
print('The sign of activity trigger was negative:', tapActivityStatus.activeSign)
print('Activity interrupt was triggered by x axis:',tapActivityStatus.activeFirstX)
print('Activity interrupt was triggered by y axis:',tapActivityStatus.activeFirstY)
print('Activity interrupt was triggered by z axis:',tapActivityStatus.activeFirstZ)

"""
Orientation status is also an object, can be stored in a variable
if multiple states are to be checked at once
"""
# Read orientation status:
print('X-Y orientation status number:',sensor.orientationStatus.orientationNumber)
print('Z axis is downward looking:',sensor.orientationStatus.downwardLooking)
"""
X-Y orientation status numbers legend:
0-portrait upright, 1-portrait upside-down, 2-landscape left, 3-landscape right.
"""

'''
The sensor has many advanced functions and a lot of flexibility, especially regarding
the interrupts handling, which can be very handy. The settings below are optional,
but it is encouraged to look through the functions and see what you might find useful.

Pay attention to the "offsetCalibration()" function, as your MSA301 might require
calibration, that is best set on the device MSA301 itself using the "offsetCalibration()"

'''

#######################################
### ACCESSING READ/WRITE PROPERTIES ###
#######################################

# Sample averaging
print("Current setting of sample averaging is", sensor.sampleAveraging)
sensor.sampleAveraging = 20
"""
Sample averaging is implemented in the driver, not embedded in MSA301.
default is 1, meaning no averaging.
"""

# Units of measurement
print('Currently used units setting is',sensor.units)
sensor.units = 'G'
"""
Available values:
'G' - acceleration readout in g's 
'SI'- acceleration readout in meters per second squared (SI units)
"""

# Setting resolution
print('Current resolution is',sensor.resolution,'bit')
sensor.resolution = 14
"""
Available values correspond to bits of resolution:
8, 10, 12 or 14
default is 14bit resolution
"""

# Setting range
print('Current range is +/-',sensor.range,'g')
sensor.range = 2
"""
Avaiable values correspond to the G's of range:
2, 4, 8 or 16
(e.g. from -2g to 2g for value 2)
default is 2g range

"""

# Setting power mode
print('Current power mode is',sensor.powerMode)
sensor.powerMode = 'Normal'
"""
Available values:
'Normal', 'LowPwr', 'Suspnd'
factory default is 'Suspnd'. It can be changed in the initialization (as described above)
"""

# Getting and setting output data rate
print('Current output data rate is',sensor.outputDataRate,'miliseconds')
sensor.outputDataRate = 1
"""
Available values are powers of 2 of miliseconds between data outputs:
1, 2, 4, ... , 512 or 1024
1024ms and 512ms are not available in normal power mode
1ms and 2ms are not available in low power mode supposedly
default - 1ms
"""

# Getting and setting output data rate for low power mode
print('Current low-power output data rate is',sensor.outputDataRateLP,'miliseconds')
sensor.outputDataRateLP = 2
"""
Available values correspond to ODR at low power mode as powers of 2 of miliseconds:
2, 4, ..., 512
default - 2ms

"""
# Configuration of the latching behavior of all interrupts
# (excluding the new-data interrupt, which resets when data is read)
print('Current latch configuration is',sensor.intLatchConfig)
sensor.intLatchConfig = 'NoLatch'
"""
Available values:
"NoLatch", "250ms", "500ms", "1s", "2s", "4s", "8s",
"Latch", "1ms", "2ms", "25ms", "50ms", "100ms"
Default is "NoLatch"
"""

# Interrupt reset - resets all interrupts latched at the moment
sensor.intLatchReset()
"""
No arguments.
"""

# Freefall duration setting
print('Current freefall duration is',sensor.fallDuration)
sensor.fallDuration = 20
"""
Available values:
Number (int or float) >=2 and <514
represents the freefall duration in miliseconds
to trigger the freefall interrupt
20 is default
"""

# Freefall threshold getting and setting
print('Current freefall threshold is',sensor.fallThreshold)
sensor.fallThreshold = 375
"""
Available arguments:
Number (int or float) >=0 and <2000
represents the freefall threshold im mili g's
375 is default
"""

# Freefall mode setting
print('Current freefall detection mode is',sensor.fallMode)
sensor.fallMode = 'SingleMode'
"""
Available values:
'SumMode', 'SingleMode'
SumMode - freefall interrupt detection is based on the sum of all axes
SingleMode - freefall interrupt detection is based on the largest absolute value among all axes
default is SingleMode
"""

# Freefall hysteresis setting
print("Current freefall hysteresis is",sensor.fallHyst,"mili g's")
sensor.fallHyst = 125
"""
Available values:
Integer Number multiple of 125, up to 375
represents the freefall hysteresis im mili g's
125 - default
"""

# Freefall hysteresis getting/setting
print('Activity duration is ',sensor.activeDur,'miliseconds')
sensor.activeDur = 1
"""
Available arguments:
Number (int) >=1 and <4
represents the number of miliseconds to trigger activity interrupt
1 - default
"""

# Active threshold getting/setting
print("Current active threshold is ",sensor.activeThr,"mili g's")
sensor.activeThr = 0.0390625
"""
Available values:
Number (float) >=0 and <0.5
represents the fraction of the current sensor g-range
to trigger the activity interrupt
0.0390625 - default

"""

# Tap quiet duration getting/setting
print('Current tap quiet duration is ',sensor.tapQuietDur,'miliseconds')
sensor.tapQuietDur = 30
"""
Available values:
20, 30
Represent number of miliseconds of tap quiet duration.
Refer to datasheet for details.

"""

# Tap shock duration getting/setting
print('Current tap shock duration is ',sensor.tapShockDur,'miliseconds')
sensor.tapShockDur = 50
"""
Available values:
50, 70
Represent number of miliseconds of tap shock duration.
refer to datasheet for details

"""

# Tap threshold getting/setting
print('Current tap threshold is ',sensor.tapThr,'fraction of the current range')
sensor.tapThr = 0.3125
"""
Available values:
Number (int or float) >=0 and <1.
Represents the fraction of the current g-range to trigger a tap interrupt
0.3125 is default

"""

# Orientation hysteresis setting
print("Current orientation hysteresis is ",sensor.orientHyst,"mili g's")
sensor.orientHyst = 62.5
"""
Available values:
Number (int or float) >=0 and <500.
Represents the acceleration in mili g's of orientation hysteresis
62.5 is default

"""

# Getting/setting of z-blocking behavior
print('Current orientation blocking setting is',sensor.zBlockMode)
sensor.zBlockMode = 'ZaxSlopeBlock'
"""
Available values:
'NoBlock'
'ZaxBlock'
'ZaxSlopeBlock' (default)
refer to datasheet for explanation

"""

# Getting/setting of z-blocking behavior
print('Current orientation mode is',sensor.orientMode)
sensor.orientMode = 'Symmetric'
"""
Available values:
'Symmetric' - (symmetrical mode) <- default
'HSymmetric'- (high-symmetrical mode)
'LSymmetric'- (low-symmetrical mode)
refer to datasheet for explanation

"""

# Z-blocking threshold getting/setting
print("Current z-blocking threshold is",sensor.zBlockThreshold,"mili g's")
sensor.zBlockThreshold = 500
"""
Available arguments:
Number (int or float) >=0 and <1000
representing the z-blocking threshold in mili-g's
default: 500
"""

###############################
### CONFIGURATION FUNCTIONS ###
###############################
"""
The configuration functions take any number of keyword arguments. If called without any argument, they return
an object with the current setting. Generic syntax:
- To setup:
sensor.configFunction(attribute1 = value1, attribute2 = value2, ...)
- To get the state:
configState = configFunction()
print(configState.attribute1)

The functions include:
axesConfig(), interruptConfig(), mapInterruptsToIntPin(), intPinConfig(), offsetCalibration()

"""

# Toggle axes on/off, swap x-y axes or reverse any axis
sensor.axesConfig(yAxisDisable = True) #disabled the y-axis
currentAxesConfig = sensor.axesConfig()
print('Y axis currently disabled:',currentAxesConfig.yAxisDisable)
print('X axis currently swapped:',currentAxesConfig.xAxisSwap)
print('With y-axis disabled: ', sensor.acceleration)
sensor.axesConfig(yAxisDisable = False)#turned the y-axis back on
print('With y-axis enabled: ', sensor.acceleration)
"""
Available attributes:
"xAxisDisable", "yAxisDisable", "zAxisDisable", "xAxisSwap", "yAxisSwap", "zAxisSwap", "xyAxesSwap"
You can give several arguments at once such as
sensor.axesConfig(xAxisDisable = True, yAxisDisable = False, zAxisDisable = True, xAxisSwap = True)
by default, all axes are on and not swapped
"""

# Enable/disable interrupts
currentInterruptConfig = sensor.interruptConfig()
print('New data interrupt is enabled:', currentInterruptConfig.newDataIntEnable)
sensor.interruptConfig(singleTapIntEnable=True, fallIntEnable=True)
sensor.interruptConfig(singleTapIntEnable=False, fallIntEnable=False) #undo
"""
Available attributes (all boolean):

orientIntEnable, singleTapIntEnable,
doubleTapIntEnable, activIntZEnable,
activIntYEnable, activIntXEnable,
newDataIntEnable, fallIntEnable

any combination of the above at once
by factory default all interrupts are disabled.
"""

# Map interrupts to the hardware interrupt pin
currentInterruptsMapped = sensor.mapInterruptsToIntPin()
print('Freefall detection is mapped to interrupt pin:',currentInterruptsMapped.fallIntMap)
sensor.mapInterruptsToIntPin(orientIntMap=True, activeIntMap=True)
sensor.mapInterruptsToIntPin(orientIntMap=False, activeIntMap=False)#undo
"""
Available attributes (all boolean):

orientIntMap, singleTapIntMap,
doubleTapIntMap, activIntMap,
fallIntMap, newDataIntMap,

any combination of the above at once
by default no interrupts are mapped to the pin
"""

# Configuration of the hardware interrupt pin
intPinConfig = sensor.intPinConfig()
print('Currently interrupt pin is open drain:',intPinConfig.openDrain)
sensor.intPinConfig(openDrain=True, highWhenActive=True)
"""
Available attributes (all boolean):
openDrain (if false: the pin is push-pull)
highWhenActive (if false: the pin is low when interrupt is active)

The function accepts any or both of the arguments at once.
default is push-pull and low when active

"""

# Offset calibration function
currentOffsetCalib = sensor.offsetCalibration()
offsets = (currentOffsetCalib.xOffset, currentOffsetCalib.yOffset, currentOffsetCalib.zOffset)
print("Current hardware offset calibration setting is ",offsets,"mili g's")
sensor.offsetCalibration(xOffset=300, zOffset=0)
currentOffsetCalib = sensor.offsetCalibration()
offsets = (currentOffsetCalib.xOffset, currentOffsetCalib.yOffset, currentOffsetCalib.zOffset)
print("Current hardware offset calibration setting is ",offsets,"mili g's")
"""
Available attributes: any or all of the below:
offsetX=value, offsetY=value, offsetZ=value
each value must be >=-500 and <500
corresponds to the offset correction in mili-g's
default is 0,0,0.

If no argument is given, the function returns the current calibration
as a tuple (x_offset,y_offset,z_offset) in mili-g's

"""

# Function that resets all the read/write registers of the MSA301 to factory settings
sensor.resetAllDefaults()
print('All defaults reset!')
#initialize the sensor again, with new parameters
sensor = msa301.MSA301(i2c,powerMode = 'Normal',sampleAveraging = 20)
#set the new data interrupt on, so that the averaging waits for new available data
sensor.interruptConfig(newDataIntEnable = True)

#############################
### USAGE OF MSA301EXTRAS ###
#############################

"""
The extras include:
1) Auto-calibration function
2) Software offsets

1) The auto-calibration function
Takes no arguments and returns a tuple of new offsets in mili-g's.
The function asks to orient the accelerometer in 4 different directions and measures the acceleration
vector in each one. Then it finds geometrically the offset to correct for as a center of a sphere
defined by the 4 vectors (4 points in space uniquely define a sphere). The function also provides
feedback about the quality of the calibration: whether the uncertainty is below the hardware offset precision
and whether the orientations were sufficiently different. I performed Monte-Carlo simulations of various
random sets of orientations and their influence on the calibration uncertainty. The function evaluates it,
providing a score as a feedback: it tells how the chosen orientations influenced the calibration uncertainty
(the best case is orienting the accelerometer in the directions of vertices of a tetrahedron).
The score is a percentile of how good the orientations were.

#######################################
USAGE OF THE AUTO-CALIBRATION FUNCTION:
#######################################
"""
# uncomment to perform the auto-calibration
(xOffsetAuto,yOffsetAuto,zOffsetAuto) = msa301extras.autoOffsetCalibration(sensor)
#(xOffsetAuto,yOffsetAuto,zOffsetAuto) = (-72.11861, 191.9877, -510.1704) # some values in mili-g's given
print("Offsets found:",(xOffsetAuto,yOffsetAuto,zOffsetAuto),"mili-g's")

# The offsets from this function can be used to perform the hardware calibration:
# (trimming to maximum hardware offset range, less than 500 and mire or equal -500)
xOffsetAutoTrimmed = max(min(xOffsetAuto,499),-500)
yOffsetAutoTrimmed = max(min(yOffsetAuto,499),-500)
zOffsetAutoTrimmed = max(min(zOffsetAuto,499),-500)
print('Reading before calibration: ',sensor.acceleration)
sensor.offsetCalibration(xOffset=xOffsetAutoTrimmed, yOffset=yOffsetAutoTrimmed, zOffset=zOffsetAutoTrimmed)
print('Reading after calibration: ',sensor.acceleration)

"""
2) Software offsets
It is a class to create an instance object of. It allows to set a software offset that will stack on top of
hardware offsets or act instead, if sensor.offsetCalibration(xOffset=0,yOffset=0,zOffset=0).
When offsets are set, it automatically saves them in a file calib_data.bin, and when the object is initialized,
it tries to read from the file to get a previous calibration.

##############################
USAGE OF SOFTWARE-CALIBRATION:
##############################
"""
# Set hardware offsets to 0 (recommended)
sensor.offsetCalibration(xOffset=0,yOffset=0,zOffset=0)

# initialize
sensorSC = msa301extras.SoftwareCalibration(sensor)

# set base offsets in units of mili-g's,for example based on calib. above
sensorSC.baseOffsets = (xOffsetAuto,yOffsetAuto,zOffsetAuto)

print('Currently set software offsets: ',sensorSC.offsets,"mili-g's")
print('Reading without software calibration:',sensor.acceleration)
print('Reading with software calibration:',sensorSC.acceleration)

"""
IMPORTANT: If you change .axisConfig() or .units
it is necessary to update the software offsets using the .updateOffsets() function:
"""
# Some changes in axes config
sensor.axesConfig(xAxisDisable = True, xyAxesSwap = True, yAxisSwap = True)
sensorSC.updateOffsets() # Update the offsets now
print(sensorSC.acceleration) # print out the result

# Change of units
sensor.units = 'SI'
sensorSC.updateOffsets() # Update the offsets now
print(sensorSC.acceleration) # print out the result

