# Summer 2014
# Copyleft Roman Rolinsky, genericsoma AT gmail DOT com
# Test of QR code scanner for Raspberry Eye project 
# http://hackaday.io/project/865-Raspberry-Eye

import io
import os
import time
import picamera
from PIL import Image
import zbar
import numpy as np
from scipy.misc import imresize

# PyGame
import pygame
from pygame.locals import *
os.environ["SDL_FBDEV"] = "/dev/fb1"
# Uncomment if you have a touch panel and find the X value for your device
#os.environ["SDL_MOUSEDRV"] = "TSLIB"
#os.environ["SDL_MOUSEDEV"] = "/dev/input/eventX"
pygame.init()
# set up the window
DISPLAYSURF = pygame.display.set_mode((320, 240), 0, 16)
pygame.mouse.set_visible(0)

width, height = 1024, 768

stream = io.BytesIO()
stream2 = io.BytesIO()

# create a reader
scanner = zbar.ImageScanner()

# configure the reader
scanner.parse_config('enable')
scanner.set_config(zbar.Symbol.NONE, zbar.Config.ENABLE, 0)
scanner.set_config(zbar.Symbol.QRCODE, zbar.Config.ENABLE, 1)

font_filename = pygame.font.match_font('droidsans')
font = pygame.font.Font(font_filename, 24)
buf = np.zeros((3, 240, 320), 'uint8')

keep_text = None
keep_count = 0
zoom = True
ghost = False
offset_x = -0.08
offset_y = 0.03

with picamera.PiCamera() as camera:
    print camera.resolution
    camera.resolution = (width, height)
    camera.rotation = 180
    print camera.resolution
    #camera.start_preview()
    done = False
    while True:
        if zoom:
            camera.crop = (0.22 + offset_x, 0.22 + offset_y, 0.66, 0.66)
        else:
            camera.crop = (0.2, 0.2, 0.6, 0.6)
        print 'capturing'
        camera.capture(stream, format='yuv', use_video_port=False)

        stream.seek(0)
        # Load the Y (luminance) data from the stream
        Y = np.fromstring(stream.getvalue(), dtype=np.uint8, count=width*height)
        Y = Y.reshape((height, width))
        # Crop
        #Y = Y[300:900,400:1200]

        DISPLAYSURF.fill((0, 0, 0))

        if ghost:
            Y2 = imresize(Y, (240, 320), 'bilinear', 'L')
            buf[2,:,:] = Y2
            pygame.surfarray.blit_array(DISPLAYSURF, buf.transpose())
        if keep_text:
            DISPLAYSURF.blit(text, (10, 10))
            keep_count += 1
            if keep_count == 5:
                keep_text = None
                keep_count = 0
        pygame.display.update()

        # wrap image data
        image = zbar.Image(width, height, 'Y800', Y.tostring())

        print 'scanning'
        # scan the image for barcodes
        scanner.scan(image)

        # extract results
        i = 0
        for symbol in image:
            # do something useful with results
            print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data
            #import pdb;pdb.set_trace()
            poly = [(l[0]/(width/320.), l[1]/(height/240.)) for l in symbol.location]
            pygame.draw.polygon(DISPLAYSURF, (255, 0, 0), poly)
            text = font.render(symbol.data, 1, (255, 255, 255))
            DISPLAYSURF.blit(text, (10, 10 + i*20))
            if i == 0: 
                keep_text = text
                keep_count = 0
            i += 1

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif event.key == K_s:
                    im = Image.fromarray(Y.reshape(height, width))
                    im.save('frame.jpg')
                    print 'saved'
                elif event.key == K_z:
                    zoom = not zoom
                elif event.key == K_g:
                    ghost = not ghost
                elif event.key == K_UP:
                    offset_y += 0.01
                elif event.key == K_DOWN:
                    offset_y -= 0.01
                elif event.key == K_LEFT:
                    offset_x += 0.01
                elif event.key == K_RIGHT:
                    offset_x -= 0.01
        print offset_x, offset_y
        if done: break
 
pygame.quit()
