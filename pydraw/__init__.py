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

- only support for reading/writing gif images, and if you use too many colors the gif image won't save
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
#import submodules
import png
import geomhelper
from geomhelper import _Line, _Bezier, _Arc


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
            if filepath.endswith(".png"):
                #PNG
                reader = png.Reader(filename=filepath)
                width,height,pixels,metadata = reader.read()
                if metadata["alpha"]:
                    colorlength = 4
                else:
                    colorlength = 3
                data = []
                for pxlrow in pixels:
                    row = []
                    index = 0
                    while index < width*colorlength:
                        color = [pxlrow[index+spectrum] for spectrum in xrange(colorlength)]
                        color = color[:3] #this bc currently no support for alpha image values
                        row.append(color)
                        index += colorlength
                    data.append(row)
                self.width,self.height = width,height
                self.imagegrid = data
            elif filepath.endswith(".gif"):
                #GIF
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
        import pydraw.advmatrix as mt
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
        if x < 0 or y < 0:
            return
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
            try:
                p = self.get(int(x),int(y))
            except IndexError:
                return #pixel outside img boundary
            color = (int((p[0]*(1-t)) + color[0]*t), int((p[1]*(1-t)) + color[1]*t), int((p[2]*(1-t)) + color[2]*t))
        #finally draw it
        try: self.imagegrid[y][x] = color
        except IndexError:
            pass #pixel outside img boundary

    def pastedata(self, x, y, data, anchor="nw", transparency=0):
        """
        Pastes a list of lists of pixels onto the image at the specified position
        Note: for now, data has to be 3(rgb) tuples, not 4(rgba)
        and only nw anchor supported for now
        """
        dataheight = len(data)
        datawidth = len(data[0])
        alpha = 255*transparency
        if "n" in anchor:
            if "w" in anchor:
                datay = 0
                for puty in xrange(y,y+dataheight):
                    datax = 0
                    for putx in xrange(x,x+datawidth):
                        dpixel = data[datax][datay]
                        r,g,b = dpixel
                        dpixel = (r,g,b,alpha)
                        self.put(putx,puty,dpixel)
                        datax += 1
                    datay += 1
            
    def drawline(self, x1, y1, x2, y2, fillcolor=(0,0,0), outlinecolor=None, fillsize=1, outlinewidth=1, capstyle="butt"): #, bendfactor=None, bendside=None, bendanchor=None):
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

    def drawmultiline(self, coords, fillcolor=(0,0,0), outlinecolor=None, fillsize=1, outlinewidth=1, joinstyle="miter"): #, bendfactor=None, bendside=None, bendanchor=None):
        """
        Draws multiple lines between a list of coordinates, useful for making them connect together.
        
        | **option** | **description**
        | --- | --- 
        | coords | list of coordinate point pairs to be connected by lines
        | **other | also accepts various color and size arguments, see the docstring for drawline.
        """
        if fillsize <= 1:
            for index in xrange(len(coords)-1):
                start,end = coords[index],coords[index+1]
                linecoords = list(start)
                linecoords.extend(list(end))
                self.drawline(*linecoords, fillcolor=fillcolor, outlinecolor=outlinecolor, fillsize=fillsize)
        elif not joinstyle:
            for index in xrange(len(coords)-1):
                start,end = coords[index],coords[index+1]
                linecoords = list(start)
                linecoords.extend(list(end))
                self.drawline(*linecoords, fillcolor=fillcolor, outlinecolor=outlinecolor, fillsize=fillsize)
        else:
            #lines are thick so they have to be joined
            def threewise(iterable):
                a,_ = itertools.tee(iterable)
                b,c = itertools.tee(_)
                next(b, None)
                next(c, None)
                next(c, None)
                return itertools.izip(a,b,c)
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
            if joinstyle == "miter":
                #sharp join style
                for start,mid,end in threewise(coords):
                    (x1,y1),(x2,y2),(x3,y3) = start,mid,end
                    line1 = _Line(x1,y1,x2,y2)
                    line2 = _Line(x2,y2,x3,y3)
                    line1_left,line1_right = line1.getbuffersides(linebuffer=buffersize)
                    line2_left,line2_right = line2.getbuffersides(linebuffer=buffersize)
                    midleft = line1_left.intersect(line2_left, infinite=True)
                    midright = line1_right.intersect(line2_right, infinite=True)
                    if not midleft or not midright:
                        #PROB FLOAT ERROR,SO NO INTERSECTION FOUND
                        #CURRENTLY JUST SKIP DRAWING,BUT NEED BETTER HANDLING
                        return
                    #add coords
                    linepolygon = []
                    linepolygon.extend([linepolygon_left[-1],midleft])
                    linepolygon.extend([midright,linepolygon_right[-1]])
                    self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
                    linepolygon_left.append(midleft)
                    linepolygon_right.append(midright)
            elif joinstyle == "round":
                #round
                for start,mid,end in threewise(coords):
                    (x1,y1),(x2,y2),(x3,y3) = start,mid,end
                    line1 = _Line(x1,y1,x2,y2)
                    line2 = _Line(x2,y2,x3,y3)
                    line1_left,line1_right = line1.getbuffersides(linebuffer=buffersize)
                    line2_left,line2_right = line2.getbuffersides(linebuffer=buffersize)
                    midleft = line1_left.intersect(line2_left, infinite=True)
                    midright = line1_right.intersect(line2_right, infinite=True)
                    if not midleft or not midright:
                        #PROB FLOAT ERROR,SO NO INTERSECTION FOUND
                        #CURRENTLY JUST SKIP DRAWING,BUT NEED BETTER HANDLING
                        return
                    #ARC approach
                    ##midx,midy = x2,y2
                    ##oppositeangle = line1.anglebetween_inv(line2)
                    ##bwangle = line1.anglebetween_abs(line2)
                    ##leftangl,rightangl = oppositeangle-bwangle,oppositeangle+bwangle
                    ##leftcurve = _Arc(midx,midy,radius=buffersize,startangle=leftangl,endangle=rightangl)
                    ##rightcurve = _Arc(midx-buffersize,midy-buffersize,radius=buffersize,startangle=leftangl,endangle=rightangl) #[(midx,midy)] #how do inner arc?

                    leftcurve = _Bezier([line1_left.tolist()[1],midleft,line2_left.tolist()[0]], intervals=20).coords
                    rightcurve = _Bezier([line1_right.tolist()[1],midright,line2_right.tolist()[0]], intervals=20).coords
                    #add coords
                    linepolygon = []
                    linepolygon.append(linepolygon_left[-1])
                    linepolygon.extend(leftcurve)
                    linepolygon.extend(list(reversed(rightcurve)))
                    linepolygon.append(linepolygon_right[-1])
                    self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
                    linepolygon_left.extend(leftcurve)
                    linepolygon_right.extend(rightcurve)
            elif joinstyle == "bevel":
                #flattened
                pass
            #finally add last line coords
            (x1,y1),(x2,y2) = coords[-2:]
            lastline = _Line(x1,y1,x2,y2)
            leftline,rightline = lastline.getbuffersides(linebuffer=buffersize)
            leftlinestart = leftline.tolist()[1]
            rightlinestart = rightline.tolist()[1]
            
            linepolygon = []
            linepolygon.extend([linepolygon_left[-1],leftlinestart])
            linepolygon.extend([rightlinestart,linepolygon_right[-1]])
            self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
            ##linepolygon_left.append(leftlinestart)
            ##linepolygon_right.append(rightlinestart)
            
            #draw as polygon
            ##linepolygon = []
            ##linepolygon.extend(linepolygon_left)
            ##linepolygon.extend(list(reversed(linepolygon_right)))
            #self.drawpolygon(linepolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)
        
    def _drawsimpleline(self, x1, y1, x2, y2, col, thick=1):
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
            self.put(int(round(x)),int(round(y)),newcolor)

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
            #pure vertical line, so just draw it without antialias
            newtransp = 255*thick #int(col[3]*c)
            newcolor = (col[0], col[1], col[2], newtransp)
            for y in xrange(y1,y2+1):
                self.put(x1,y,newcolor)
            return

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
            ybase = math.floor(intery)
            ydeci = intery-ybase
            plot(x, ybase, 1-ydeci, col, steep)
            plot(x, ybase+1, ydeci, col, steep)
            intery += gradient

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

    def drawarc(self, x, y, radius, opening=None, facing=None, startangle=None, endangle=None, fillcolor=(0,0,0), outlinecolor=None, outlinewidth=1):
        """
        Experimental, but seems to work correctly
        Optional to use opening and facings args, or start and end angle args
        """
        arcpolygon = [(x,y)]
        arcpolygon.extend(_Arc(x, y, radius, opening=opening, facing=facing, startangle=startangle, endangle=endangle))
        self.drawpolygon(arcpolygon, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth)

    def drawcircle(self, x, y, fillsize, fillcolor=(0,0,0), outlinecolor=None, outlinewidth=1): #, flatten=None, flatangle=None):
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
            ### BEST: http://yellowsplash.wordpress.com/2009/10/23/fast-antialiased-circles-and-ellipses-from-xiaolin-wus-concepts/
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

    def drawsquare(self, x,y,fillsize, fillcolor=(0,0,0), outlinecolor=None, outlinewidth=1, outlinejoinstyle=None):
        halfsize = fillsize/2.0
        rectanglecoords = [(x-halfsize,y-halfsize),(x+halfsize,y-halfsize),(x+halfsize,y+halfsize),(x-halfsize,y+halfsize),(x-halfsize,y-halfsize)]
        self.drawpolygon(coords=rectanglecoords, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth, outlinejoinstyle=outlinejoinstyle)
  
    def drawpolygon(self, coords, holes=[], fillcolor=(0,0,0), outlinecolor=None, outlinewidth=1, outlinejoinstyle="miter"):
        """
        Draws a polygon based on input coordinates.
        Note: as with other primitives, fillcolor does not work properly.
        
        | **option** | **description**
        | --- | --- 
        | coords | list of coordinate point pairs that make up the polygon. Automatically detects whether to enclose the polygon.
        | *holes | optional list of one or more polygons that represent holes in the polygon, each hole being a list of coordinate point pairs. Hole polygon coordinates are automatically closed if they aren't already. 
        | **other | also accepts various color and size arguments, see the docstring for drawline.
        
        """
        #maybe autocomplete polygon and holes
        if coords[-1] != coords[0]:
            coords = list(coords)
            coords.append(coords[0])
        for hole in holes:
            if hole[-1] != hole[0]:
                hole = list(hole)
                hole.append(hole[0])
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
            def coordsandholes():
                #generator for exterior coords and holes
                for edge in pairwise(coords):
                    yield edge
                if holes:
                    for hole in holes:
                        for edge in pairwise(hole):
                            yield edge
            #coordsandholes = [edge for edge in pairwise(coords)]
            #coordsandholes.extend([edge for hole in holepolygons for edge in pairwise(hole)])
            ysortededges = [ list(flatten(sorted(eachedge, key=operator.itemgetter(1)))) for eachedge in coordsandholes() ]
            ysortededges = list(sorted(ysortededges, key=operator.itemgetter(1)))
            edgeindex = 0
            curedge = ysortededges[edgeindex]
            checkedges = []
            #get bbox
            xs, ys = zip(*coords)
            bbox = [min(xs), min(ys), max(xs), max(ys)]
            #begin
            xmin,ymin,xmax,ymax = bbox
            ymin,ymax = map(int, map(round, (ymin,ymax)))
            for y in xrange(ymin,ymax+1):
                fillxs = []
                fillxs_half = []
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
                scanline = _Line(xmin,y,xmax,y)
                for edge in checkedges:
                    edge = _Line(*edge)
                    intersection = scanline.intersect(edge)
                    if intersection:
                        ix,iy = intersection
                        fillxs.append(ix)
