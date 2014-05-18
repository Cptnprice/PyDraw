"""
PyDraw
v0.1

## Introduction
PyDraw is a pure-Python drawing library.
The reason for making this library was to experiment with new drawing features to
merge with the pure-Python "Pymaging" library. But since Pymaging still hasn't 
been released in a working-version aimed for end-users, I'm just releasing this as a separate 
package until it can hopefully be incorporated into the Pymaging library later on.
PyDraw might also be interesting in itself since it incredibly lightweight,
straightforward to use, and provides not only basic drawing but also some
advanced features. One of the joys of it being pure-Python is that it becomes
fairly easy and way more accessible for even novice Python programmers to
experiment with and extend its drawing functionality and routines. 
Main features include:

- uses similar drawing commands to those used in PIL and Aggdraw
- the user can draw on a new empty image, open an existing one, and save the image to file
- draws various graphical primitives:
  - lines
  - circles
  - multilines
  - polygons
  - bezier curves
- drawings uses antialising (smooth sub-pixel precision)
- offers exact and fuzzy floodfill coloring of large areas (however, fuzzy floodfill is currently way too slow to be used)
- can also transform images
  - perspective transform, ie 3d tilting of an image
  - sphere/stereographic transform, ie 3d globe effect (partially working, partially not)

The main backdraws currently are:

- only support for reading/writing gif images, and if you use to many colors the gif image won't save
- while transparent gif images can be read, transparency will not be saved (becomes black)
- not as fast as C-based libraries (on average 10x slower)
- not a stable version yet, so several lacking features and errors (see Status below)

## Basic Usage
A typical example of how to use it would be:

```
import pydraw
img = pydraw.Image().new(width=500,height=500)
img.drawbezier([(22,22),(88,88),(188,22),(333,88)], fillcolor=(222,0,0))
img.drawcircle(333,111,fillsize=55,outlinecolor=(222,222,0))
img.drawline(0,250,499,250, fillcolor=(222,222,222))
img.floodfill(444,444,fillcolor=(0,222,0))
img.floodfill(222,222,fillcolor=(0,0,222))
img.view()
```

## Requires:
No dependencies; everything is written with the standard builtin Python library.
This is mainly thanks to the basic read-write capabilities of the Tkinter PhotoImage class.
Also tested to work on both Python 2.x and 3.x. 

## Status:
Main features are working okay so should be able to be used by end-users.
However, still in its most basic alpha-version, which means there may be many bugs. 
But most importantly it is lacking a few crucial drawing features,
which will be added in the future, such as:

- None of the primitives are being filled correctly (so drawing is limited to outlines)
- Thick multilines and thick polygon outlines appear choppy, need to add smooth join rules
- Lines need to be capped at their ends, with option for rounded caps
- Need more basic image transforms, such as rotate and flip
- Support for saving transparency, and drawing partially transparent colors
- Support for various color formats besides RGB (such as hex or colornames)
- And most importantly, more image formats

## License:
This code is free to share, use, reuse, and modify according to the MIT license, see license.txt

## Credits:
Karim Bahgat (2014)
Several Stackoverflow posts have been helpful for adding certain features,
and in some cases the code has been taken directly from the posts.
In other cases help and code has been found on websites.
In all such cases, the appropriate credit is given in the code.

## Contributors
I welcome any efforts to contribute code, particularly for:

- optimizing for speed, particularly the floodfill algorithm and its fuzzy variant
- adding/improving/correcting any rendering algorithms
- improve the quality of antialiasing, is currently still somewhat choppy
- fixing why image transform results in weird ripples and holes in the images
- adding new features (see Status above)

"""


import sys,os,math,operator,itertools


#PYTHON VERSION CHECKING
PYTHON3 = int(sys.version[0]) == 3
if PYTHON3:
    xrange = range
    import tkinter as tk
else:
    import Tkinter as tk


