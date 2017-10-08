import numpy as np
import cv2
import os
import glob
import argparse
from time import gmtime, strftime
from shutil import copyfile, move, copytree

def returnHeader():
    return """
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    	<head>
    		<meta http-equiv="X-UA-Compatible" content="IE=Edge"/>
    		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

    		<title>{0}</title>
    		<link href='https://fonts.googleapis.com/css?family=Lato:300,100' rel='stylesheet' type='text/css' />
    		<link type="text/css" rel="stylesheet" media="all" href="./global.css" />
    		<script src="./json.js"></script>
    		<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    		<script src="./cookie.js"></script>
    		<script src="./global.js"></script>
    	</head>
    <body data-resolution="5120 3840 2560 1920 1280 1024 640" data-respath="./">

    <ol id="marker">
    </ol>

    <div id="sidebar">
    	<div class="foreground">
    		<div id="profile" class="camera icon"></div>
    		<h1>{0}</h1>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &darr; | Foto omlaag</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &uarr; | Foto omhoog</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &rarr; | Start</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &larr; | Stop</p>
    		<ul id="nav">

    		</ul>
    	</div>

    	<ul id="control">
    	<li><a href="#" id="resbutton"><span class="monitor icon"></span><span class="restext"></span></a></li>
    	<li style="display: block"><a href="#" id="textbutton" class="active"><span class="toggle icon"></span><span class="text">hide text</span></a></li>
    	<li  style="display: block"><a href="#" id="download"><span class="download icon"></span>download</a></li>
    	</ul>

    	<div class="background"></div>
    </div>

    <div id="resolution">
    </div>
    """.format(args['title'])

def returnFooter():
    return """

    </body>
    </html>
    """

def clamp(x):
  return max(0, min(x, 255))

def rgb_to_hex(r, g, b):
  return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

def get_prominent_rgb(img, num=4):
  Z = img.reshape((-1,3))
  Z = np.float32(Z) # convert to np.float32

  # define criteria, number of clusters(K) and apply kmeans()
  criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
  ret, label, center = cv2.kmeans(Z, num, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
  # Now convert back into uint8, and make original image
  center = np.uint8(center)
  res = center[label.flatten()]
  res2 = res.reshape((img.shape))

  unique_pixels = np.vstack({tuple(r) for r in res2.reshape(-1,3)})
  unique_hex_colors = []
  for bgr in unique_pixels:
    unique_hex_colors.append(rgb_to_hex(bgr[2], bgr[1], bgr[0]))
  return unique_hex_colors

def resize_and_get_colors(filename_image, num_colors, out_dir):
  if not os.path.exists(out_dir):
    os.makedirs(out_dir)
  img = cv2.imread(filename_image)

  height, width, depth = img.shape

  lengths = np.array([640, 1024, 1280, 1920, 2560, 3840, 5120])
  if height > width:
    scale_factors = np.divide(lengths, float(height))
  else:
    scale_factors = np.divide(lengths, float(width))

  largest_width, largest_height = 0, 0
  for scale_factor, length in zip(scale_factors, lengths):
    if scale_factor < 1.0:
      new_width, new_height = int(scale_factor*width), int(scale_factor*height)
      if new_width > largest_width: largest_width = new_width
      if new_height > largest_height: largest_height = new_height
    #   if length in [2560, 3840, 5120]: new_img = cv2.resize(img, None, fx=scale_factors[3], fy=scale_factors[3], interpolation = cv2.INTER_CUBIC)
    #   else: new_img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation = cv2.INTER_CUBIC)
      new_img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation = cv2.INTER_CUBIC)
      if length == 1024:
        unique_hex_colors = get_prominent_rgb(new_img, num_colors)
      cv2.imwrite(out_dir+str(length)+".jpg", new_img)
  return unique_hex_colors, largest_width, largest_height

parser = argparse.ArgumentParser(description='Create gallary & index.html from set of images.')
parser.add_argument('title', type=str, help='Gallary title.')
parser.add_argument('imagedir', type=str, help='Directory containing images to be parsed.')
parser.add_argument('imageExt', type=str, help='Image extension i.e. JPG or *')
parser.add_argument('outputdir', type=str, help='Directory to output gallary to.')
args = vars(parser.parse_args())

currTime = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
image_elements = []
images_to_proc = glob.glob("{0}/*.{1}".format(args['imagedir'], args['imageExt']))
if not os.path.exists(args['outputdir']):
    os.makedirs(args['outputdir'])

for i, ima_filename in enumerate(images_to_proc):
  print("Processing image {0}/{1} - {2}".format(i, len(images_to_proc), ima_filename))
  dir_name = os.path.basename(ima_filename).split('.')[0]
  unique_hex_colors, largest_width, largest_height = resize_and_get_colors(ima_filename, 7, os.path.abspath(args['outputdir'])+'/'+dir_name+'/')
  image_elements.append("\t <div class=\"slide\" style=\"color: #ffffff; background-color: #ffffff\" data-type=\"image\" data-width=\"\" data-height=\"\" data-imagewidth=\""+str(largest_width)+"\" data-imageheight=\""+str(largest_height)+"\" data-textcolor=\"#ffffff\" data-color1=\""+unique_hex_colors[0]+"\" data-color2=\""+unique_hex_colors[1]+"\" data-color3=\""+unique_hex_colors[2]+"\" data-color4=\""+unique_hex_colors[3]+"\" data-color5=\""+unique_hex_colors[4]+"\" data-color6=\""+unique_hex_colors[5]+"\" data-color7=\""+unique_hex_colors[6]+"\" data-videoformats=\"h264 vp8\" data-polygon=\'\'> <a name=\"1\" class=\"internal\"></a> <div class=\"post\" style=\"top: 70\%; left: 20\%; width: 60\%; height: 30\%\"> <div class=\"content\"> </div> </div> <img class=\"image blank\" src=\"//:0\" width=\""+str(largest_width)+"\" height=\""+str(largest_height)+"\" data-url=\""+dir_name+"\" /> </div>")

header = "<div id=\"main\">"
target = open(os.path.abspath(args['outputdir'])+"/index_"+currTime+".html", 'w')
baseHeader = returnHeader()
target.write(baseHeader + "\n")
target.write(header + "\n")

for elem in image_elements:
  target.write(elem)
  target.write("\n")

target.write("</div> \n")
baseFooter = returnFooter()
target.write(baseFooter)
target.close()

copytree("./img", os.path.join(args['outputdir'],"img"))
for f in ["cookie.js", "global.css", "global.js", "json.js"]:
    copyfile("./"+f, args['outputdir']+"/"+f)