##                        if edge.slope:
##                            ix_below = ix + 1/float(edge.slope)
##                            if edge.slope < 0:
##                                fillxs.append(ix)
##                            else:
##                                fillxs.append(ix_below)
##                            halfx = (ix,ix_below)
##                            if halfx[1]-halfx[0] > 1.5 or halfx[0]-halfx[1] > 1.5:
##                                #only do antialias fill if fillspan will be 2 pixels or more
##                                fillxs_half.append(halfx)
##                        else:
##                            fillxs.append(ix)
                #scan line and fill
                fillxs = sorted(fillxs)
                if fillxs:
                    for fillmin,fillmax in groupby2(fillxs):
                        fillmin,fillmax = map(int,map(round,(fillmin,fillmax)))
                        for x in xrange(fillmin,fillmax+1):
                            self.put(x,y,fillcolor)
##                if fillxs_half:
##                    r,g,b = fillcolor[:3]
##                    downflag = True
##                    for fillmin,fillmax in fillxs_half:
##                        if fillmin > fillmax:
##                            fillmin,fillmax = fillmax,fillmin
##                            downflag = False
##                        fillmin,fillmax = map(int,map(round,(fillmin,fillmax)))
##                        gradlength = fillmax-fillmin
##                        incr = 255/float(gradlength)
##                        gradtransp = 0
##                        for x in xrange(fillmin,fillmax+1):
##                            gradcolor = (r,g,b,gradtransp)
##                            self.put(x,y,gradcolor)
##                            gradcolor_inv = (r,g,b,255-gradtransp)
##                            if downflag:
##                                self.put(x,y-1,gradcolor_inv)
##                            else:
##                                self.put(x,y+1,gradcolor_inv)
##                            gradtransp += incr
            #cheating to draw antialiased edges as lines
            self.drawmultiline(coords, fillcolor=fillcolor, outlinecolor=None, fillsize=1)
            for hole in holes:
                self.drawmultiline(hole, fillcolor=fillcolor, outlinecolor=None, fillsize=1)
        #then draw outline
        if outlinecolor:
            coords.append(coords[1])
            self.drawmultiline(coords, fillcolor=outlinecolor, fillsize=outlinewidth, outlinecolor=None, joinstyle=outlinejoinstyle)

    def drawrectangle(self, bbox, fillcolor=(0,0,0), outlinecolor=None, outlinewidth=1, outlinejoinstyle=None):
        x1,y1,x2,y2 = bbox
        rectanglecoords = [(x1,y1),(x1,y2),(x2,y2),(x2,y1),(x1,y1)]
        self.drawpolygon(coords=rectanglecoords, fillcolor=fillcolor, outlinecolor=outlinecolor, outlinewidth=outlinewidth, outlinejoinstyle=outlinejoinstyle)

    def drawarrow(self, x1, y1, x2, y2, fillcolor=(0,0,0), outlinecolor=None, fillsize=1, outlinewidth=1, capstyle="butt"): #, bendfactor=None, bendside=None, bendanchor=None):
        pass
        
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
        if savepath.endswith(".png"):
            imagerows = [list(itertools.chain.from_iterable(row)) for row in self.imagegrid]
            png.from_array(imagerows, mode="RGB").save(savepath)
        elif savepath.endswith(".gif"):
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



