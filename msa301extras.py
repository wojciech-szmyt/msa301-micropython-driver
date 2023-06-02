from utime import sleep_ms
import ustruct

class VectorOps:
    @staticmethod
    def scaleVector(a,f):
        #scales vector by a factor
        return [a[0]*f,a[1]*f,a[2]*f]
    
    @staticmethod
    def crossProduct(a,b):
        # arguments are arrays or 3 numbers each (3D vectors)
        product = [ a[1]*b[2]-a[2]*b[1] , a[2]*b[0]-a[0]*b[2] , a[0]*b[1]-a[1]*b[0] ]
        return product
    
    @staticmethod
    def dotProduct(a,b):
        return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
    
    @staticmethod
    def normalizeVector(a):
        # argument is an array or 3 numbers (3D vector)
        norm = VectorOps.getVectorLength(a)
        return VectorOps.scaleVector(a,1/norm)
    
    @staticmethod
    def getVectorLength(a):
        return (a[0]**2+a[1]**2+a[2]**2)**0.5
    
    @staticmethod
    def getMidpoint(a,b):
        return [(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2]
    
    @staticmethod
    def getMatrixDet(a,b,c): #a,b and c are vertical vectors creating a matrix
        return a[0]*b[1]*c[2] + b[0]*c[1]*a[2] + c[0]*a[1]*b[2] - a[2]*b[1]*c[0] - b[2]*c[1]*a[0] - c[2]*a[1]*b[0]

    @staticmethod
    def subtractVectors(a,b):
        return [a[0]-b[0],a[1]-b[1],a[2]-b[2]]
    
    @staticmethod
    def addVectors(a,b):
        return [a[0]+b[0],a[1]+b[1],a[2]+b[2]]
    
    @staticmethod
    def projectVector(a,n):
        #projects a onto direction n
        n = VectorOps.normalizeVector(n)
        return VectorOps.scaleVector(n,VectorOps.dotProduct(a,n))
    
    @staticmethod
    def piecewisePower(a,p):
        return [a[i]**p for i in range(3)]
    
    @staticmethod
    def getSphereCenter(p):
        #p is a 4x3 matrix of 4 vectors that define a tetrahedron
        #to find a sphere defined by this tetrahedron
        
        #Three vectors defining the tetrahedron
        #they are normals of the 3 planes to intersect
        n = [VectorOps.subtractVectors(p[1],p[0]),
             VectorOps.subtractVectors(p[2],p[0]),
             VectorOps.subtractVectors(p[3],p[0])]
            
        #midpoints of 3 edges of the tetrahedron
        m = [VectorOps.getMidpoint(p[0],p[1]),
             VectorOps.getMidpoint(p[0],p[2]),
             VectorOps.getMidpoint(p[0],p[3])]
        
        D = [VectorOps.dotProduct(n[0],m[0]),
             VectorOps.dotProduct(n[1],m[1]),
             VectorOps.dotProduct(n[2],m[2])]
        
        W  = VectorOps.getMatrixDet([n[0][0],n[1][0],n[2][0]],
                                    [n[0][1],n[1][1],n[2][1]],
                                    [n[0][2],n[1][2],n[2][2]])
        
        Wx = VectorOps.getMatrixDet(D,
                                    [n[0][1],n[1][1],n[2][1]],
                                    [n[0][2],n[1][2],n[2][2]])
        
        Wy = VectorOps.getMatrixDet([n[0][0],n[1][0],n[2][0]],
                                    D,
                                    [n[0][2],n[1][2],n[2][2]])
        
        Wz = VectorOps.getMatrixDet([n[0][0],n[1][0],n[2][0]],
                                    [n[0][1],n[1][1],n[2][1]],
                                    D)
        return [Wx/W,Wy/W,Wz/W]

class Welford:
    #class for numerically accurate averaging and standard deviation
    def __init__(self):
        self.k = 0
        self.m = 0
        self.m2 = 0
    
    def update(self, x):
        self.k += 1
        delta = x - self.m
        self.m += delta/self.k
        delta2 = x - self.m
        self.m2 += delta*delta2
    
    @property
    def mean(self):
        return self.m
    
    @property
    def variance(self):
        if self.k<2:
            return float('nan')
        else:
            return self.m2/self.k
        
    @property
    def varianceOfMean(self):
        if self.k<2:
            return float('nan')
        else:
            return self.m2/(self.k*(self.k-1))
        
    @property
    def standardDeviation(self):
        return self.variance**0.5
    
    @property
    def standardDeviationOfMean(self):
        return self.varianceOfMean**0.5

class SoftwareCalibration:
    def __init__(self,sensorObj):
        self.sensorObj = sensorObj
        self._calibFilename = 'calib_data.bin'
        try:
            with open(self._calibFilename,'rb') as f:
                self._baseOffsets = ustruct.unpack("<fff", f.read())
            f.close()
        except OSError:
            self.baseOffsets = (0,0,0)
        self.updateOffsets()
            
    @property
    def offsets(self):
        return self._offsets
    @offsets.setter
    def offsets(self,value):
        raise AttributeError('.offsets are read-only. Only .baseOffsets can be set,\n',
                             '.offsets are calculated based on .baseOffsets and axesConfig.')
    
    def storeBaseOffsets(self):
        with open(self._calibFilename,'wb') as f:
            f.write(ustruct.pack('<fff', *self._baseOffsets))
        f.close()
    
    def updateOffsets(self):
        axesConfig = self.sensorObj.axesConfig()
        tempOffsets = VectorOps.scaleVector(list(self._baseOffsets),self.sensorObj._unitsFactor)
        if axesConfig.xAxisDisable:
            tempOffsets[0] = 0
        if axesConfig.yAxisDisable:
            tempOffsets[1] = 0
        if axesConfig.zAxisDisable:
            tempOffsets[2] = 0
        if axesConfig.xAxisSwap:
            tempOffsets[0] *= -1
        if axesConfig.yAxisSwap:
            tempOffsets[1] *= -1
        if axesConfig.zAxisSwap:
            tempOffsets[2] *= -1
        if axesConfig.xyAxesSwap:
            tempOffsets = [tempOffsets[1],tempOffsets[0],tempOffsets[2]]
        self._offsets = tuple(tempOffsets)
    
    @property
    def baseOffsets(self):
        return self._baseOffsets
    
    @baseOffsets.setter
    def baseOffsets(self,data):
        # set offset data in mili-g's
        self._baseOffsets = data
        self.storeBaseOffsets()
        self.updateOffsets()
    
    # property that gives software-calibrated acceleration
    @property
    def acceleration(self):
                
        x = 0
        y = 0
        z = 0
                
        for i in range(self.sensorObj._sampleAveraging):
            while not self.sensorObj.newDataReady:
                pass
            data = self.sensorObj._register_3_words(self.sensorObj._OUT_X_L)
            x += data[0]
            y += data[1]
            z += data[2]
        x = x*self.sensorObj._factor+self._offsets[0]
        y = y*self.sensorObj._factor+self._offsets[1]
        z = z*self.sensorObj._factor+self._offsets[2]
        
        return (x, y, z)
    
### AUTO-CALIBRATION FUNCTION ###
# the function requires holding the accelerometer in 4 different orientations
# and calibrates the offsets automatically
def autoOffsetCalibration(sensorObject):
    # first keep the original settings
    prev_scaleFactor = sensorObject.scaleFactor
    prev_units = sensorObject.units
    prev_resolution = sensorObject.resolution
    prev_range = sensorObject.range
    prev_sampleAveraging = sensorObject.sampleAveraging
    prev_newDataIntEnable = sensorObject._newDataIntEnable
    prev_odr = sensorObject.outputDataRate
    prev_axesConfig = sensorObject.axesConfig().__dict__
    prev_powerMode = sensorObject.powerMode
    prev_hardwareOffsets = sensorObject.offsetCalibration().__dict__
    
    # set settings for calibration
    sensorObject.resolution = 14
    sensorObject.range = 2
    sensorObject.units = 'G'
    sensorObject.sampleAveraging = 1
    sensorObject.outputDataRate = 1
    sensorObject.powerMode = 'Normal'
    sensorObject.axesConfig(xAxisDisable=False, yAxisDisable=False, zAxisDisable=False,
                            xAxisSwap=False,    yAxisSwap=False,    zAxisSwap=False, xyAxesSwap=False)
    sensorObject.interruptConfig(newDataIntEnable=True)
    
    sensorObject.offsetCalibration(xOffset=0,yOffset=0,zOffset=0)
    
    # declaring arrays for x,y,z measurements for calibration
    
    p = [ [0 for k in range(3)] for i in range(4) ] # 4 points, 3 coordinates each
    u = [ [0 for k in range(3)] for i in range(4) ] # uncertainties of the above
    
    while True:
        for i in range(4):
            print('Step',i+1,'of',4)
            print('Change the accelerometer orientation and hold...')
            sleep_ms(1000)
            secondsRemaining = 3
            while secondsRemaining:
                print(secondsRemaining,'s')
                sleep_ms(1000)
                secondsRemaining -= 1
            
            statistics = [Welford() for k in range(3)]
            
            for j in range(100): #hardcoded averaging of 100 samples
                while not sensorObject.newDataReady:
                    pass
                data = sensorObject._register_3_words(sensorObject._OUT_X_L)
                for k in range(3):
                    statistics[k].update(data[k])
            for k in range(3):
                p[i][k] = statistics[k].mean*sensorObject._factor
                u[i][k] = statistics[k].varianceOfMean*sensorObject._factor**2
        break
    epsilon = 1e-4 #small value of change for numerical derivative
    Q = VectorOps.getSphereCenter(p)
    uQ = [0,0,0] #uncertainty of Q
    uQN = 0 #uncertainty of Q normalized
    for i in range(4):
        inds = [(j+i)%4 for j in range(4)]
        wiggleDirection = VectorOps.normalizeVector(VectorOps.subtractVectors(Q,p[inds[0]]))
        sigma = VectorOps.dotProduct(VectorOps.piecewisePower(wiggleDirection,2),u[inds[0]])**0.5
        pWiggled = VectorOps.addVectors(p[inds[0]],VectorOps.scaleVector(wiggleDirection,epsilon))
        Qwiggled = VectorOps.getSphereCenter([pWiggled,p[inds[1]],p[inds[2]],p[inds[3]]])
        Qchange = VectorOps.subtractVectors(Qwiggled,Q)
        uQN += sum(VectorOps.piecewisePower(Qchange,2))
        uQ = VectorOps.addVectors(uQ,VectorOps.piecewisePower(VectorOps.scaleVector(Qchange,sigma/epsilon),2))
    uQN = (uQN/3)**0.5 / epsilon
    score = 1-2/(uQN+1/uQN)
    """ The score means the fraction of all random arrangements of points
        which would give a smaller uncertainty of calibration than the current one,
        for example score = 0.2 means that the orientations you chose
        for calibration define the top 20% of all possible orientations
        in terms of how precise calibration these orientations can give """
    uQ = VectorOps.piecewisePower(uQ,0.5)
    u = [VectorOps.piecewisePower(u[i],0.5) for i in range(4)]
    
    Q = VectorOps.scaleVector(Q,-1000) # reverse vector and scale g to mili-g:
                                       # sphere center location has to be brought back to (x,y,z)=(0,0,0)
    uQ = VectorOps.scaleVector(uQ,1000)# so that it represents the offsets to be applied
    for i in range(4):
        u[i] = VectorOps.scaleVector(u[i],1000)
    print('Calibration in mili-g:')
    print(Q)
    print('Uncertainty of calibration in mili-g:')
    print(uQ)
    print('Uncertainty XYZ measurement in mili-g:')
    [print(u[i]) for i in range(4)]
    print('Calibration score:')
    print(score)
    print('With this score, the uncertainty of the calibration\nis magnifiedby the factor of',uQN)
    print('with respect to the uncertainty of the acceleration measurement.')
    if any( [unc>3.90625 for unc in uQ] ):
        print('The calibration of some axes exceeds the hardware offset precision of 3.90625mg.')
        print('If you are not satisfied, repeat the calibration with more varied directions')
        print('or hold the device more steadily during the calibration.')
    else:
        print('The calibration uncertainty is well within the reasonable offset precision.')
        print('Offset determination fully successful.')
        
    axesNames = ('X','Y','Z')            
    for i in range(3):
        if Q[i]<-500 or Q[i]>=500:
            print('WARNING:')
            print('Axis',axesNames[i], 'offset out of range for hardware offset: ',Q[i])
            print('Hardware offset range is -500mg <= offset < 500mg')
            print('For an accurate calibration, use software offsets.')
            print('(class SoftwareCalibration) or try another MSA301.')
        
    # Return to previous settings
    sensorObject.scaleFactor = prev_scaleFactor 
    sensorObject.units = prev_units
    sensorObject.resolution = prev_resolution
    sensorObject.range = prev_range
    sensorObject.sampleAveraging = prev_sampleAveraging
    sensorObject.interruptConfig(newDataIntEnable=prev_newDataIntEnable)
    sensorObject.outputDataRate = prev_odr
    sensorObject.axesConfig(**prev_axesConfig)
    sensorObject.powerMode = prev_powerMode
    sensorObject.offsetCalibration(**prev_hardwareOffsets)
    
    return tuple(Q) #tuple of calibration given as floats in units of mili-g's