#THE CLASSES
class Image(object):

    #STARTING
    def new(self,width,height,background=None):
        """
        Creates and returns a new image instance.

        | **option** | **description**
        | --- | --- 
        | width | the width of the image in pixels, integer
        | height | the height of the image in pixels, integer
        | *background | an RGB color tuple to use as the background for the image, default is white/grayish.
        
        """
        self.width = width
        self.height = height
        if not background:
            background = (200,200,200)
        horizline = [background for _ in xrange(width)]
        self.imagegrid = [list(horizline) for _ in xrange(height)]
        return self
    def load(self, filepath=None, data=None):
        """
        Loads an existing image, either from a file,
        or from a list of lists containing RGB color tuples.
        If both are provided, the filepath will be used.

        | **option** | **description**
        | --- | --- 
        | *filepath | the string path of the image file to load, with extension
        | *data | a list of lists containing RGB color tuples
        
        """
        if filepath:
            tempwin = tk.Tk()
            tempimg = tk.PhotoImage(file=filepath)
            data = [[tuple([int(spec) for spec in tempimg.get(x,y).split()])
                    for x in xrange(tempimg.width())]
                    for y in xrange(tempimg.height())]
            self.width = len(data[0])
            self.height = len(data)
            self.imagegrid = data
        elif data:
            self.width = len(data[0])
            self.height = len(data)
            self.imagegrid = data
        return self

    #TRANSFORM
##    def rotate(self):
##        """
##        not working yet
##        """
##        self.imagegrid = [list(each) for each in zip(*listoflists)]
##        #and update width/height
    def spheremapping(self, sphereradius, xoffset=0, yoffset=0, zdist=0):
        """
        Map the image onto a 3d globe-like sphere.
        Return a new transformed image instance.
        Note: still work in progress, not fully correct.

        | **option** | **description**
        | --- | --- 
        | sphereradius | the radius of the sphere to wrap the image around in pixel integers
        | xoffset/yoffset/zdist | don't use, not working properly

        """
        #what happens is that the entire output image is like a window looking out on a globe from a given dist and angle, and the original image is like a sheet of paper filling the window and then gets sucked and wrapped from its position directly onto the globe, actually the origpic does not necessarily originate from the window/camera pos
        #need to figure out viewopening and viewdirection
        #based on http://stackoverflow.com/questions/9604132/how-to-project-a-point-on-to-a-sphere
        #alternatively use: point = centervect + radius*(point-centervect)/(norm(point-centervect))

        #sphereboxwidth,sphereboxheight,sphereboxdepth = (sphereradius*2,sphereradius*2,sphereradius*2)
        midx,midy,midz = (sphereradius+xoffset,sphereradius+yoffset,sphereradius+zdist)
        def pixel2sphere(x,y,z):
            newx,newy,newz = (x-midx,y-midy,z-midz)
            newmagn = math.sqrt(newx*newx+newy*newy+newz*newz)
            try:
                scaledx,scaledy,scaledz = [(sphereradius/newmagn)*each for each in (newx,newy,newz)]
                newpoint = (scaledx+midx,scaledy+midy,scaledz+midz)
                return newpoint
            except ZeroDivisionError:
                pass
        newimg = Image().new(self.width,self.height)
        for y in xrange(len(self.imagegrid)):
            for x in xrange(len(self.imagegrid[0])):
                color = self.get(x,y)
                newpos = pixel2sphere(x,y,z=0)
                if newpos:
                    newx,newy,newz = newpos
                    newimg.put(int(newx),int(newy),color)
        return newimg
    def tilt(self, oldplane, newplane):
        """
        Performs a perspective transform, ie tilts it, and returns the transformed image.
        Note: it is not very obvious how to set the oldplane and newplane arguments
        in order to tilt an image the way one wants. Need to make the arguments more
        user-friendly and handle the oldplane/newplane behind the scenes.
        Some hints on how to do that at http://www.cs.utexas.edu/~fussell/courses/cs384g/lectures/lecture20-Z_buffer_pipeline.pdf

        | **option** | **description**
        | --- | --- 
        | oldplane | a list of four old xy coordinate pairs
        | newplane | four points in the new plane corresponding to the old points

        """
