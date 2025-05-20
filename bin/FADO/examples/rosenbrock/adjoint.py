import sys
import time

#time.sleep(3)

config = sys.argv[1]

fid = open(config,"r")
lines = fid.readlines()
fid.close()

data = lines[0][0:-1]
x = float(lines[1])
y = float(lines[2])
mode = lines[3]

fid = open(data,"r")
lines = fid.readlines()
fid.close()

a = float(lines[0])
b = float(lines[1])

# Rosenbrock's function
f1 = (a-x)**2+b*(y-x**2)**2

# A simple linear constraint
f2 = x+y

if mode.startswith("rosenbrock"):
    dfdx = 2*(x-a)+4*b*x*(x**2-y)
    dfdy = 2*b*(y-x**2)
else:
    dfdx = 1
    dfdy = 1
#end

fid = open("gradient.txt","w")
fid.writelines([str(dfdx)+"\n",str(dfdy)+"\n"])
fid.close()