if __name__ == "__main__":
    img = Image().new(100,100, background=(222,0,0))
    #img = Image().load("C:/Users/BIGKIMO/Desktop/test2.png")

    #SINGLE PIXEL TEST
    img.put(94.7,94.7,(0,0,222))
    #img.put(95.7,98,(0,0,222))
    #img.put(98,95.7,(0,0,222))

    #GREEN POLYGONS WITH OUTLINE
    #img.drawpolygon(coords=[(30,30),(90,10),(90,90),(10,90),(30,30)], fillcolor=(0,222,0), outlinecolor=(0,0,0), outlinewidth=12, outlinejoinstyle="round")
    #img.drawpolygon(coords=[(80,20),(50,15),(20,44),(90,50),(50,90),(10,50),(30,20),(50,10)], fillcolor=(0,222,0), outlinecolor=(0,0,0), outlinewidth=5, outlinejoinstyle="round")

    #POLYGON WITH HOLES
    img.drawpolygon(coords=[(30,30),(90,10),(90,90),(10,90),(30,30)], holes=[[(51,41),(77,51),(77,65),(51,77),(51,41)] , [(43,63),(49,63),(49,69),(43,69),(43,63)]], fillcolor=(222,222,0), outlinecolor=(0,0,0), outlinewidth=12, outlinejoinstyle="round")

    #MISC MULTILINE TEST
    #img.drawmultiline(coords=[(90,20),(80,20),(50,15),(20,44),(90,50),(50,90),(10,50),(30,20),(50,10)], fillcolor=(0,0,0), fillsize=8, outlinecolor=None, joinstyle="miter")
    #img.drawmultiline(coords=[(10,50),(50,50),(50,90)], fillcolor=(0,0,0), fillsize=8, outlinecolor=None, joinstyle="round")
    #img.drawmultiline(coords=[(10,50),(50,50),(60,90)], fillcolor=(0,111,0), fillsize=12, outlinecolor=None, joinstyle="round")

    #SINGLE LINE TEST
    #img.drawline(22,11,88,77,fillcolor=(222,0,0),fillsize=8, capstyle="round")
    #img.drawline(22,66,88,77,fillcolor=(222,0,0,166),fillsize=11, capstyle="round")
    ##img.drawline(44,33,55,80,fillcolor=(222,0,0),fillsize=0.5)

    #VARIOUS OTHER SHAPES
    #img.drawbezier([(11,11),(90,40),(90,90)])
    #img.drawpolygon([(90,50),(90-5,50-5),(90+5,50+5),(90-5,50+5),(90,50)], fillcolor=(222,0,0))
    #img.drawcircle(50,50,fillsize=8, fillcolor=(222,222,0), outlinecolor=(0,0,222), outlinewidth=1)
    img.drawarc(44,62,radius=30,opening=90,facing=360, outlinecolor=(0,0,222), outlinewidth=1)
    img.drawrectangle([42,42,88,55], fillcolor=(0,0,222), outlinecolor=(211,111,0), outlinewidth=4, outlinejoinstyle="round")
    img.drawsquare(80,80,fillsize=13, fillcolor=(111,0,222), outlinecolor=(211,0,0), outlinewidth=1, outlinejoinstyle="miter")

    #TEST DATA PASTE
    #img = Image().load("C:/Users/BIGKIMO/Desktop/puremap.png")
    #data = Image().load("C:/Users/BIGKIMO/Desktop/hmm.png").imagegrid
    #img.pastedata(444,222,data,transparency=0.5)
    
    img.view()
    img.save("C:/Users/BIGKIMO/Desktop/hmm.png")
