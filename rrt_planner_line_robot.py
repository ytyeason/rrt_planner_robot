#!/usr/bin/python
import time
import random
import drawSample
import math
import _tkinter
import sys
import imageToRects
import numpy as np

#display = drawSample.SelectRect(imfile=im2Small,keepcontrol=0,quitLabel="")

visualize = 1
prompt_before_next=1  # ask before re-running sonce solved
SMALLSTEP = 5 # what our "local planner" can handle.
length = 50 #length of the robot
radius = length/2.0 #radius of the robot

XMAX=1800
YMAX=1000
G = [  [ 0 ]  , [] ]   # nodes, edges


s,obstacles = imageToRects.imageToRects(sys.argv[1])

XMAX = s[0]
YMAX = s[1]



# goal/target
tx = 800
ty = 150
t_theta = 0
# start
start_x = 100
start_y = 630
start_theta = 0
#target range
tx_range_low = tx -4
tx_range_high = tx+4
ty_range_low = ty-4
ty_range_high = ty+4

vertices = [ [start_x,start_y,start_theta] ]

sigmax_for_randgen = XMAX/2.0
sigmay_for_randgen = YMAX/2.0

nodes=0
edges=1
maxvertex = 0

def drawGraph(G):
    global vertices,nodes,edges
    if not visualize: return
    for i in G[edges]:
        if len(vertices)!=1:
            canvas.polyline(  [vertices[i[0]], vertices[i[1]] ]  )

#used in genvertex
def genPoint():
    # TODO : Function to implement the sampling technique
    # Uniform distribution
    random_x = random.uniform(1,XMAX)
    random_y = random.uniform(1,YMAX)
    #       OR
    # Gaussian distribution with mean at the goal
    # random_x = random.gauss(800,XMAX/2)
    # random_y = random.gauss(150,YMAX/2)
    random_theta = random.uniform(0,2*math.pi)
    return [random_x,random_y,random_theta]

def genvertex():
    vertices.append( genPoint() )
    return len(vertices)-1

def pointToVertex(p):
    vertices.append( p )
    return len(vertices)-1

#used in pickGvertex
def pickvertex():
    return random.choice( range(len(vertices) ))

def lineFromPoints(p1,p2):
    line = []
    llsq = 0.0 # line length squared
    for i in range(len(p1)):  # each dimension
        h = p2[i] - p1[i]
        line.append( h )
        llsq += h*h
    ll = math.sqrt(llsq)  # length
    # normalize line
    if ll <=0: return [0,0]
    for i in range(len(p1)):  # each dimension
        line[i] = line[i]/ll
    return line

#used in closestPointToPoint
def pointPointDistance(p1,p2):
    """ Return the distance between a pair of points (L2 norm). """
    llsq = 0.0 # line length squared
    # faster, only for 2D
    h = p2[0] - p1[0]
    llsq = llsq + (h*h)
    h = p2[1] - p1[1]
    llsq = llsq + (h*h)
    return math.sqrt(llsq)

    for i in range(len(p1)):  # each dimension, general case
        h = p2[i] - p1[i]
        llsq = llsq + (h*h)
    return math.sqrt(llsq)

def closestPointToPoint(G,p2):
    dmin = 999999999
    for v in G[nodes]:
        p1 = vertices [ v ]
        d = pointPointDistance(p1,p2)
        if d <= dmin:
            dmin = d
            close = v
    return close

def returnParent(k):
    """ Return parent note for input node k. """
    for e in G[edges]:
        if e[1]==k:
            canvas.polyline(  [vertices[e[0]], vertices[e[1]] ], style=3  )
            return e[0]

def pickGvertex():
    try: edge = random.choice( G[edges] )
    except: return pickvertex()
    v = random.choice( edge )
    return v

def redraw():
    canvas.clear()
    canvas.markit(start_x, start_y, r=SMALLSTEP)
    canvas.markit( tx, ty, r=SMALLSTEP )
    drawGraph(G)
    for o in obstacles: canvas.showRect(o, outline='blue', fill='blue')
    canvas.delete("debug")

#used in intersect
def ccw(A,B,C):
    """ Determine if three points are listed in a counterclockwise order.
    For three points A, B and C. If the slope of the line AB is less than
    the slope of the line AC then the three points are in counterclockwise order.
    See:  http://compgeom.cs.uiuc.edu/~jeffe/teaching/373/notes/x06-sweepline.pdf
    """
    return (C[1]-A[1])*(B[0]-A[0]) > (B[1]-A[1])*(C[0]-A[0])

#used in lineHitsRect
def intersect(A,B,C,D):
        """ do lines AB and CD intersect? """
        i = ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
        #if i:
        #    canvas.polyline(  [ A,B ], style=4  , tags = ("debug"))
        #    canvas.polyline(  [ C,D ], style=4  , tags = ("debug"))
        #else:
        #    canvas.polyline(  [ A,B ], style=1  , tags = ("debug")) # green
        #    canvas.polyline(  [ C,D ], style=1  , tags = ("debug"))
        return i


def lineHitsRect(p1,p2,r):
   rline = ( (r[0],r[1]), (r[0],r[3]) )
   if intersect( p1, p2, rline[0], rline[1] ): return 1
   rline = ( (r[0],r[1]), (r[2],r[1]) )
   if intersect( p1, p2, rline[0], rline[1] ): return 1
   rline = ( (r[0],r[3]), (r[2],r[3]) )
   if intersect( p1, p2, rline[0], rline[1] ): return 1
   rline = ( (r[2],r[1]), (r[2],r[3]) )
   if intersect( p1, p2, rline[0], rline[1] ): return 1

   return 0

