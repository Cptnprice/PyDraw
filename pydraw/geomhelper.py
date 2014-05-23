#GEOMETRY HELPER CLASSES
import math

class _Line:
    def __init__(self, x1,y1,x2,y2):
        self.x1,self.y1,self.x2,self.y2 = x1,y1,x2,y2
        self.xdiff = x2-x1
        self.ydiff = y2-y1
        try:
            self.slope = self.ydiff/float(self.xdiff)
            self.zero_y = self.slope*(0-x1)+y1
        except ZeroDivisionError:
            self.slope = None
            self.zero_y = None
    def __str__(self):
        return str(self.tolist())
    def tolist(self):
        return ((self.x1,self.y1),(self.x2,self.y2))
    def intersect(self, otherline, infinite=False):
        """
        Input must be another line instance
        Finds real or imaginary intersect assuming lines go forever, regardless of real intersect
        Infinite is based on http://stackoverflow.com/questions/20677795/find-the-point-of-intersecting-lines
        Real is based on http://stackoverflow.com/questions/18234049/determine-if-two-lines-intersect
        """
        if infinite:
            D  = -self.ydiff * otherline.xdiff - self.xdiff * -otherline.ydiff
            Dx = self._selfprod() * otherline.xdiff - self.xdiff * otherline._selfprod()
            Dy = -self.ydiff * otherline._selfprod() - self._selfprod() * -otherline.ydiff
            if D != 0:
                x = Dx / D
                y = Dy / D
                return x,y
            else:
                return False
        else:
            # MANUAL APPROACH
            # http://stackoverflow.com/questions/18234049/determine-if-two-lines-intersect
            if self.slope == None:
                if otherline.slope == None:
                    return False
                ix = self.x1
                iy = ix*otherline.slope+otherline.zero_y
            elif otherline.slope == None:
                ix = otherline.x1
                iy = ix*self.slope+self.zero_y
            else:
                try:
                    ix = (otherline.zero_y-self.zero_y) / (self.slope-otherline.slope)
                except ZeroDivisionError:
                    #slopes are exactly the same so never intersect
                    return False
                iy = ix*self.slope+self.zero_y

            #check that intsec happens within bbox of both lines
            if ix >= min(self.x1,self.x2) and ix >= min(otherline.x1,otherline.x2)\
            and ix <= max(self.x1,self.x2) and ix <= max(otherline.x1,otherline.x2)\
            and iy >= min(self.y1,self.y2) and iy >= min(otherline.y1,otherline.y2)\
            and iy <= max(self.y1,self.y2) and iy <= max(otherline.y1,otherline.y2):
                return ix,iy
            else:
                return False
    def getlength(self):
        return math.hypot(self.xdiff,self.ydiff)
    def getangle(self):
        try:
            angle = math.degrees(math.atan(self.ydiff/float(self.xdiff)))
            if self.xdiff < 0:
                angle = 180 - angle
            else:
                angle *= -1
        except ZeroDivisionError:
            if self.ydiff < 0:
                angle = 90
            elif self.ydiff > 0:
                angle = -90
            else:
                raise TypeError("error: the vector isnt moving anywhere, so has no angle")
        return angle
    def getbuffersides(self, linebuffer):
        x1,y1,x2,y2 = self.x1,self.y1,self.x2,self.y2
        midline = _Line(x1,y1,x2,y2)
        angl = midline.getangle()
        perpangl_rad = math.radians(angl-90) #perpendicular angle in radians
        xbuff = linebuffer * math.cos(perpangl_rad)
        ybuff = linebuffer * math.sin(perpangl_rad)
        #xs
        leftx1 = (x1-xbuff)
        leftx2 = (x2-xbuff)
        rightx1 = (x1+xbuff)
        rightx2 = (x2+xbuff)
        #ys
        lefty1 = (y1+ybuff)
        lefty2 = (y2+ybuff)
        righty1 = (y1-ybuff)
        righty2 = (y2-ybuff)
        #return lines
        leftline = _Line(leftx1,lefty1,leftx2,lefty2)
        rightline = _Line(rightx1,righty1,rightx2,righty2)
        return leftline,rightline
    def anglebetween_rel(self, otherline):
        angl1 = self.getangle()
        angl2 = otherline.getangle()
        bwangl_rel = angl1-angl2 # - is left turn, + is right turn
        return bwangl_rel
    def anglebetween_abs(self, otherline):
        bwangl_rel = self.anglebetween_rel(otherline)
        angl1 = self.getangle()
        bwangl = angl1+bwangl_rel
        return bwangl
    def anglebetween_inv(self, otherline):
        bwangl = self.anglebetween_abs(otherline)
        if bwangl < 0:
            normangl = (180 + bwangl)/-2.0
        else:
            normangl = (180 - bwangl)/-2.0
        normangl = (180 + bwangl)/-2.0
        return normangl
    
    #INTERNAL USE ONLY
    def _selfprod(self):
        """
        Used by the line intersect method
        """
        return -(self.x1*self.y2 - self.x2*self.y1)
    