##        oldplane = (0,0),(self.width,0),(self.width,self.height),(0,self.height)
##        nw,ne,se,sw = oldplane
##        nnw,nne,nse,nsw = (nw[0]-topdepth,nw[1]+topdepth),(ne[0]+topdepth,ne[1]+topdepth),se,sw
##        newplane = [nnw,nne,nse,nsw]
        #first find the transform coefficients, thanks to http://stackoverflow.com/questions/14177744/how-does-perspective-transformation-work-in-pil
        pb,pa = oldplane,newplane
        grid = []
        for p1,p2 in zip(pa, pb):
            grid.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            grid.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        import PyDraw.advmatrix as mt
        A = mt.Matrix(grid)
        B = mt.Vec([xory for xy in pb for xory in xy])
        AT = A.tr()
        ATA = AT.mmul(A)
        gridinv = ATA.inverse()
        invAT = gridinv.mmul(AT)
        res = invAT.mmul(B)
        transcoeff = res.flatten()
        #then calculate new coords, thanks to http://math.stackexchange.com/questions/413860/is-perspective-transform-affine-if-it-is-why-its-impossible-to-perspective-a"
        k = 1
        a,b,c,d,e,f,g,h = transcoeff
        outimg = Image().new(self.width,self.height)
        for y in xrange(len(self.imagegrid)):
            for x in xrange(len(self.imagegrid[0])):
                color = self.get(x,y)
                newx = int(round((a*x+b*y+c)/float(g*x+h*y+k)))
                newy = int(round((d*x+e*y+f)/float(g*x+h*y+k)))
                try:
                    outimg.put(newx,newy,color)
                    #print x,y,newx,newy
                except IndexError:
                    #out of bounds
                    pass
        return outimg

    #DRAWING
    def get(self,x,y):
        """
        Get the color of pixel at specified xy position.
        Note: mostly used internally, but may sometimes be useful for end-user too.

        | **option** | **description**
        | --- | --- 
        | x/y | width/height position of the pixel to retrieve, with 0,0 being in topleft corner
        
        """
        rgb = self.imagegrid[y][x]
        return rgb
    
    def put(self,x,y,color):
        """
        Set the color of a pixel at specified xy position.
        Note: mostly used internally, but may sometimes be useful for end-user too.

        | **option** | **description**
        | --- | --- 
        | x/y | width/height position of the pixel to set, with 0,0 being in topleft corner
        | color | RGB color tuple to set to the pixel

        """
        #if floating xy coords, make into semitransparent colors
        if isinstance(x, float) or isinstance(y, float):
            #calc values
            xint,yint = int(x), int(y)
            xfloat,yfloat = x-xint, y-yint
            if xfloat:
                x1,x2 = xint,xint+1
                x1transp,x2transp = 1-xfloat,xfloat
            if yfloat:
                y1,y2 = yint,yint+1
                y1transp,y2transp = 1-yfloat,yfloat
            #allow transp color
            if len(color)==3:
                r,g,b = color
                color = (r,g,b,255)
            #disperse pixels
            if xfloat and yfloat:
                newcolor = (color[0],color[1],color[2],color[3]*x1transp*y1transp)
                self.put(x1,y1,newcolor)
                newcolor = (color[0],color[1],color[2],color[3]*x1transp*y2transp)
                self.put(x1,y2,newcolor)
                newcolor = (color[0],color[1],color[2],color[3]*x2transp*y1transp)
                self.put(x2,y1,newcolor)
                newcolor = (color[0],color[1],color[2],color[3]*x2transp*y2transp)
                self.put(x2,y2,newcolor)
            elif xfloat:
                newcolor = (color[0],color[1],color[2],color[3]*x1transp)
                self.put(x1,yint,newcolor)
                newcolor = (color[0],color[1],color[2],color[3]*x2transp)
                self.put(x2,yint,newcolor)
            elif yfloat:
                newcolor = (color[0],color[1],color[2],color[3]*y1transp)
                self.put(xint,y1,newcolor)
                newcolor = (color[0],color[1],color[2],color[3]*y2transp)
                self.put(xint,y2,newcolor)
            return
        #or plot normal whole pixels
        elif len(color)==3:
            #solid color
            pass
        elif len(color)==4:
            #transparent color, blend with background
            t = color[3]/255.0
            p = self.get(int(x),int(y))
            color = (int((p[0]*(1-t)) + color[0]*t), int((p[1]*(1-t)) + color[1]*t), int((p[2]*(1-t)) + color[2]*t))
        #finally draw it
        try: self.imagegrid[y][x] = color
        except IndexError:
            pass #pixel outside img boundary
        
    def drawline(self, x1, y1, x2, y2, fillcolor=None, outlinecolor=(0,0,0), fillsize=1, outlinewidth=1, capstyle="butt"): #, bendfactor=None, bendside=None, bendanchor=None):
        """
        Draws a single line.

        | **option** | **description**
        | --- | --- 
        | x1,y1,x2,y2 | start and end coordinates of the line, integers
        | *fillcolor | RGB color tuple to fill the body of the line with (currently not working)
        | *outlinecolor | RGB color tuple to fill the outline of the line with, default is no outline
        | *fillsize | the thickness of the main line, as pixel integers
        | *outlinewidth | the width of the outlines, as pixel integers
        
        """