def inRect(p,rect,dilation,dilation2):
   """ Return 1 if p is inside rect, dilated by dilation (for edge cases). """
   if p[0]<rect[0]-dilation: return 0
   if p[1]<rect[1]-dilation2: return 0
   if p[0]>rect[2]+dilation: return 0
   if p[1]>rect[3]+dilation2: return 0
   return 1

#TODO: Implement the rrt_search algorithm in this function.
def rrt_search(G, tx, ty):
    # Implement the rrt_algorithm in this section of the code.
    # You should call genPoint() within this function to
    #get samples from different distributions.
    found = 0
    while True:
        x_random = genPoint()
        if ((x_random[0]<=XMAX)and(x_random[0]>=0))and((x_random[1]<=YMAX)and(x_random[1]>=0)) :
            break;
    x_nearest = vertices[closestPointToPoint(G,x_random)]

    line_between = lineFromPoints(x_nearest,x_random)
    move_distance = [line_between[0] * SMALLSTEP, line_between[1] * SMALLSTEP]

    x_new = [x_nearest[0]+move_distance[0], x_nearest[1]+move_distance[1], x_random[2]]

    in_rect = 0
    for o in obstacles :
        print "angle"
        print abs(25*math.sin(x_new[2]))
        if inRect(x_new,o,abs(25*math.sin(x_new[2])),abs(25*math.cos(x_new[2]))):
            in_rect = 1

    if not in_rect :
        have_obstacles = 0
        for o in obstacles :
            if (lineHitsRect(x_nearest,x_new,o)):
                have_obstacles = 1
                break

        if not have_obstacles :
            print x_new
            if ((tx_range_low)<=x_new[0]<=(tx_range_high))and((ty_range_low)<=x_new[1]<=(ty_range_high)) :#turn the flag to found
                found = 1
            vertices.append(x_new)
            G[nodes].append(len(G[nodes]))
            G[edges].append(((vertices.index(x_nearest)),(vertices.index(x_new))))
            canvas.polyline([vertices[(vertices.index(x_nearest))],vertices[vertices.index(x_new)]])
            if found == 1:
                child_node = vertices.index(x_new)
                count = 0
                path_length = 0
                while child_node!=0:
                    count = count +1
                    path_length = path_length + 1
                    a = vertices[child_node][0]+(radius*math.sin(vertices[child_node][2]))
                    b = vertices[child_node][1]+(radius*math.cos(vertices[child_node][2]))
                    c = vertices[child_node][0]-(radius*math.sin(vertices[child_node][2]))
                    d = vertices[child_node][1]-(radius*math.cos(vertices[child_node][2]))
                    if count%2 == 0:
                        canvas.polyline([[a,b],[c,d] ], style=3  )
                    child_node = returnParent(child_node)
                print "path_length is "
                print path_length
                print SMALLSTEP

        have_obstacles = 0

    in_rect = 0
    canvas.events()
    return found

if visualize:
    canvas = drawSample.SelectRect(xmin=0,ymin=0,xmax=XMAX ,ymax=YMAX, nrects=0, keepcontrol=0)#, rescale=800/1800.)


if 0:  # line intersection testing
        obstacles.append( [ 75,60,125,500 ] )  # tall vertical
        for o in obstacles: canvas.showRect(o, outline='red', fill='blue')
        lines = [
           ( (70,50), (150,150) ),
           ( (50,50), (150,20) ),
           ( (20,20), (200,200) ),
           ( (300,300), (20, 200)  ),
           ( (300,300), (280, 90)  ),
           ]
        for l in lines:
           for o in obstacles:
              lineHitsRect(l[0],l[1],o)
        canvas.mainloop()


if 0:
    # random obstacle field
    for nobst in range(0,6000):
        wall_discretization=SMALLSTEP*2  # walls are on a regular grid.
        wall_lengthmax=10.  # fraction of total (1/lengthmax)
        x = wall_discretization*int(random.random()*XMAX/wall_discretization)
        y = wall_discretization*int(random.random()*YMAX/wall_discretization)
        #length = YMAX/wall_lengthmax
        length = SMALLSTEP*2
        if random.choice([0,1]) >0:
            obstacles.append( [ x,y,x+SMALLSTEP,y+10+length ] )  # vertical
        else:
            obstacles.append( [ x,y,x+10+length,y+SMALLSTEP ] )  # horizontal
else:
  if 0:
    # hardcoded simple obstacles
    obstacles.append( [ 300,0,400,95 ] )  # tall vertical
    # slightly hard
    obstacles.append( [ 300,805,400,YMAX ] )  # tall vertical
    #obstacles.append( [ 300,400,1300,430 ] )
    # hard
    obstacles.append( [ 820,220,900,940 ] )
    obstacles.append( [ 300,0,  400,95 ] )  # tall vertical
    obstacles.append( [ 300,100,400,YMAX ] )  # tall vertical
    obstacles.append( [ 200,300,800,400 ] )  # middle horizontal
    obstacles.append( [ 380,500,700,550 ] )
    # very hard
    obstacles.append( [ 705,500,XMAX,550 ] )




if visualize:
    for o in obstacles: canvas.showRect(o, outline='red', fill='blue')


maxvertex += 1

G = [  [ 0 ]  , [] ]   # nodes, edges
vertices = [ [start_x,start_y,start_theta]  ]
redraw()

total_count = 0
while 1:
    # graph G

    if visualize: canvas.markit( tx, ty, r=SMALLSTEP )

    # drawGraph(G)
    target = rrt_search(G, tx, ty)
    total_count = total_count + 1
    print target
    if target==1 :
        print total_count
        break

#canvas.showRect(rect,fill='red')

if visualize:
    canvas.mainloop()