class _Bezier:
    def __init__(self, xypoints, intervals=100):
        # xys should be a sequence of 2-tuples (Bezier control points)
        def pascal_row(n):
            # This returns the nth row of Pascal's Triangle
            result = [1]
            x, numerator = 1, n
            for denominator in range(1, n//2+1):
                # print(numerator,denominator,x)
                x *= numerator
                x /= denominator
                result.append(x)
                numerator -= 1
            if n&1 == 0:
                # n is even
                result.extend(reversed(result[:-1]))
            else:
                result.extend(reversed(result)) 
            return result
        n = len(xypoints)
        combinations = pascal_row(n-1)
        ts = (t/float(intervals) for t in xrange(intervals+1))
        # This uses the generalized formula for bezier curves
        # http://en.wikipedia.org/wiki/B%C3%A9zier_curve#Generalization
        result = []
        for t in ts:
            tpowers = (t**i for i in range(n))
            upowers = reversed([(1-t)**i for i in range(n)])
            coefs = [c*a*b for c, a, b in zip(combinations, tpowers, upowers)]
            result.append(
                tuple(sum([coef*p for coef, p in zip(coefs, ps)]) for ps in zip(*xypoints)))
        self.coords = result

def _Arc(radius, start, end, clockwise=True):
    """
    Taken directly from: http://www.daniweb.com/software-development/python/threads/321181/python-bresenham-circle-arc-algorithm
    Python implementation of the modified Bresenham algorithm 
    for complete circles, arcs and pies
    radius: radius of the circle in pixels
    start and end are angles in degrees
    function will return a list of points (tuple coordinates)
    and the coordinates of the start and end point in a list xy
    """
    # round it to avoid rounding errors and wrong drawn pie slices
    start = math.radians(round(start))    
    end = math.radians(round(end))
    if start>=math.pi*2:
        start = math.radians(math.degrees(start)%360)
    if end>=math.pi*2:
        end = math.radians(math.degrees(end)%360)
    # always clockwise drawing, if anti-clockwise drawing desired
    # exchange start and end
    if not clockwise:
        s = start
        start = end
        end = s
    # determination which quarters and octants are necessary
    # init vars
    xy = [[0,0], [0,0]] # to locate actual start and end point for pies
    # the x/y border value for drawing the points
    q_x = []
    q_y = []
    # first q element in list q is quarter of start angle
    # second q element is quarter of end angle
    # now determine the quarters to compute
    q = []
    # 0 - 90 degrees = 12 o clock to 3 o clock = 0.0 - math.pi/2 --> q==1
    # 90 - 180 degrees = math.pi/2 - math.pi --> q==2
    # 180 - 270 degrees = math.pi - math.pi/2*3 --> q==3
    # 270 - 360 degrees = math.pi/2*3 - math.pi*2 --> q==4
    j = 0
    for i in [start, end]:
        angle = i
        if angle<math.pi/2:
            q.append(1)
            # compute the minimum x and y-axis value for plotting
            q_x.append(int(round(math.sin(angle)*radius)))
            q_y.append(int(round(math.cos(angle)*radius)))
            if j==1 and angle==0:
                xy[1] = [0,-radius] # 90 degrees 
        elif angle>=math.pi/2 and angle<math.pi:
            q.append(2)
            # compute the minimum x and y-axis value for plotting
            q_x.append(int(round(math.cos(angle-math.pi/2)*radius)))
            q_y.append(int(round(math.sin(angle-math.pi/2)*radius)))
            if j==1 and angle==math.pi/2:
                xy[1] = [radius,0] # 90 degrees
        elif angle>=math.pi and angle<math.pi/2*3:
            q.append(3)
            # compute the minimum x and y-axis value for plotting
            q_x.append(int(round(math.sin(angle-math.pi)*radius)))
            q_y.append(int(round(math.cos(angle-math.pi)*radius)))
            if j==1 and angle==math.pi:
                xy[1] = [0, radius]
        else:
            q.append(4)
            # compute the minimum x and y-axis value for plotting
            q_x.append(int(round(math.cos(angle-math.pi/2*3)*radius)))
            q_y.append(int(round(math.sin(angle-math.pi/2*3)*radius)))
            if j==1 and angle==math.pi/2*3:
                xy[1] = [-radius, 0]
        j = j + 1
    # print "q", q, "q_x", q_x, "q_y", q_y
    quarters = []
    sq = q[0]
    while 1:
        quarters.append(sq)
        if q[1] == sq and start<end or q[1] == sq and start>end and q[0]!=q[1]:
            break # we reach the final end quarter
        elif q[1] == sq and start>end:
            quarters.extend([(sq+1)%5, (sq+2)%5, (sq+3)%5, (sq+4)%5])
            break
        else:
            sq = sq + 1
            if sq>4:
                sq = 1
    # print "quarters", quarters
    switch = 3 - (2 * radius)
    points = []
    points1 = set()
    points2 = set()
    points3 = set()
    points4 = set()
    # 
    x = 0
    y = int(round(radius))
    # first quarter/octant starts clockwise at 12 o'clock
    while x <= y:
        if 1 in quarters:
            if not (1 in q):
                # add all points of the quarter completely
                # first quarter first octant
                points1.add((x,-y))
                # first quarter 2nd octant
                points1.add((y,-x))
            else:
                # start or end point in this quarter?
                if q[0] == 1: 
                    # start point
                    if q_x[0]<=x and q_y[0]>=abs(-y) and len(quarters)>1 or q_x[0]<=x and q_x[1]>=x:
                        # first quarter first octant
                        points1.add((x,-y))
                        if -y<xy[0][1]:
                            xy[0] = [x,-y]
                        elif -y==xy[0][1]:
                            if x<xy[0][0]:
                                xy[0] = [x,-y]
                    if q_x[0]<=y and q_y[0]>=x and len(quarters)>1 or q_x[0]<=y and q_x[1]>=y and q_y[0]>=abs(-x) and q_y[1]<=abs(-x):
                        # first quarter 2nd octant
                        points1.add((y,-x))
                        if -x<xy[0][1]:
                            xy[0] = [y,-x]
                        elif -x==xy[0][1]:
                            if y<xy[0][0]:
                                xy[0] = [y,-x]
                if q[1] == 1:
                    # end point
                    if q_x[1]>=x and len(quarters)>1 or q_x[0]<=x and q_x[1]>=x:
                        # first quarter first octant
                        points1.add((x,-y))
                        if x>xy[1][0]:
                            xy[1] = [x,-y]
                        elif x==xy[1][0]:
                            if -y>xy[1][1]:
                                xy[1] = [x,-y]
                    if q_x[1]>=y and q_y[1]<=x and len(quarters)>1 or q_x[0]<=y and q_x[1]>=y and q_y[0]>=abs(-x) and q_y[1]<=abs(-x):
                        # first quarter 2nd octant
                        points1.add((y,-x))
                        if y>xy[1][0]:
                            xy[1] = [y,-x]
                        elif y==xy[1][0]:
                            if -x>xy[1][1]:
                                xy[1] = [y,-x]
        if 2 in quarters:
            if not (2 in q):
                # add all points of the quarter completely
                # second quarter 3rd octant
                points2.add((y,x))
                # second quarter 4.octant
                points2.add((x,y))
            else:
                # start or end point in this quarter?
                if q[0] == 2: 
                    # start point
                    if q_x[0]>=y and q_y[0]<=x and len(quarters)>1 or q_x[0]>=y and q_x[1]<=y and q_y[0]<=x and q_y[1]>=x:
                        # second quarter 3rd octant
                        points2.add((y,x))
                        if y>xy[0][0]:
                            xy[0] = [y,x]
                        elif y==xy[0][0]:
                            if x<xy[0][1]:
                                xy[0] = [y,x]
                    if q_x[0]>=x and q_y[0]<=y and len(quarters)>1 or q_x[0]>=x and q_x[1]<=x and q_y[0]<=y and q_y[1]>=y:
                        # second quarter 4.octant
                        points2.add((x,y))
                        if x>xy[0][0]:
                            xy[0] = [x,y]
                        elif x==xy[0][0]:
                            if y<xy[0][1]:
                                xy[0] = [x,y]                        
                if q[1] == 2:
                    # end point
                    if q_x[1]<=y and q_y[1]>=x and len(quarters)>1 or q_x[0]>=y and q_x[1]<=y and q_y[0]<=x and q_y[1]>=x:
                        # second quarter 3rd octant
                        points2.add((y,x))
                        if x>xy[1][1]:
                            xy[1] = [y,x]
                        elif x==xy[1][1]:
                            if y<xy[1][0]:
                                xy[1] = [y,x]
                    if q_x[1]<=x and q_y[1]>=y and len(quarters)>1 or q_x[0]>=x and q_x[1]<=x and q_y[0]<=y and q_y[1]>=y:
                        # second quarter 4.octant
                        points2.add((x,y))
                        if y>xy[1][1]:
                            xy[1] = [x,y]
                        elif x==xy[1][1]:
                            if x<xy[1][0]:
                                xy[1] = [x,y]
        if 3 in quarters:    
            if not (3 in q):
                # add all points of the quarter completely
                # third quarter 5.octant
                points3.add((-x,y))        
                # third quarter 6.octant
                points3.add((-y,x))
            else:
                # start or end point in this quarter?
                if q[0] == 3:
                    # start point
                    if q_x[0]<=x and q_y[0]>=abs(y) and len(quarters)>1 or q_x[0]<=x and q_x[1]>=x:
                        # third quarter 5.octant
                        points3.add((-x,y))
                        if y>xy[0][1]:
                            xy[0] = [-x,y]
                        elif y==xy[0][1]:
                            if -x>xy[0][0]:
                                xy[0] = [-x,y]                        
                    if q_x[0]<=y and q_y[0]>=x and len(quarters)>1 or q_x[0]<=y and q_x[1]>=y and q_y[0]>=x and q_y[1]<=x:
                        # third quarter 6.octant
                        points3.add((-y,x))
                        if x>xy[0][1]:
                            xy[0] = [-y,x]
                        elif x==xy[0][1]:
                            if -y>xy[0][0]:
                                xy[0] = [-y,x]                                                
                if q[1] == 3:
                    # end point
                    if q_x[1]>=x and len(quarters)>1 or q_x[0]<=x and q_x[1]>=x:
                        # third quarter 5.octant
                        points3.add((-x,y))
                        if -x<xy[1][0]:
                            xy[1] = [-x,y]
                        elif -x==xy[1][0]:
                            if y<xy[1][1]:
                                xy[1] = [-x,y]
                    if q_x[1]>=y and q_y[1]<=x and len(quarters)>1 or q_x[0]<=y and q_x[1]>=y and q_y[0]>=x and q_y[1]<=x:
                        # third quarter 6.octant
                        points3.add((-y,x))
                        if -y<xy[1][0]:
                            xy[1] = [-y,x]
                        elif -y==xy[1][0]:
                            if x<xy[1][1]:
                                xy[1] = [-y,x]                        
        if 4 in quarters:
            if not (4 in q):
                # add all points of the quarter completely
                # fourth quarter 7.octant
                points4.add((-y,-x))
                # fourth quarter 8.octant
                points4.add((-x,-y))
            else:
                # start or end point in this quarter?
                if q[0] == 4: 
                    # start point
                    if q_x[0]>=y and q_y[0]<=x and len(quarters)>1 or q_x[0]>=y and q_x[1]<=y and q_y[0]<=x and q_y[1]>=x:
                        # fourth quarter 7.octant
                        points4.add((-y,-x))
                        if -y<xy[0][0]:
                            xy[0] = [-y,-x]
                        elif -y==xy[0][0]:
                            if -x>xy[0][1]:
                                xy[0] = [-y,-x]
                    if q_x[0]>=x and q_y[0]<=abs(-y) and len(quarters)>1 or q_x[0]>=x and q_x[1]<=x and q_y[0]<=y and q_y[1]>=y:
                        # fourth quarter 8.octant
                        points4.add((-x,-y))
                        if -x<xy[0][0]:
                            xy[0] = [-x,-y]
                        elif -x==xy[0][0]:
                            if -y>xy[0][1]:
                                xy[0] = [-x,-y]
                if q[1] == 4:
                    # end point
                    if q_x[1]<=y and q_y[1]>=x and len(quarters)>1 or q_x[0]>=y and q_x[1]<=y  and q_y[0]<=x and q_y[1]>=x:
                        # fourth quarter 7.octant
                        points4.add((-y,-x))
                        if -x<xy[1][1]:
                            xy[1] = [-y,-x]
                        elif -x==xy[1][1]:
                            if -y>xy[1][0]:
                                xy[1] = [-y,-x]
                    if q_x[1]<=x and q_y[1]>=abs(-y) and len(quarters)>1 or q_x[0]>=x and q_x[1]<=x and q_y[0]<=y and q_y[1]>=y:
                        # fourth quarter 8.octant
                        points4.add((-x,-y))
                        if -y<xy[1][1]:
                            xy[1] = [-x,-y]
                        elif -y==xy[1][1]:
                            if -x>xy[1][0]:
                                xy[1] = [-x,-y]
        if switch < 0:
            switch = switch + (4 * x) + 6
        else:
            switch = switch + (4 * (x - y)) + 10
            y = y - 1
        x = x + 1
    if 1 in quarters:
        points1_s = list(points1)
        # points1_s.sort() # if for some reason you need them sorted
        points.extend(points1_s)
    if 2 in quarters:
        points2_s = list(points2)
        # points2_s.sort() # if for some reason you need them sorted
        # points2_s.reverse() # # if for some reason you need in right order
        points.extend(points2_s)
    if 3 in quarters:        
        points3_s = list(points3)
        # points3_s.sort()
        # points3_s.reverse()
        points.extend(points3_s)
    if 4 in quarters:    
        points4_s = list(points4)
        # points4_s.sort()
        points.extend(points4_s)
    return points #, xy