##        maybe add these options in future
##        - bendfactor is strength/how far out the curve should extend from the line
##        - bendside is left or right side to bend
##        - bendanchor is the float ratio to offset the bend from its default anchor point at the center of the line.
        
        #decide to draw single or thick line with outline
        if fillsize <= 1:
            #draw single line
            self._drawsimpleline(x1, y1, x2, y2, col=fillcolor, thick=fillsize)
        else:
            if outlinecolor or fillcolor:
                linepolygon = []
                #get orig params
                buff = fillsize/2.0
                xchange = x2-x1
                ychange = y2-y1
                try:
                    origslope = ychange/float(xchange)
                except ZeroDivisionError:
                    origslope = ychange
                angl = math.degrees(math.atan(origslope))
                perpangl_rad = math.radians(angl-90) #perpendicular angle in radians
                xbuff = buff * math.cos(perpangl_rad)
                ybuff = buff * math.sin(perpangl_rad)
                #leftline
                leftx1,leftx2 = (x1-xbuff,x2-xbuff)
                lefty1,lefty2 = (y1-ybuff,y2-ybuff)
                leftlinecoords = (leftx1,lefty1,leftx2,lefty2)
                #rightline
                rightx1,rightx2 = (x1+xbuff,x2+xbuff)
                righty1,righty2 = (y1+ybuff,y2+ybuff)
                rightlinecoords = (rightx2,righty2,rightx1,righty1)
                #finally draw the thick line as a polygon
                if capstyle == "butt":
                    linepolygon.extend(leftlinecoords)
                    linepolygon.extend(rightlinecoords)
                    def groupby2(iterable):
                        args = [iter(iterable)] * 2
                        return itertools.izip(*args)
                    linepolygon = list(groupby2(linepolygon))
                    self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
                elif capstyle == "round":
                    #left side
                    linepolygon.extend(leftlinecoords)
                    #right round tip
                    ytipbuff = buff*2 * math.sin(math.radians(angl))
                    xtipbuff = buff*2 * math.cos(math.radians(angl))
                    xtipright = x2+xtipbuff
                    ytipright = y2+ytipbuff
                    roundcurve = _Bezier([leftlinecoords[-2:],(xtipright,ytipright),rightlinecoords[:2]], intervals=buff)
                    def flatten(iterable):
                        return itertools.chain.from_iterable(iterable)
                    linepolygon.extend(list(flatten(roundcurve.coords)))
                    #right side
                    linepolygon.extend(rightlinecoords)
                    #left round tip
                    xtipleft = x1-xtipbuff
                    ytipleft = y1-ytipbuff
                    roundcurve = _Bezier([rightlinecoords[-2:],(xtipleft,ytipleft),leftlinecoords[:2]], intervals=buff)
                    def flatten(iterable):
                        return itertools.chain.from_iterable(iterable)
                    linepolygon.extend(list(flatten(roundcurve.coords)))
                    #draw as polygon
                    def groupby2(iterable):
                        args = [iter(iterable)] * 2
                        return itertools.izip(*args)
                    linepolygon = list(groupby2(linepolygon))
                    self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
                elif capstyle == "projecting":
                    #left side
                    ytipbuff = buff * math.sin(math.radians(angl))
                    xtipbuff = buff * math.cos(math.radians(angl))
                    linepolygon.extend([leftx2+xtipbuff, lefty2+ytipbuff, leftx1+xtipbuff, lefty1+ytipbuff])
                    #right side
                    linepolygon.extend([rightx1+xtipbuff, righty1+ytipbuff, rightx2+xtipbuff, righty2+ytipbuff])
                    #draw as polygon
                    def groupby2(iterable):
                        args = [iter(iterable)] * 2
                        return itertools.izip(*args)
                    linepolygon = list(groupby2(linepolygon))
                    self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)

    def drawmultiline(self, coords, fillcolor=None, outlinecolor=(0,0,0), fillsize=1, outlinewidth=1, joinstyle="miter"): #, bendfactor=None, bendside=None, bendanchor=None):
        """
        Draws multiple lines between a list of coordinates, useful for making them connect together.
        
        | **option** | **description**
        | --- | --- 
        | coords | list of coordinate point pairs to be connected by lines
        | **other | also accepts various color and size arguments, see the docstring for drawline.
        """
        buff = fillsize/2.0
        def threewise(iterable):
            a,_ = itertools.tee(iterable)
            b,c = itertools.tee(_)
            next(b, None)
            next(c, None)
            next(c, None)
            return itertools.izip(a,b,c)
        if joinstyle == "miter":
            #sharp
            linepolygon_left = []
            linepolygon_right = []
            buffersize = fillsize/2.0
            #the first line
            (x1,y1),(x2,y2),(x3,y3) = coords[:3]
            line1 = _Line(x1,y1,x2,y2)
            line2 = _Line(x2,y2,x3,y3)
            leftline,rightline = line1.getbuffersides(linebuffer=buffersize)
            leftlinestart = leftline.tolist()[0]
            rightlinestart = rightline.tolist()[0]
            linepolygon_left.append(leftlinestart)
            linepolygon_right.append(rightlinestart)
            #then all mid areas
            for start,mid,end in threewise(coords):
                (x1,y1),(x2,y2),(x3,y3) = start,mid,end
                line1 = _Line(x1,y1,x2,y2)
                line2 = _Line(x2,y2,x3,y3)
                line1_left,line1_right = line1.getbuffersides(linebuffer=buffersize)
                line2_left,line2_right = line2.getbuffersides(linebuffer=buffersize)
                midleft = line1_left.intersect(line2_left, infinite=True)
                midright = line1_right.intersect(line2_right, infinite=True)
                #add coords
                linepolygon_left.append(midleft)
                linepolygon_right.append(midright)
            #finally add last line coords
            (x1,y1),(x2,y2) = coords[-2:]
            lastline = _Line(x1,y1,x2,y2)
            leftline,rightline = lastline.getbuffersides(linebuffer=buffersize)
            leftlinestart = leftline.tolist()[1]
            rightlinestart = rightline.tolist()[1]
            linepolygon_left.append(leftlinestart)
            linepolygon_right.append(rightlinestart)
            #draw as polygon
            linepolygon = []
            linepolygon.extend(linepolygon_left)
            linepolygon.extend(list(reversed(linepolygon_right)))
            self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
        elif joinstyle == "round":
            pass
        elif joinstyle == "bevel":
            #flattened
            pass
        elif joinstyle == None:
            for index in xrange(len(coords)-1):
                start,end = coords[index],coords[index+1]
                linecoords = list(start)
                linecoords.extend(list(end))
                self.drawline(*linecoords, fillcolor=fillcolor, outlinecolor=outlinecolor, fillsize=fillsize)
        
    def _drawsimpleline(self, x1, y1, x2, y2, col, thick):
        """
        backend being used internally, holds the basic line algorithm, including antialiasing.
        taken and modified from a Stackoverflow post...
        appears to be a bit jagged, not as smooth as preferred, so
        need to look into how to improve/fix it.
        Note: the "col" argument is the color tuple of the line.
        """
        def plot(x, y, c, col,steep):
            if steep:
                x,y = y,x
            #not entirely satisfied with quality yet, does some weird stuff when overlapping
            #p = self.get(int(x),int(y))
            newtransp = c*255*thick #int(col[3]*c)
            newcolor = (col[0], col[1], col[2], newtransp)
            #newcolor = (int((p[0]*(1-c)) + col[0]*c), int((p[1]*(1-c)) + col[1]*c), int((p[2]*(1-c)) + col[2]*c))
            self.put(int(x),int(y),newcolor)

        def iround(x):
            return ipart(x + 0.5)

        def ipart(x):
            return math.floor(x)

        def fpart(x):
            return x-math.floor(x)

        def rfpart(x):
            return 1 - fpart(x)
        
        dx = x2 - x1
        dy = y2 - y1

        steep = abs(dx) < abs(dy)
        if steep:
            x1,y1=y1,x1
            x2,y2=y2,x2
            dx,dy=dy,dx
        if x2 < x1:
            x1,x2=x2,x1
            y1,y2=y2,y1
        try:
            gradient = float(dy) / float(dx)
        except ZeroDivisionError:
            gradient = float(dy)

        #handle first endpoint
        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = rfpart(x1 + 0.5)
        xpxl1 = xend    #this will be used in the main loop
        ypxl1 = ipart(yend)
        plot(xpxl1, ypxl1, rfpart(yend)*xgap, col, steep)
        plot(xpxl1, ypxl1 + 1, fpart(yend)*xgap, col, steep)
        intery = yend + gradient # first y-intersection for the main loop

        #handle second endpoint
        xend = round(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = fpart(x2 + 0.5)
        xpxl2 = xend    # this will be used in the main loop
        ypxl2 = ipart(yend)
        plot(xpxl2, ypxl2, rfpart(yend)*xgap, col, steep)
        plot(xpxl2, ypxl2 + 1, fpart(yend)*xgap, col, steep)

        #main loop
        for x in xrange(int(xpxl1 + 1), int(xpxl2 )):
            ybase = int(intery)
            ydeci = intery-int(intery)
            plot(x, ybase, 1-ydeci, col, steep)
            plot(x, ybase+1, ydeci, col, steep)
            intery = intery + gradient

    def drawbezier(self, xypoints, fillcolor=(0,0,0), outlinecolor=None, fillsize=1, intervals=100):
        """
        Draws a bezier curve given a list of coordinate control point pairs.
        Mostly taken directly from a stackoverflow post...
        
        | **option** | **description**
        | --- | --- 
        | xypoints | list of coordinate point pairs, at least 3. The first and last points are the endpoints, and the ones in between are control points used to inform the curvature.
        | **other | also accepts various color and size arguments, see the docstring for drawline.
        | *intervals | how finegrained/often the curve should be bent, default is 100, ie curves every one percent of the line.
        
        """
        curve = _Bezier(xypoints, intervals)
        self.drawmultiline(curve.coords, fillcolor=fillcolor, outlinecolor=outlinecolor, fillsize=fillsize)

    def drawcircle(self, x, y, fillsize, fillcolor=None, outlinecolor=(0,0,0), outlinewidth=1): #, flatten=None, flatangle=None):
        """
        Draws a circle at specified centerpoint.
        
        | **option** | **description**
        | --- | --- 
        | x/y | the integer x/y position to be the midpoint of the circle.
        | fillsize | required to specify the fillsize of the circle, as pixel integers
        | **other | also accepts various color and size arguments, see the docstring for drawline.
        
        """
        #later on add ability to make that circle an ellipse with these args:
        #flatten=...
        #flatangle=...

        #alternative circle algorithms
        #http://stackoverflow.com/questions/1201200/fast-algorithm-for-drawing-filled-circles
        #http://willperone.net/Code/codecircle.php
        #http://www.mathopenref.com/coordcirclealgorithm.html
        
        #use bezier circle path
        size = fillsize
        c = 0.55191502449*size #0.55191502449 http://spencermortensen.com/articles/bezier-circle/ #alternative nr: 0.551784 http://www.tinaja.com/glib/ellipse4.pdf
        relcontrolpoints = [(0,size),(c,size),(size,c),
                 (size,0),(size,-c),(c,-size),
                 (0,-size),(-c,-size),(-size,-c),
                 (-size,0),(-size,c),(-c,size),(0,size)]
        circlepolygon = []
        oldindex = 1
        for index in xrange(4):
            cornerpoints = relcontrolpoints[oldindex-1:oldindex+3]
            cornerpoints = [(x+relx,y+rely) for relx,rely in cornerpoints]
            #self.drawbezier(cornerpoints, fillsize=outlinewidth, fillcolor=outlinecolor, outlinecolor=None, intervals=int(fillsize*20))
            circlepolygon.extend(_Bezier(cornerpoints, intervals=int(fillsize*3)).coords)
            oldindex += 3
        #then draw and fill as polygon
        self.drawpolygon(circlepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
  
    def drawpolygon(self, coords, fillcolor=None, outlinecolor=(255,255,255), outlinewidth=1):
        """
        Draws a polygon based on input coordinates.
        Note: as with other primitives, fillcolor does not work properly.
        
        | **option** | **description**
        | --- | --- 
        | coords | list of coordinate point pairs that make up the polygon. Automatically detects whether to enclose the polygon.
        | **other | also accepts various color and size arguments, see the docstring for drawline.
        
        """
        #maybe autocomplete polygon
        if coords[-1] != coords[0]:
            coords = list(coords)
            coords.append(coords[0])
        #first fill insides of polygon
        if fillcolor:
            def pairwise(iterable):
                a,b = itertools.tee(iterable)
                next(b, None)
                return itertools.izip(a,b)
            def flatten(iterable):
                return itertools.chain.from_iterable(iterable)
            def groupby2(iterable):
                args = [iter(iterable)] * 2
                return itertools.izip(*args)
            #main
            ysortededges = [ list(flatten(sorted(eachedge, key=operator.itemgetter(1)))) for eachedge in pairwise(coords) ]
            ysortededges = list(sorted(ysortededges, key=operator.itemgetter(1)))
            edgeindex = 0
            curedge = ysortededges[edgeindex]
            checkedges = []
            #get bbox
            xs, ys = zip(*coords)
            bbox = [min(xs), min(ys), max(xs), max(ys)]
            #begin
            xmin,ymin,xmax,ymax = bbox
            for y in xrange(ymin,ymax+1):
                fillxs = []
                #collect relevant edges
                "first from previous old ones"
                tempcollect = [tempedge for tempedge in checkedges if tempedge[3] > y]
                "then from new ones"
                while curedge[1] <= y and edgeindex < len(ysortededges):
                    tempcollect.append(curedge)
                    edgeindex += 1
                    try:
                        curedge = ysortededges[edgeindex]
                    except IndexError:
                        break   #just to make higher
                if tempcollect:
                    checkedges = tempcollect
                #find intersect
                #print checkedges
                scanline = _Line(xmin,y,xmax,y)
                for edge in checkedges:
                    edge = _Line(*edge)
                    intersection = scanline.intersect(edge)
                    #print intersection, scanline.tolist(), edge.tolist()
                    if intersection:
                        ix,iy = intersection
                        fillxs.append(ix)
                #scan line and fill
                fillxs = sorted(fillxs)
                #print y, len(fillxs)#, checkedges
                if fillxs:
                    for fillmin,fillmax in groupby2(fillxs):
                        #print "\t",fillmin,fillmax
                        fillmin,fillmax = map(int,map(round,(fillmin,fillmax)))
                        for x in xrange(fillmin,fillmax+1):
                            self.put(x,y,fillcolor)
        #then draw outline
        if outlinecolor:
            self.drawmultiline(coords, fillcolor=outlinecolor, fillsize=outlinewidth, outlinecolor=None)

    def floodfill(self,x,y,fillcolor,fuzzythresh=1.0):
        """
        Fill a large area of similarly colored neighboring pixels to the color at the origin point.
        Adapted from http://inventwithpython.com/blog/2011/08/11/recursion-explained-with-the-flood-fill-algorithm-and-zombies-and-cats/comment-page-1/
        Note: needs to be optimized, bc now checks all neighbours multiple times regardless of whether checked before bc has no memory.
        Also, lowering the fuzzythreshhold is not a good idea as it is incredibly slow.

        | **option** | **description**
        | --- | --- 
        | x/t | the xy coordinate integers of where to begin the floodfill.
        | fillcolor | the new RGB color tuple to replace the old colors with
        
        """
        #test and fill all neighbouring cells
        fillcolor = list(fillcolor)
        colortofollow = self.get(x,y)
        sqrt = math.sqrt
        def notexactcolor(x,y):
            if self.get(x,y) != colortofollow:
                return True
        def notfuzzycolor(x,y):
            """based on W3 principles, http://www.had2know.com/technology/color-contrast-calculator-web-design.html
            but doesnt really work yet, super slow, likely due to the if bigger than test operation"""
            #r,g,b = self.get(x,y)
            #checkbrightness = ( 299*r + 587*g + 114*b )/1000
            #r,g,b = colortofollow
            #comparebrightness = ( 299*r + 587*g + 114*b )/1000
            #brightnessdiff = float(str((checkbrightness-comparebrightness)/255.0).replace("-",""))#sqrt(((checkbrightness-comparebrightness)/255.0)**2)
            main = self.get(x,y)
            compare = colortofollow
            colordiff = sum([spec[0]-spec[1] for spec in zip(main,compare)])/255.0
            if colordiff > fuzzythresh:
                return True
        if fuzzythresh == 1.0: reachedboundary = notexactcolor
        else: reachedboundary = notfuzzycolor
        theStack = [ (x, y) ]
        while len(theStack) > 0:
            x, y = theStack.pop()
            try:
                if reachedboundary(x,y):
                    continue
            except IndexError:
                continue
            self.put(x,y,fillcolor)
            theStack.append( (x + 1, y) )  # right
            theStack.append( (x - 1, y) )  # left
            theStack.append( (x, y + 1) )  # down
            theStack.append( (x, y - 1) )  # up

    #AFTERMATH
    def view(self):
        """
        Pops up a Tkinter window in which to view the image
        """
        window = tk.Tk()
        canvas = tk.Canvas(window, width=self.width, height=self.height)
        canvas.create_text((self.width/2, self.height/2), text="error\nviewing\nimage")
        self.tkimg = self._tkimage()
        canvas.create_image((self.width/2, self.height/2), image=self.tkimg, state="normal")
        canvas.pack()
        tk.mainloop()
    def updateview(self):
        """
        Updates the image in the Tkinter window to include recent changes to the image
        """
        self.tkimg = self._tkimage()
    def save(self, savepath):
        """
        Saves the image to the given filepath.

        | **option** | **description**
        | --- | --- 
        | filepath | the string path location to save the image. Extension must be given and can only be ".gif".
        
        """
        tempwin = tk.Tk() #only so dont get "too early to create image" error
        tkimg = self._tkimage()
        tkimg.write(savepath, "gif")
        tempwin.destroy()
        
    #INTERNAL USE ONLY
    def _tkimage(self):
        """
        Converts the image pixel matrix to a Tkinter Photoimage to allow viewing/saving.
        For internal use only.
        """
        tkimg = tk.PhotoImage(width=self.width, height=self.height)
        imgstring = " ".join(["{"+" ".join(["#%02x%02x%02x" %tuple(rgb) for rgb in horizline])+"}" for horizline in self.imagegrid])
        tkimg.put(imgstring)
        return tkimg

#INTERNAL HELPER CLASSES
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


if __name__ == "__main__":
    img = Image().new(100,100)
    img.put(94.7,94.7,(0,0,222))
    #img.put(95.7,98,(0,0,222))
    #img.put(98,95.7,(0,0,222))
    img.drawpolygon(coords=[(30,30),(90,10),(90,90),(10,90),(30,30)], fillcolor=(0,222,0), outlinecolor=(0,0,0))
    img.drawpolygon(coords=[(90,20),(80,20),(50,15),(20,44),(90,50),(50,90),(10,50),(30,20),(50,10)], fillcolor=(0,222,0), outlinecolor=(0,0,0),outlinewidth=4)
    #img.drawmultiline(coords=[(90,20),(80,20),(50,15),(20,44),(90,50),(50,90),(10,50),(30,20),(50,10)], fillcolor=(0,0,0), fillsize=8, outlinecolor=None, joinstyle="miter")
    ###img.drawmultiline(coords=[(10,50),(50,50),(50,90)], fillcolor=(0,0,0), fillsize=8, outlinecolor=None, joinstyle=None)
    ###img.drawmultiline(coords=[(10,50),(50,50),(90,55)], fillcolor=(0,111,0), fillsize=8, outlinecolor=None, joinstyle="miter")
    #img.drawline(22,11,88,77,fillcolor=(222,0,0),fillsize=8, capstyle="round")
    #img.drawline(22,66,88,77,fillcolor=(222,0,0,166),fillsize=11, capstyle="round")
    ##img.drawline(44,33,55,80,fillcolor=(222,0,0),fillsize=0.5)
    #img.drawbezier([(11,11),(90,40),(90,90)])
    #img.drawpolygon([(90,50),(90-5,50-5),(90+5,50+5),(90-5,50+5),(90,50)], fillcolor=(222,0,0))
    #img.drawcircle(50,50,fillsize=8, fillcolor=(222,222,0), outlinecolor=(0,0,222), outlinewidth=1)
    img.view()
    img.save("C:/Users/BIGKIMO/Desktop/hmm.gif")
