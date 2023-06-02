#
# Copyright Wojciech Szmyt 2023, MIT License
# Custom driver for MSA301 3-axis accelerometer, 
# based on the MicroPython I2C driver for LIS2HH12 3-axis accelerometer, credit: 2017-2018 Mika Tuupola
# 


"""
MicroPython I2C driver for MSA301 3-axis accelerometer
Refer to datasheet: MEMSensing Microsystems Data Sheet V 1.0 / July 2017 MSA301
"""

import ustruct
from machine import I2C
import utime

__version__ = "0.0.1"

class ReturnDataObject:
    pass #empty class to return data in its objects

class MSA301():
    """Class which provides interface to MSA301 3-axis accelerometer."""
    ###################################
    #### MSA301 register addresses ####
    ###################################

    ### ADDRESSES OF READ ONLY MEMORY ###
    _SOFT_RESET = 0x00 #soft reset address
    _WHO_AM_I = 0x01 # Address of part ID (0x13 is MSA301 part ID)
    _OUT_X_L = 0x02 #low  byte of x-axis output
    _OUT_X_H = 0x03 #high byte of x-axis output
    _OUT_Y_L = 0x04 #low  byte of y-axis output
    _OUT_Y_H = 0x05 #high byte of y-axis output
    _OUT_Z_L = 0x06 #low  byte of z-axis output
    _OUT_Z_H = 0x07 #high byte of z-axis output
    _MOT_INT = 0x09 #motion interrupt
    _DAT_INT = 0x0A #new data interrupt
    _TAP_ACT_INT_STAT = 0x0B #status of tap and activity interrupts
    _ORIENT_STAT = 0x0C #orientation status

    ### ADDRESSES OF READ/WRITE MEMORY ###
    _RES_RANGE = 0x0F #device resolution and range setting
    _ODR_AXISTOGGLE = 0x10 #output data rate setting and turning axes on and off
    _PWRMODE_BW = 0x11 #power mode and setting of output data rate at low power
    _SWAP_POL = 0x12 #axes polarity swapping
    _INT_SET0 = 0x16 #on/off of interrupts first byte
    _INT_SET1 = 0x17 #on/off of interrupts second byte
    _INT_MAP0 = 0x19 #mapping of interrupts to interrupt pin first byte
    _INT_MAP1 = 0x1A #mapping of interrupts to interrupt pin second byte
    _INT_CFG = 0x20  #configuration of state of the interrupt pin H/L and open-drain or push-pull
    _INT_LAT = 0x21  #interrupt latch setting
    _FALL_DUR = 0x22 #freefall duration ((set_value)+1)×2ms, default is 20ms
    _FALL_THR = 0x23 #freefall threshold ((set_value)×7.81mg), default is 375mg
    _FALL_HYS = 0x24 #freefall hysteresis and mode setting
    _ACTIV_DUR = 0x27 #active duration
    _ACTIV_THR = 0x28 #active threshold: 3.91mg/LSB (2g range);
                             #                  7.81mg/LSB (4g range);
                             #                  15.625mg/LSB (8g range);
                             #                  31.25mg/LSB (16g range)
    _TAP_DUR = 0x2A #tap duration,
    _TAP_THR = 0x2B #tap threshold
    _ORIENT_INT_SETTING = 0x2C #settings of orientation interrupt: hysteresis, z-blocking and orientation mode
    _Z_BLOCK = 0x2D #threshold for z-blocking

    defaultInitDict = { 'sampleAveraging' : 1,
                        'units' : 'G'} # default values of variables necessary to define at sensor initialization

    axesOffsetDict = { 'xOffset' : 0x38,
                       'yOffset' : 0x39,
                       'zOffset' : 0x3A } #addresses of offset calibration
    
    #######################################################
    ### MASKS, VALUES, DICTIONARIES (class attributtes) ###
    #######################################################

    # _SOFT_RESET
    SOFT_RESET_VAL = 0b00100000

    # _WHO_AM_I
    PART_ID = 0x13 # part ID of MSA301

    # MOT_INT motion interrupt status to read
    motionIntStatusDict = { 'orientIntStatus'    : 0b01000000,
                            'singleTapIntStatus' : 0b00100000,
                            'doubleTapIntStatus' : 0b00010000,
                            'activeIntStatus'    : 0b00000100,
                            'fallIntStatus'      : 0b00000001 }

    # _TAP_ACT_INT_STAT status of tap interrupts masks
    tapActIntStatusDict = { 'tapSign'      : 0b10000000,
                            'tapFirstX'    : 0b01000000,
                            'tapFirstY'    : 0b00100000,
                            'tapFirstZ'    : 0b00010000,
                            'activeSign'   : 0b00001000,
                            'activeFirstX' : 0b00000100,
                            'activeFirstY' : 0b00000010,
                            'activeFirstZ' : 0b00000001 }

    # _ORIENT_STAT orientation status
    _Z_ORIENT_MASK  = 0b01000000 #if this bit is true, z-axis is downward looking
    _XY_ORIENT_MASK = 0b00110000 #this value bit-shifted >>4 equals:
                                        # 0 - portrait upright
                                        # 1 - portrait upside down
                                        # 2 - landscape left
                                        # 3 - landscape right

    # _RES_RANGE resolution control
    _RES_MASK  = 0b00001100
    resolutionDict = { 8 : 0b00001100,
                       10: 0b00001000,
                       12: 0b00000100,
                       14: 0b00000000 }

    # _RES_RANGE range control
    _RANGE_MASK  = 0b00000011
    rangeDict = { 2 : 0b00000000,
                  4 : 0b00000001,
                  8 : 0b00000010,
                  16: 0b00000011 }

    # _ODR_AXISTOGGLE toggle axes on/off
    axesToggleDict = { 'xAxisDisable' : 0b10000000,# Bit masks. To disable a given axis, set the given bit to 1. 
                       'yAxisDisable' : 0b01000000,# Value 0 enables axis.
                       'zAxisDisable' : 0b00100000 }

    # _ODR_AXISTOGGLE output data rate settings.
    # miliseconds per data output. Highest is 1000Hz, that is 1ms per data output
    _ODR_MASK  = 0b00001111
    odrDict = { 1   : 0b00001010, #not available in low power mode
                2   : 0b00001001, #not available in low power mode
                4   : 0b00001000,
                8   : 0b00000111,
                16  : 0b00000110,
                32  : 0b00000101,
                64  : 0b00000100,
                128 : 0b00000011,
                256 : 0b00000010,
                512 : 0b00000001, #not available in high power mode
                1024: 0b00000000 }#not available in high power mode

    # _PWRMODE_BW power mode
    _PWRMODE_MASK =  0b11000000
    pwrModeDict = { 'Normal' : 0b00000000,
                    'LowPwr' : 0b01000000,
                    'Suspnd' : 0b10000000 }


    # _PWRMODE_BW output data rate at low power. 1ms data rate is unavailable at low power.
    _LOWPWR_ODR_MASK = 0b00011110
    lowPwrOdrDict = {512 : 0b00000100,
                     256 : 0b00000110,
                     128 : 0b00001000,
                     64  : 0b00001010,
                     32  : 0b00001100,
                     16  : 0b00001110,
                     8   : 0b00010000,
                     4   : 0b00010010,
                     2   : 0b00010100}

    # _SWAP_POL swapping axes polarity masks
    axesSwapDict = { 'xAxisSwap'  : 0b00001000,
                     'yAxisSwap'  : 0b00000100,
                     'zAxisSwap'  : 0b00000010,
                     'xyAxesSwap' : 0b00000001 }

    # _INT_SET0 enable/disable given interrupts masks
    intSet0dict = { 'orientIntEnable'    : 0b01000000,
                    'singleTapIntEnable' : 0b00100000,
                    'doubleTapIntEnable' : 0b00010000,
                    'activeIntZEnable'   : 0b00000100,
                    'activeIntYEnable'   : 0b00000010,
                    'activeIntXEnable'   : 0b00000001 }

    # _INT_SET1 enable/disable given interrupts masks
    intSet1dict = {'newDataIntEnable' : 0b00010000,
                   'fallIntEnable'    : 0b00001000 }

    # _INT_MAP0 map interrupts to interrupt pin
    intMap0dict = { 'orientIntMap'    : 0b01000000,
                    'singleTapIntMap' : 0b00100000,
                    'doubleTapIntMap' : 0b00010000,
                    'activeIntMap'    : 0b00000100,
                    'fallIntMap'      : 0b00000001 }

    # _INT_MAP1 map interrupts to interrupt pin
    intMap1dict = { 'newDataIntMap' : 0b00000001 }

    # _INT_CFG interrupt pin behavior configuration
    intPinConfigDict = { 'openDrain'      : 0b00000010,
                         'highWhenActive' : 0b00000001 }

    # _INT_LAT interrupt latch setting
    _INT_RESET_MASK     = 0b10000000 #mask for bits resetting (de-latching) the interrupt
    _INT_LATSET_MASK    = 0b00001111 #mask for bits setting the latch time
    intLatchDict = { 'NoLatch' : 0b00000000,
                     '250ms'   : 0b00000001,
                     '500ms'   : 0b00000010,
                     '1s'      : 0b00000011,
                     '2s'      : 0b00000100,
                     '4s'      : 0b00000101,
                     '8s'      : 0b00000110,
                     'Latch'   : 0b00000111,
                     '1ms'     : 0b00001010,
                     '2ms'     : 0b00001011,
                     '25ms'    : 0b00001100,
                     '50ms'    : 0b00001100,
                     '100ms'   : 0b00001110 }

    # _FALL_HYS hysteresis setting
    _FALL_MODE_MASK = 0b00000100 #bit in this location high - sum mode; low - single mode
    fallModeDict = { 'SumMode'    : 0b00000100,
                     'SingleMode' : 0b00000000 }
    _FALL_HYST_MASK = 0b00000011 #hysteresis = value×125mg

    # _ACTIV_DUR duration of active interurupt
    _ACTIV_DUR_MASK = 0b00000011 # active duration time = (value+1)ms

    # _TAP_DUR tap duration
    _TAP_QUIET_MASK = 0b10000000 #high bit here - 20ms; low - 30ms
    tapQuietDict = { 20 : 0b10000000,
                     30 : 0b00000000 }
    _TAP_SHOCK_MASK = 0b01000000 #high bit here - 70ms; low - 50ms
    tapShockDict = { 70 : 0b01000000,
                     50 : 0b00000000 }
    _TAP_DUR_MASK   = 0b00000111
    tapDurDict = {50 : 0b00000000,
                  100: 0b00000001,
                  150: 0b00000010,
                  200: 0b00000011,
                  250: 0b00000100,
                  375: 0b00000101,
                  500: 0b00000110,
                  700: 0b00000111 }

    # _TAP_THR threshold of tap interrupt
    _TAP_THR_MASK = 0b00011111 #62.5mg/LSB(2g range); 125mg/LSB(4g range); 250mg/LSB(8g range); 500mg/LSB(16g range)

    # _ORIENT_INT_SETTING settings of orientation interrupt
    _ORIENT_HYST_MASK  = 0b01110000 #hysteresis of irientation interrupt, 1LSB=62.5mg

    _ORIENT_BLOCK_MASK = 0b00001100
    zBlockModeDict = { 'NoBlock'      : 0b00000000,
                       'ZaxBlock'     : 0b00000100,
                       'ZaxSlopeBlock': 0b00001000} #z_axis blocking or slope in any axis > 0.2g

    _ORIENT_MODE_MASK  = 0b00000011
    orientModeDict = { 'Symmetric' : 0b00000000, #symmetrical mode
                       'HSymmetric': 0b00000001, #high-symmetrical mode
                       'LSymmetric': 0b00000010 }#low-symmetrical mode

    # _Z_BLOCK setting of z-blocking
    _Z_BLOCK_MASK  = 0b00001111 #value = threshold for z-block, 1LSB=62.5mg (max=0.9375g)

    unitsDict = {'G' : 0.001,       # 1 mg = 0.001 g
                 'SI': 0.00980665 } # 1 mg = 0.00980665 m/s^2
    
    def __init__(self, i2c, **kwargs):
        # set the i2c
        self.i2c = i2c
        # give default address
        if 'address' not in kwargs:
            self.address = 0x26
        # verify the correct device
        if MSA301.PART_ID != self.whoAmI:
            raise RuntimeError('MSA301 not found in I2C bus.')
        
        # setting the scale factor according to the current state stored on the MSA301
        self.scaleFactor = (self.range*125)/2**12
        
        # set the necessary attributes not given in keyword arguments
        for key in set(MSA301.defaultInitDict) - set(kwargs):
            setattr(self,key,MSA301.defaultInitDict[key])
        # set the attributes given with keywords
        for key, value in kwargs.items():
            if not isinstance(getattr(MSA301,key,None),property):
                raise AttributeError(key,'is not a property of MSA301.')
            setattr(self,key,value)
            
        # getting the setting of new data interrupt (low-level programmed for efficiency)
        self._newDataIntEnable = bool(self._register_char(MSA301._INT_SET1)
                                      & MSA301.intSet1dict['newDataIntEnable'])
        
        # Declaration of empty data objects as internal variables to store statuses
        self._motionInterrupts  = ReturnDataObject()
        self._tapActivityStatus = ReturnDataObject()
        self._orientationStatus = ReturnDataObject()

    @property
    def acceleration(self):
        """
        Acceleration measured by the sensor. By default will return a
        3-tuple of X, Y, Z axis acceleration values in m/s^2. Will
        return values in g if constructor was provided `sf=SF_G`
        parameter.
        """
                
        x = 0
        y = 0
        z = 0
                
        for i in range(self._sampleAveraging):
            while not self.newDataReady:
                pass
            data = self._register_3_words(MSA301._OUT_X_L)
            x += data[0]
            y += data[1]
            z += data[2]
        x *= self._factor
        y *= self._factor
        z *= self._factor
        
        return (x, y, z)
    @acceleration.setter
    def acceleration(self,value):
        raise AttributeError('.acceleration is a read-only property')
    
    @property
    def scaleFactor(self):
        return self._scaleFactor
    
    @scaleFactor.setter
    def scaleFactor(self,value):
        self._scaleFactor = value
        if hasattr(self, '_unitsFactor') and hasattr(self, '_sampleAveraging'):
            self._factor = self._scaleFactor*self._unitsFactor/self._sampleAveraging
    
    @property
    def units(self):
        return self._units
    
    @units.setter
    def units(self,value):
        if value in MSA301.unitsDict:
            self._unitsFactor = MSA301.unitsDict[value]
            self._units = value
            if hasattr(self, '_scaleFactor') and hasattr(self, '_sampleAveraging'):
                self._factor = self._scaleFactor*self._unitsFactor/self._sampleAveraging
        else:
            raise ValueError("Available units are: 'G' and 'SI'")

    @property
    def sampleAveraging(self):
        return self._sampleAveraging
    @sampleAveraging.setter
    def sampleAveraging(self,Nsamples):
        if not (Nsamples>0 and isinstance(Nsamples, int)):
            raise ValueError('Number of samples must be a positive integer')
        self._sampleAveraging = Nsamples
        if hasattr(self, '_scaleFactor') and hasattr(self, '_unitsFactor'):
            self._factor = self._scaleFactor*self._unitsFactor/self._sampleAveraging
    
    @property
    def motionInterrupts(self):
        char = self._register_char(MSA301._MOT_INT)
        for key, value in MSA301.motionIntStatusDict.items():
            setattr(self._motionInterrupts,key,bool( char & value ))
        return self._motionInterrupts
    @motionInterrupts.setter
    def motionInterrupts(self,value):
        raise AttributeError('.motionInterrupts is a read-only property.')
    
    @property
    def tapActivityStatus(self):
        char = self._register_char(MSA301._TAP_ACT_INT_STAT)
        for key, value in MSA301.tapActIntStatusDict.items():
            setattr(self._tapActivityStatus,key,bool( char & value ))
        return self._tapActivityStatus
    @tapActivityStatus.setter
    def tapActivityStatus(self,value):
        raise AttributeError('.tapActivityStatus is a read-only property')
        
    @property
    def orientationStatus(self):
        char = self._register_char(MSA301._ORIENT_STAT)
        self._orientationStatus.downwardLooking   = bool(char & MSA301._Z_ORIENT_MASK)
        self._orientationStatus.orientationNumber = (char & MSA301._XY_ORIENT_MASK)>>4
        return self._orientationStatus
    @orientationStatus.setter
    def orientationStatus(self,value):
        raise AttributeError('.orientationStatus is a read-only property')
    
    @property
    def newDataReady(self):
        return not self._newDataIntEnable or (self._register_char(MSA301._DAT_INT))
    @newDataReady.setter
    def newDataReady(self,value):
        raise AttributeError('.newDataReady is a read-only property')

    @property
    def whoAmI(self):
        # Value of the whoAmI register.
        return self._register_char(MSA301._WHO_AM_I)
    @whoAmI.setter
    def whoAmI(self,value):
        raise AttributeError('.whoAmI is a read-only property')

    def _register_word(self, register, value=None):
        if value is None:
            data = self.i2c.readfrom_mem(self.address, register, 2)
            return ustruct.unpack("<h", data)[0]
        data = ustruct.pack("<h", value)
        return self.i2c.writeto_mem(self.address, register, data)

    def _register_3_words(self, register):
        #gives a tuple of 3 words as integers
        #useful for reading acceleration from all axes at once
        data = self.i2c.readfrom_mem(self.address, register, 6)
        return (ustruct.unpack("<h", data[:2])[0],
                ustruct.unpack("<h", data[2:4])[0],
                ustruct.unpack("<h", data[4:])[0])

    def _register_char(self, register, value=None):
        if value is None:
            return self.i2c.readfrom_mem(self.address, register, 1)[0]
        data = ustruct.pack("<b", value)
        return self.i2c.writeto_mem(self.address, register, data)

    
    ### RESOLUTION ###
    @property
    def resolution(self):
        return 14-((self._register_char(MSA301._RES_RANGE) & MSA301._RES_MASK ) >> 1)
    @resolution.setter
    def resolution(self, value):
        self._setMaskedValueDictBased(MSA301._RES_RANGE,MSA301._RES_MASK,value,MSA301.resolutionDict,
                                      'Available resolution values in bits are:')
    
    ### RANGE ###
    @property
    def range(self):
        return 2**((self._register_char(MSA301._RES_RANGE) & MSA301._RANGE_MASK)+1)
    @range.setter
    def range(self, value):
        self._setMaskedValueDictBased(MSA301._RES_RANGE,MSA301._RANGE_MASK,value,MSA301.rangeDict,
                                      'Available G-range values are:')
        self.scaleFactor = (value*125)/2**12

    ### AXES CONFIGURATION ###
    def axesConfig(self, **kwargs):
        return self._dynamicBitwiseUpdate([MSA301.axesToggleDict, MSA301.axesSwapDict],
                                          [MSA301._ODR_AXISTOGGLE, MSA301._SWAP_POL], **kwargs)

    ### OUTPUT DATA RATE AT NORMAL POWER ###
    @property
    def outputDataRate(self):
        return 2**(10 - min((self._register_char(MSA301._ODR_AXISTOGGLE) & MSA301._ODR_MASK),10))
    @outputDataRate.setter
    def outputDataRate(self, value):
        self._setMaskedValueDictBased(MSA301._ODR_AXISTOGGLE,MSA301._ODR_MASK,value,MSA301.odrDict,
                                      'Available output data rate in miliseconds are:')
                
    ### POWER MODE ###
    @property
    def powerMode(self):
        value = self._register_char(MSA301._PWRMODE_BW) & MSA301._PWRMODE_MASK
        return self._getKeyOfValue(value,MSA301.pwrModeDict)
    @powerMode.setter
    def powerMode(self, value):
        self._setMaskedValueDictBased(MSA301._PWRMODE_BW,MSA301._PWRMODE_MASK,value,MSA301.pwrModeDict,
                                      'Avaliable power modes are:')
        
    ### OUTPUT DATA RATE AT LOW POWER ###
    @property
    def outputDataRateLP(self):
        return 2**(11-(min((self._register_char(MSA301._PWRMODE_BW) & MSA301._LOWPWR_ODR_MASK)>>1,10)))
    @outputDataRateLP.setter
    def outputDataRateLP(self, value):
        self._setMaskedValueDictBased(MSA301._PWRMODE_BW,MSA301._LOWPWR_ODR_MASK,value,MSA301.lowPwrOdrDict,
                                      'Available low-power output data rate in miliseconds are:')
    
    ### DICTIONARY-BASED INTERNAL FUNCTIONS FOR REPEATABLE OPERATIONS
    def _getKeyOfValue(self,value,dictionary):
        for item in dictionary:
            if dictionary[item] == value:
                return item
    def _setMaskedValueDictBased(self,address,mask,value,dictionary,errorMessage):
        if value in dictionary:
            char = self._register_char(address)
            char &= ~mask # clear bits
            char |= dictionary[value]
            self._register_char(address, char)
        else:
            raise AttributeError(errorMessage, [item for item in dictionary])
    
    def _dynamicBitwiseUpdate(self, dictArr, addrArr, **kwargs):
        # be sure to pass arrays of dictArr and addrArr of the same length
        # with corresponding elements
        nBytes = len(dictArr)
        if kwargs:
            setting =     [0b00000000] * nBytes
            settingMask = [0b00000000] * nBytes
            
            for key, value in kwargs.items():
                if not isinstance(value,bool):
                    raise ValueError('Values must be boolean True of False')
                legalAttribute = False
                for i in range(nBytes):
                    if key in dictArr[i]:
                        settingMask[i] |= dictArr[i][key]
                        setting[i]     |= dictArr[i][key]*value
                        legalAttribute = True
                        break
                if not legalAttribute:
                    raise AttributeError('Available attribute names are:\n',
                                     [[item for item in selectDict] for selectDict in dictArr ])
            for i in range(nBytes):
                if settingMask[i]:
                    char = self._register_char(addrArr[i])
                    char &= ~settingMask[i]
                    char |= setting[i]
                    self._register_char(addrArr[i],char)
        else:
            dataToReturn = ReturnDataObject()
            for i in range(nBytes):
                char = self._register_char(addrArr[i])
                for key, value in dictArr[i].items():
                    setattr(dataToReturn, key, bool(char & value))
            return dataToReturn


    ### ENABLE/DISABLE GIVEN INTERRUPTS ###
    def interruptConfig(self, **kwargs):
        dataToReturn = self._dynamicBitwiseUpdate([MSA301.intSet0dict, MSA301.intSet1dict],
                                                  [MSA301._INT_SET0, MSA301._INT_SET1], **kwargs)
        if 'newDataIntEnable' in kwargs:
            self._newDataIntEnable = kwargs['newDataIntEnable']
        return dataToReturn
    
    ### MAP INTERRUPTS TO THE INTERRUPT PIN ###
    def mapInterruptsToIntPin(self, **kwargs):
        return self._dynamicBitwiseUpdate([MSA301.intMap0dict, MSA301.intMap1dict],
                                          [MSA301._INT_MAP0, MSA301._INT_MAP1], **kwargs)
    
    ### CONFIGURATION OF INTERRUPT PIN BEHAVIOR ###
    def intPinConfig(self, **kwargs):
        return self._dynamicBitwiseUpdate([MSA301.intPinConfigDict], [MSA301._INT_CFG], **kwargs)

    ### CONFIGURATION OF LATCHING BEHAVIOR OF ALL INTERRUPTS ###
    @property
    def intLatchConfig(self):
        value = self._register_char(MSA301._INT_LAT) & MSA301._INT_LATSET_MASK
        return self._getKeyOfValue(value,MSA301.intLatchDict)
            
    @intLatchConfig.setter
    def intLatchConfig(self, value):
        self._setMaskedValueDictBased(MSA301._INT_LAT,MSA301._INT_LATSET_MASK,value,MSA301.intLatchDict,
                                      'Avaliable values of interrupt latching configuration are:')
        
    ### RESET ALL LATCHED INTERRUPTS ###
    def intLatchReset(self):
        self._register_char( MSA301._INT_LAT, self._register_char(MSA301._INT_LAT) | MSA301._INT_RESET_MASK )
        
    ### FREEFALL DURATION SETTING ###
    # the argument is a value more or equal 2 and less than 514 corresponding to the number of ms
    # of the freefall detection
    # the value is rounded down, set at 8-bit resolution
    @property
    def fallDuration(self):
        return (self._register_char(MSA301._FALL_DUR)+1)*2
    @fallDuration.setter
    def fallDuration(self,fallDurationMS): #the property sets the freefall duration in ms
        if fallDurationMS<2 or fallDurationMS>=514 or not isinstance(fallDurationMS,(int,float)):
            raise ValueError('Freefall duration in ms must be >=0 and <514')
        self._register_char(MSA301._FALL_DUR,int(fallDurationMS/2)-1)
        
    ### FREEFALL THRESHOLD SETTING ###
    # the function sets the freefall threshold in mili-g's
    # rounded down, set at 8-bit resolution
    @property
    def fallThreshold(self):
        return self._register_char(MSA301._FALL_THR)*7.8125
    @fallThreshold.setter
    def fallThreshold(self,fallThresholdMG):
        if not isinstance(fallThresholdMG,(int,float)) or fallThresholdMG<0 or not fallThresholdMG<2000:
            raise ValueError('Freefall threshold in mg must be a number greater or equal 0 and below 2000')
        self._register_char(MSA301._FALL_THR,int(fallThresholdMG/7.8125))
        
    ### FREEFALL DETECTION MODE SETTING ###
    @property
    def fallMode(self):
        value = bool(self._register_char(MSA301._FALL_HYS) & MSA301._FALL_MODE_MASK)
        return self._getKeyOfValue(value,MSA301.fallModeDict)
    @fallMode.setter
    def fallMode(self, value): #argument: "SumMode" or "SingleMode"
        self._setMaskedValueDictBased(MSA301._FALL_HYS,MSA301._FALL_MODE_MASK,value,MSA301.fallModeDict,
                                      'Available fall modes are:')
        
    ### FREEFALL HYSTERESIS SETTING ###
    # the argument is a value of freefall hysteresis, multiple of 125 given in mili-g's
    @property
    def fallHyst(self):
        return (self._register_char(MSA301._FALL_HYS) & MSA301._FALL_HYST_MASK) * 125
    @fallHyst.setter
    def fallHyst(self, fallHystMG):
        if fallHystMG%125 or not isinstance(fallHystMG,int) or fallHystMG<0 or fallHystMG>375:
            raise ValueError("Freefall hysteresis in mg's must be an integer multiple of 125, from 0 to 375")
        char = self._register_char(MSA301._FALL_HYS)
        char &= ~MSA301._FALL_HYST_MASK # clear bits
        char |= fallHystMG//125
        self._register_char(MSA301._FALL_HYS, char)
        
    ### ACTIVE DURATIN TIME SETTING ###
    # the argument is a value in ms, integer in the range from 1 to 4
    @property
    def activeDur(self):
        return self._register_char(MSA301._ACTIV_DUR)+1
    @activeDur.setter
    def activeDur(self, activeDurMS):
        if not isinstance(activeDurMS,int) or activeDurMS<1 or activeDurMS>4:
            raise ValueError('Active duration time must be an integer number of ms in the range from 1 to 4')
        self._register_char(MSA301._ACTIV_DUR, activeDurMS-1)
        
    ### ACTIVE THRESHOLD SETTING ###
    # the argument is a value more or equal 0.0 and less than 0.5 corresponding to the fraction of the set range
    # e.g. 0.25 at a range of 2g corresponds to the active threshold of 0.5g
    # the threshold is rounded down, set at 8-bit resolution """
    @property
    def activeThr(self):
        return self._register_char(MSA301._ACTIV_THR)/512
    @activeThr.setter
    def activeThr(self, value):
        if not isinstance(value,(int,float)) or value<0 or value>=0.5:
            raise ValueError('Active threshold must be a fraction of the range, >=0.0 and <0.5')
        self._register_char(MSA301._ACTIV_THR, int(value*512))
        
    ### TAP QUIET DURATION ###
    @property
    def tapQuietDur(self):
        value = bool(self._register_char(MSA301._TAP_DUR) & MSA301._TAP_QUIET_MASK)
        return self._getKeyOfValue(value,MSA301.tapQuietDict)
    
    @tapQuietDur.setter
    def tapQuietDur(self, value):
        self._setMaskedValueDictBased(MSA301._TAP_DUR,MSA301._TAP_QUIET_MASK,value,MSA301.tapQuietDict,
                                      'Avaliable values of tap quiet duration in miliseconds:')
        
    ### TAP SHOCK DURATION ###
    @property
    def tapShockDur(self):
        value = bool(self._register_char(MSA301._TAP_DUR) & MSA301._TAP_SHOCK_MASK)
        return self._getKeyOfValue(value,MSA301.tapShockDict)
    @tapShockDur.setter
    def tapShockDur(self, value):
        self._setMaskedValueDictBased(MSA301._TAP_DUR,MSA301._TAP_SHOCK_MASK,value,MSA301.tapShockDict,
                                      'Avaliable values of tap shock duration in miliseconds:')
        
    ### TAP DURATION ###
    @property
    def tapDur(self):
        value = self._register_char(MSA301._TAP_DUR) & MSA301._TAP_DUR_MASK
        return self._getKeyOfValue(value,MSA301.tapDurDict)
    @tapDur.setter
    def tapDur(self, value):
        self._setMaskedValueDictBased(MSA301._TAP_DUR,MSA301._TAP_DUR_MASK,value,MSA301.tapDurDict,
                                      'Avaliable values of tap duration in miliseconds:')
                 
    ### TAP THRESHOLD ###
    # the argument is a value more or equal 0.0 and less than 1.0 corresponding to the fraction of the set range
    # e.g. 0.5 at a range of 2g corresponds to the tap threshold of 1g
    # the threshold is rounded down, set at 5-bit resolution
    @property
    def tapThr(self):
        return self._register_char(MSA301._TAP_THR)/32
    @tapThr.setter
    def tapThr(self, value):
        if not isinstance(value,(int,float)) or value<0 or value>=1:
            raise ValueError('Tap threshold must be a fraction of the range, >=0.0 and <1')
        self._register_char(MSA301._TAP_THR, int(value*32))
        
    ### ORIENTATION HYSTERESIS SETTING ###
    # the argument is a value more or equal 0 and less than 500 corresponting to mg's of the hysteresis
    # e.g. 250 corresponds to the orientation hysteresis of 250mg
    # the value is rounded down, set at 3-bit resolution
    @property
    def orientHyst(self):
        return (self._register_char(MSA301._ORIENT_INT_SETTING)>>4)*62.5
    @orientHyst.setter
    def orientHyst(self, orientHystMG):
        if not isinstance(orientHystMG,(int,float)) or orientHystMG<0 or orientHystMG>=500:
            raise ValueError('Orientation hysteresis must be >=0.0 and <500.0')
        char = self._register_char(MSA301._ORIENT_INT_SETTING)
        char &= ~MSA301._ORIENT_HYST_MASK # clear bits
        char |= int(orientHystMG*0.016)<<4
        self._register_char(MSA301._ORIENT_INT_SETTING, char)
    
    ### Z-BLOCKING BEHAVIOR ###
    @property
    def zBlockMode(self):
        value = self._register_char(MSA301._ORIENT_INT_SETTING) & MSA301._ORIENT_BLOCK_MASK
        return self._getKeyOfValue(value,MSA301.zBlockModeDict)
    @zBlockMode.setter
    def zBlockMode(self,value):
        self._setMaskedValueDictBased(MSA301._ORIENT_INT_SETTING,MSA301._ORIENT_BLOCK_MASK,
                                      value, MSA301.zBlockModeDict, 'Z-block mode allowed values:')
        
    ### ORIENTATION MODE ###
    @property
    def orientMode(self):
        value = self._register_char(MSA301._ORIENT_INT_SETTING) & MSA301._ORIENT_MODE_MASK
        return self._getKeyOfValue(value,MSA301.orientModeDict)
    @orientMode.setter
    def orientMode(self,value):
        self._setMaskedValueDictBased(MSA301._ORIENT_INT_SETTING,MSA301._ORIENT_MODE_MASK,
                                      value,MSA301.orientModeDict, 'Allowed values of orientation mode:')

    ### Z_BLOCKING THRESHOLD ###
    # the argument is in mg's more or equal 0 and less than 1000 corresponting to mg's of the z-block threshold
    # the value is rounded down, set at a 4-bit resolution
    @property
    def zBlockThreshold(self):
        return self._register_char(MSA301._Z_BLOCK)*62.5
    @zBlockThreshold.setter
    def zBlockThreshold(self, zBlockThrMG):
        if not isinstance(zBlockThrMG,(int,float)) or zBlockThrMG<0 or zBlockThrMG>=1000:
            raise ValueError("Z-blocking threshold in mg's must be >=0.0 and <1000.0")
        self._register_char(MSA301._Z_BLOCK, int(zBlockThrMG/62.5))
        
    ### AXES OFFSET CALIBRATION SETTING OR GETTING ###
    # arguments are x, y and z offset values, each given in mg's
    # more or equal -500 and less than 500, rounded towards 0 and set at 8-bit resolution, signed. 
    # (1LSB=3.90625mg) if no argument is given, the function gives a current offset as a tuple (x_o,y_o,z_o)
    def offsetCalibration(self, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                if not key in MSA301.axesOffsetDict:
                    raise AttributeError('Available attributes are:'
                                         ,[item for item in MSA301.axesOffsetDict])
                if not isinstance(value,(int,float)) or value<-500 or value>=500:
                    raise ValueError("Offsets in mg's are limited to >=-500 and <500. Error in:",key)
                self._register_char(MSA301.axesOffsetDict[key],int(value/3.90625))  
        else:
            dataToReturn = ReturnDataObject()
            for key, value in MSA301.axesOffsetDict.items():
                readOffset = self._register_char(value)*3.90625
                setattr(dataToReturn,key,readOffset if readOffset<500
                                    else readOffset - 1000)
            return dataToReturn #object containing calibraiton data
    
    ### DO A SOFT RESET ###
    def softReset(self):
        self._register_char(MSA301._SOFT_RESET,MSA301.SOFT_RESET_VAL)
    
    ### RESET ALL DEFAULTS ###
    # the function resets all the values of read/write registers to defaults
    def resetAllDefaults(self):
        self._register_char(0x0F,0x00)
        self._register_char(0x10,0x0F)
        self._register_char(0x11,0x9E)
        self._register_char(0x12,0x00)
        self._register_char(0x16,0x00)
        self._register_char(0x17,0x00)
        self._register_char(0x19,0x00)
        self._register_char(0x1A,0x00)
        self._register_char(0x20,0x00)
        self._register_char(0x21,0x00)
        self._register_char(0x22,0x09)
        self._register_char(0x23,0x30)
        self._register_char(0x24,0x01)
        self._register_char(0x27,0x00)
        self._register_char(0x28,0x14)
        self._register_char(0x2A,0x04)
        self._register_char(0x2B,0x0A)
        self._register_char(0x2C,0x18)
        self._register_char(0x2D,0x08)
        self._register_char(0x38,0x00)
        self._register_char(0x39,0x00)
        self._register_char(0x3A,0x00)
        
    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass