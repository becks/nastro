#!/usr/bin/env python3
"""Organelle OLED simulator for the Mac.

Listens for the patch's OLED messages (sent by mac-sim.pd over UDP) and shows
the 128x64 screen in the browser at http://localhost:8123

Drawing routines are ports of Organelle_OS/OledScreen.cpp, so what you see
here is what the hardware draws.

Run:  python3 oled-sim.py      (then open mac-sim.pd in Pd)
"""
import http.server
import json
import socket
import struct
import threading
import time
import zlib

import os
UDP_PORT = int(os.environ.get("OLED_UDP", 9123))
HTTP_PORT = int(os.environ.get("OLED_HTTP", 8123))

FONT = [0,0,0,0,0,0,0,79,0,0,0,7,0,7,0,20,127,20,127,20,36,42,127,42,18,35,19,8,100,98,0,2,5,2,0,0,5,3,0,0,28,34,65,0,0,0,0,65,34,28,20,8,62,8,20,8,8,62,8,8,0,80,48,0,0,8,8,8,8,8,0,96,96,0,0,32,16,8,4,2,62,81,73,69,62,0,66,127,64,0,66,97,81,73,70,33,65,69,75,49,24,20,18,127,16,39,69,69,69,57,60,74,73,73,48,1,113,9,5,3,54,73,73,73,54,6,73,73,73,54,0,54,54,0,0,0,86,54,0,0,8,20,34,65,0,20,20,20,20,20,0,65,34,20,8,2,1,81,9,6,50,73,121,65,62,126,17,17,17,126,127,73,73,73,54,62,65,65,65,34,127,65,65,34,28,127,73,73,73,65,127,9,9,9,1,62,65,73,73,122,127,8,8,8,127,0,65,127,65,0,32,64,65,63,1,127,8,20,34,65,127,64,64,64,64,127,2,12,2,127,127,4,8,16,127,62,65,65,65,62,127,9,9,9,6,62,65,81,33,94,127,9,25,41,70,70,73,73,73,49,1,1,127,1,1,63,64,64,64,63,31,32,64,32,31,63,64,56,64,63,99,20,8,20,99,7,8,112,8,7,97,81,73,69,67,127,65,65,0,0,2,4,8,16,32,0,0,65,65,127,4,2,1,2,4,64,64,64,64,64,0,1,2,4,0,32,84,84,84,120,127,72,68,68,56,56,68,68,68,32,56,68,68,72,127,56,84,84,84,24,8,126,9,1,2,12,82,82,82,62,127,8,4,4,120,0,68,125,64,0,0,32,64,68,61,127,16,40,68,0,0,65,127,64,0,124,4,24,4,120,124,8,4,4,120,56,68,68,68,56,124,20,20,20,8,8,20,20,24,124,124,8,4,4,8,72,84,84,84,32,4,63,68,64,32,60,64,64,32,124,28,32,64,32,28,60,64,48,64,60,68,40,16,40,68,12,80,80,80,60,68,100,84,76,68,8,54,65,0,0,0,0,127,0,0,0,0,65,54,8,0,8,4,8,4,0,0,0,0,0]  # 5x8 font, ASCII 32..127, 5 column bytes per glyph

BIG = {"arial16":{"w":[0,2,6,7,7,15,11,2,4,4,5,8,2,4,2,4,8,5,8,8,8,8,8,8,8,8,2,2,8,8,8,8,15,11,10,10,10,9,8,10,10,2,8,10,8,11,10,10,9,10,11,9,10,10,11,15,9,10,9,4,4,4,8,9,3,8,8,7,8,7,5,8,8,2,3,7,2,12,8,8,8,8,5,7,5,8,7,13,7,9,7,6,2,6,8,8],"o":[0,2,8,15,22,37,48,50,54,58,63,71,73,77,79,83,91,96,104,112,120,128,136,144,152,160,162,164,172,180,188,196,211,222,232,242,252,261,269,279,289,291,299,309,317,328,338,348,357,367,378,387,397,407,418,433,442,452,461,465,469,473,481,490,493,501,509,516,524,531,536,544,552,554,557,564,566,578,586,594,602,610,615,622,627,635,642,655,662,671,678,684,686,692,700,708],"d":[254,254,27,27,30,30,0,0,30,30,0,0,0,0,0,0,48,240,254,62,240,254,62,31,31,3,31,31,3,3,56,124,230,255,198,140,8,6,14,24,63,25,15,7,60,126,66,66,126,60,128,224,112,28,142,130,128,128,0,0,0,0,16,24,14,7,1,0,15,31,16,16,31,15,0,156,254,230,230,230,62,28,128,0,0,7,15,24,24,25,27,15,14,15,29,8,30,30,0,0,224,252,30,2,15,127,240,128,2,30,252,224,128,240,127,15,20,20,14,20,20,0,0,0,0,0,192,192,192,248,248,192,192,192,0,0,0,7,7,0,0,0,0,0,152,120,0,0,0,0,3,3,3,3,0,0,24,24,0,240,254,14,28,31,3,0,240,252,14,6,6,14,252,240,3,15,28,24,24,28,15,3,48,24,12,254,254,0,0,0,31,31,24,28,14,6,134,198,252,56,24,28,30,27,27,25,24,24,8,12,6,102,102,230,254,156,6,14,28,24,24,28,15,7,0,128,224,112,28,254,254,0,7,7,6,6,6,31,31,6,240,254,126,102,102,230,198,128,6,14,28,24,24,28,15,7,240,252,206,102,102,230,206,140,3,15,28,24,24,24,15,7,6,6,6,198,246,62,14,6,0,0,28,31,3,0,0,0,56,252,198,198,198,198,252,56,7,15,24,24,24,24,15,7,120,252,206,134,134,206,252,240,12,28,25,25,25,28,15,3,48,48,24,24,48,48,152,120,128,192,192,96,96,48,48,24,0,1,1,3,3,6,6,12,176,176,176,176,176,176,176,176,1,1,1,1,1,1,1,1,24,48,48,96,96,192,192,128,12,6,6,3,3,1,1,0,24,28,14,134,198,230,124,56,0,0,0,27,27,0,0,0,192,240,120,156,236,102,54,54,54,230,246,124,28,248,224,15,63,112,239,223,152,152,152,140,159,159,216,204,103,35,0,0,192,248,62,6,62,248,192,0,0,16,30,15,3,3,3,3,3,15,30,16,254,254,198,198,198,198,198,254,188,0,31,31,24,24,24,24,24,25,15,7,240,252,12,6,6,6,6,14,28,8,3,15,12,24,24,24,24,28,14,4,254,254,6,6,6,6,6,12,252,240,31,31,24,24,24,24,24,12,15,3,254,254,198,198,198,198,198,198,198,31,31,24,24,24,24,24,24,24,254,254,198,198,198,198,198,6,31,31,0,0,0,0,0,0,240,252,12,6,6,134,134,142,156,136,3,15,12,24,24,25,25,13,15,7,254,254,192,192,192,192,192,192,254,254,31,31,0,0,0,0,0,0,31,31,254,254,31,31,0,0,0,0,0,0,254,254,6,14,28,24,24,28,15,7,254,254,128,192,96,240,216,12,6,2,31,31,1,0,0,0,3,15,28,24,254,254,0,0,0,0,0,0,31,31,24,24,24,24,24,24,254,254,30,248,192,0,192,248,30,254,254,31,31,0,1,15,30,15,1,0,31,31,254,254,28,56,224,192,0,0,254,254,31,31,0,0,0,1,7,14,31,31,240,252,12,6,6,6,6,12,252,240,3,15,12,24,24,24,24,12,15,3,254,254,198,198,198,198,238,124,56,31,31,0,0,0,0,0,0,0,240,252,12,6,6,6,6,12,252,240,3,15,12,24,26,30,12,28,63,35,254,254,198,198,198,198,198,110,124,56,0,31,31,0,0,0,1,3,15,30,24,16,56,124,110,230,198,198,206,156,24,6,14,28,24,24,24,29,15,7,6,6,6,6,254,254,6,6,6,6,0,0,0,0,31,31,0,0,0,0,254,254,0,0,0,0,0,0,254,254,7,15,28,24,24,24,24,28,15,7,6,30,248,224,0,0,0,224,248,30,6,0,0,0,3,31,28,31,3,0,0,0,6,62,252,192,0,240,254,14,254,240,0,192,248,62,6,0,0,1,31,30,31,1,0,1,31,30,31,3,0,0,6,14,60,240,224,240,60,14,6,24,28,15,3,1,3,15,28,24,6,14,60,112,192,192,112,60,14,6,0,0,0,0,31,31,0,0,0,0,0,6,6,134,230,118,62,14,6,24,28,31,27,25,24,24,24,24,254,254,6,6,255,255,192,192,14,254,240,0,0,3,31,28,6,6,254,254,192,192,255,255,64,112,60,14,14,60,112,64,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,192,192,192,192,192,192,192,192,192,2,6,4,0,0,0,96,112,48,176,176,240,224,0,14,31,27,25,25,15,31,16,254,254,96,48,48,112,224,192,31,31,12,24,24,28,15,7,192,224,112,48,48,112,96,7,15,28,24,24,12,4,192,224,112,48,48,96,254,254,7,15,28,24,24,12,31,31,192,224,176,176,176,224,192,7,15,29,25,25,13,5,48,252,254,54,54,0,31,31,0,0,192,224,112,48,48,96,240,240,103,239,220,216,216,204,255,127,254,254,96,48,48,48,240,224,31,31,0,0,0,0,31,31,246,246,31,31,0,246,246,192,255,127,254,254,128,192,224,48,16,31,31,3,1,7,30,24,254,254,31,31,240,240,96,48,48,240,224,96,48,48,240,224,31,31,0,0,0,31,31,0,0,0,31,31,240,240,96,48,48,48,240,224,31,31,0,0,0,0,31,31,192,224,112,48,48,112,224,192,7,15,28,24,24,28,15,7,240,240,96,48,48,112,224,192,255,255,12,24,24,28,15,7,192,224,112,48,48,96,240,240,7,15,28,24,24,12,255,255,240,240,96,48,48,31,31,0,0,0,224,240,176,176,48,112,96,12,29,25,27,27,31,14,48,252,254,48,48,0,15,31,24,24,240,240,0,0,0,0,240,240,15,31,24,24,24,12,31,31,112,240,128,0,128,240,112,0,3,31,28,31,3,0,48,240,192,0,128,240,112,240,128,0,192,240,48,0,3,31,28,31,3,0,3,31,28,31,3,0,48,112,224,128,224,112,48,24,28,15,3,15,28,24,48,240,192,0,0,0,192,240,48,0,192,199,255,124,31,7,0,0,48,48,48,176,240,240,48,24,30,31,27,25,24,24,128,192,252,126,6,6,1,3,127,254,192,192,254,254,255,255,6,6,126,252,192,128,192,192,254,127,1,1,128,192,192,192,128,128,128,192,1,0,0,0,1,1,1,0,252,4,4,4,4,4,4,252,31,16,16,16,16,16,16,31]},"arial24":{"w":[0,3,9,13,11,16,16,3,6,6,8,11,3,7,3,7,11,7,11,11,12,11,11,11,11,11,3,3,12,12,12,13,22,17,14,15,14,13,12,16,13,3,11,14,12,17,13,16,13,17,14,14,13,13,16,23,14,15,14,6,7,6,12,13,6,12,12,11,12,11,8,12,11,3,5,10,3,17,11,13,12,12,7,11,7,11,11,19,11,13,10,7,3,7,12,12],"o":[0,3,12,25,36,52,68,71,77,83,91,102,105,112,115,122,133,140,151,162,174,185,196,207,218,229,232,235,247,259,271,284,306,323,337,352,366,379,391,407,420,423,434,448,460,477,490,506,519,536,550,564,577,590,606,629,643,658,672,678,685,691,703,716,722,734,746,757,769,780,788,800,811,814,819,829,832,849,860,873,885,897,904,915,922,933,944,963,974,987,997,1004,1007,1014,1026,1038],"d":[254,254,254,135,191,135,3,3,3,126,126,126,0,0,0,126,126,126,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,224,224,224,224,248,254,254,230,224,248,254,254,230,56,56,248,255,255,63,56,248,255,255,63,56,56,0,3,3,3,0,0,3,3,3,0,0,0,0,0,248,252,254,142,255,255,14,62,60,48,48,240,241,227,131,255,255,135,254,254,124,0,0,1,3,3,15,15,3,1,1,0,248,254,6,6,254,248,0,0,128,224,124,30,6,0,0,0,0,3,3,3,3,192,248,62,15,1,240,252,12,12,252,240,0,0,0,4,7,3,0,0,0,0,1,7,6,6,7,1,0,0,120,252,254,206,142,142,206,254,252,120,0,0,0,0,120,252,254,206,135,131,135,143,223,252,248,248,252,220,204,128,0,0,1,3,3,3,3,3,3,1,1,0,1,3,1,0,126,126,126,0,0,0,0,0,0,128,240,252,254,14,2,255,255,255,0,0,0,0,15,63,127,112,64,2,14,254,252,240,0,0,0,0,255,255,255,64,112,127,63,15,0,24,152,208,126,126,208,152,24,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,224,224,224,0,0,0,0,14,14,14,14,255,255,255,14,14,14,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,128,128,128,51,31,15,0,0,0,0,0,0,0,28,28,28,28,28,28,28,0,0,0,0,0,0,0,0,0,0,128,128,128,3,3,3,0,0,128,248,254,126,6,0,240,255,255,15,0,0,3,3,3,0,0,0,0,224,248,252,30,14,14,14,30,252,248,224,63,255,255,192,128,128,128,192,255,255,63,0,0,1,3,3,3,3,3,1,0,0,224,112,112,56,254,254,254,0,0,0,0,255,255,255,0,0,0,0,3,3,3,112,120,124,30,14,14,14,30,252,252,240,0,192,224,240,248,188,158,143,135,131,128,3,3,3,3,3,3,3,3,3,3,3,48,60,60,30,142,142,206,252,252,120,0,112,240,240,192,131,131,131,199,254,254,124,0,0,1,3,3,3,3,3,1,0,0,0,0,0,128,224,240,124,254,254,254,0,0,120,124,127,119,115,112,112,255,255,255,112,112,0,0,0,0,0,0,0,3,3,3,0,0,0,248,254,254,206,206,206,206,142,14,0,51,243,243,195,129,129,129,195,255,255,62,0,0,1,3,3,3,3,3,1,0,0,192,248,252,28,142,142,142,158,60,60,48,63,255,255,199,131,131,131,199,255,255,124,0,0,1,3,3,3,3,3,1,0,0,14,14,14,14,14,206,238,254,126,62,30,0,0,192,248,255,63,7,1,0,0,0,0,0,3,3,3,0,0,0,0,0,0,240,252,252,158,14,14,14,158,252,252,240,120,253,255,207,135,135,135,207,255,253,120,0,1,1,3,3,3,3,3,1,1,0,240,248,252,30,14,14,14,30,252,248,224,97,231,231,207,142,142,142,199,255,255,63,0,1,1,3,3,3,3,1,1,0,0,224,224,224,128,128,128,3,3,3,224,224,224,128,128,128,51,31,15,0,128,128,128,192,192,224,224,112,112,112,56,7,15,15,15,29,29,56,56,112,112,112,224,0,0,0,0,0,0,0,0,0,0,0,0,224,224,224,224,224,224,224,224,224,224,224,224,28,28,28,28,28,28,28,28,28,28,28,28,0,0,0,0,0,0,0,0,0,0,0,0,56,112,112,112,224,224,192,192,128,128,128,0,224,112,112,112,56,56,29,29,15,15,15,7,0,0,0,0,0,0,0,0,0,0,0,0,48,56,60,28,14,14,14,14,14,156,252,248,240,0,0,0,0,0,184,188,190,15,7,3,1,0,0,0,0,0,0,3,3,3,0,0,0,0,0,0,128,224,240,248,56,220,220,238,238,238,206,238,238,254,60,60,120,240,224,128,0,254,255,255,3,252,255,255,195,128,128,225,255,255,255,135,128,192,240,255,63,31,0,1,7,15,31,60,121,115,115,227,225,225,227,227,227,227,241,113,120,60,28,12,4,0,0,0,0,192,240,254,126,14,126,254,240,192,0,0,0,0,0,192,248,254,63,63,57,56,56,56,57,63,63,254,248,192,0,2,3,3,1,0,0,0,0,0,0,0,0,0,1,3,3,2,254,254,254,14,14,14,14,14,14,158,252,252,240,0,255,255,255,135,135,135,135,135,135,135,207,255,252,120,3,3,3,3,3,3,3,3,3,3,3,1,1,0,192,240,248,124,28,30,14,14,14,14,30,28,60,56,16,31,127,255,240,192,128,128,128,128,128,192,192,224,224,64,0,0,0,1,1,3,3,3,3,3,3,1,1,0,0,254,254,254,14,14,14,14,14,14,30,60,248,240,192,255,255,255,128,128,128,128,128,128,192,224,255,127,31,3,3,3,3,3,3,3,3,3,3,1,0,0,0,254,254,254,14,14,14,14,14,14,14,14,14,14,255,255,255,135,135,135,135,135,135,135,135,135,128,3,3,3,3,3,3,3,3,3,3,3,3,3,254,254,254,14,14,14,14,14,14,14,14,14,255,255,255,7,7,7,7,7,7,7,7,0,3,3,3,0,0,0,0,0,0,0,0,0,192,240,248,124,28,30,14,14,14,14,14,30,28,60,56,16,31,127,255,240,192,192,128,128,128,142,142,206,206,254,254,254,0,0,0,1,1,3,3,3,3,3,3,3,1,1,0,0,254,254,254,0,0,0,0,0,0,0,254,254,254,255,255,255,7,7,7,7,7,7,7,255,255,255,3,3,3,0,0,0,0,0,0,0,3,3,3,254,254,254,255,255,255,3,3,3,0,0,0,0,0,0,0,0,254,254,254,112,240,240,192,128,128,128,192,255,255,127,0,1,1,3,3,3,3,3,1,1,0,254,254,254,0,128,192,224,240,120,60,30,14,6,2,255,255,255,15,7,3,3,15,31,126,248,224,128,0,3,3,3,0,0,0,0,0,0,0,1,3,3,3,254,254,254,0,0,0,0,0,0,0,0,0,255,255,255,128,128,128,128,128,128,128,128,128,3,3,3,3,3,3,3,3,3,3,3,3,254,254,254,30,254,248,192,0,0,0,192,248,254,30,254,254,254,255,255,255,0,0,15,255,254,224,254,255,15,0,0,255,255,255,3,3,3,0,0,0,0,3,3,3,0,0,0,0,3,3,3,254,254,254,124,248,224,128,0,0,0,254,254,254,255,255,255,0,1,7,15,62,252,240,255,255,255,3,3,3,0,0,0,0,0,0,3,3,3,3,192,240,248,124,28,30,14,14,14,14,30,28,124,248,240,192,31,127,255,240,192,192,128,128,128,128,192,192,240,255,127,31,0,0,0,1,1,3,3,3,3,3,3,1,1,0,0,0,254,254,254,14,14,14,14,14,14,30,252,252,240,255,255,255,14,14,14,14,14,14,15,7,3,1,3,3,3,0,0,0,0,0,0,0,0,0,0,192,240,248,124,28,30,14,14,14,14,30,28,124,248,240,192,0,31,127,255,240,192,192,128,160,176,224,224,224,240,255,191,143,0,0,0,0,1,1,3,3,3,3,3,3,1,3,3,7,7,1,254,254,254,14,14,14,14,14,14,158,254,252,240,0,255,255,255,7,7,7,15,31,63,251,243,193,128,0,3,3,3,0,0,0,0,0,0,0,3,3,3,2,0,112,252,252,222,142,142,142,14,30,60,60,48,0,48,240,241,225,195,131,131,135,135,135,207,254,254,120,0,0,1,1,3,3,3,3,3,3,3,1,0,0,14,14,14,14,14,254,254,254,14,14,14,14,14,0,0,0,0,0,255,255,255,0,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0,0,254,254,254,0,0,0,0,0,0,0,254,254,254,127,255,255,192,128,128,128,128,128,192,255,255,127,0,0,1,3,3,3,3,3,3,3,1,0,0,2,30,126,252,240,128,0,0,0,0,0,128,240,252,126,30,0,0,0,3,15,63,254,240,192,240,254,63,15,3,0,0,0,0,0,0,0,0,1,3,3,3,1,0,0,0,0,0,6,62,254,252,192,0,0,0,192,248,254,30,254,248,192,0,0,0,192,252,254,62,6,0,0,3,31,255,254,224,254,255,31,1,0,1,31,255,252,224,254,255,31,3,0,0,0,0,0,0,1,3,3,3,0,0,0,0,0,0,0,3,3,3,0,0,0,0,0,0,6,14,62,252,240,224,224,240,124,62,14,6,0,0,128,224,240,124,63,15,15,63,124,240,224,128,0,3,3,3,1,0,0,0,0,0,0,1,3,3,3,6,14,62,124,240,224,128,0,128,224,240,124,62,14,6,0,0,0,0,1,3,255,255,255,3,1,0,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0,0,0,0,0,14,14,14,14,14,14,142,206,238,254,126,62,30,192,224,240,248,188,158,143,135,131,129,128,128,128,128,3,3,3,3,3,3,3,3,3,3,3,3,3,3,254,254,254,14,14,14,255,255,255,0,0,0,127,127,127,112,112,112,6,126,254,248,128,0,0,0,0,15,255,255,240,0,0,0,0,0,3,3,3,14,14,14,254,254,254,0,0,0,255,255,255,112,112,112,127,127,127,0,128,224,248,126,30,30,126,248,224,128,0,2,3,3,1,0,0,0,0,1,3,3,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,112,112,112,112,112,112,112,112,112,112,112,112,112,2,6,14,30,28,16,0,0,0,0,0,0,0,0,0,0,0,0,0,192,192,224,96,96,96,224,224,192,128,0,225,241,249,152,24,28,12,140,255,255,255,0,0,1,3,3,3,3,3,1,1,3,3,2,254,254,254,192,192,224,224,224,224,192,128,0,255,255,255,193,128,128,128,128,193,255,255,62,3,3,3,1,1,3,3,3,3,1,0,0,0,128,192,224,224,224,224,224,192,192,0,62,255,255,193,128,128,128,193,227,227,65,0,0,1,3,3,3,3,3,1,1,0,0,128,192,224,224,224,224,192,192,254,254,254,62,255,255,193,128,128,128,128,193,255,255,255,0,0,1,3,3,3,3,1,1,3,3,3,0,128,192,224,224,224,224,224,192,128,0,62,255,255,205,140,140,140,141,207,207,78,0,0,1,3,3,3,3,3,1,1,0,192,192,252,254,254,198,198,6,0,0,255,255,255,0,0,0,0,0,3,3,3,0,0,0,0,128,192,224,224,224,224,192,192,224,224,224,62,255,255,193,128,128,128,128,193,255,255,255,24,56,121,115,115,115,115,113,121,63,63,15,254,254,254,192,192,224,224,224,224,192,128,255,255,255,1,0,0,0,1,255,255,255,3,3,3,0,0,0,0,0,3,3,3,238,238,238,255,255,255,3,3,3,0,0,238,238,238,0,0,255,255,255,112,112,127,63,31,254,254,254,0,0,128,192,224,96,32,255,255,255,30,15,63,253,240,192,0,3,3,3,0,0,0,0,3,3,3,254,254,254,255,255,255,3,3,3,224,224,224,192,224,224,224,224,192,128,192,224,224,224,224,192,128,255,255,255,1,0,0,0,255,255,255,1,0,0,1,255,255,255,3,3,3,0,0,0,0,3,3,3,0,0,0,0,3,3,3,224,224,224,192,192,224,224,224,224,192,128,255,255,255,1,0,0,0,1,255,255,255,3,3,3,0,0,0,0,0,3,3,3,0,128,192,192,224,224,224,224,224,192,192,128,0,62,255,255,227,193,128,128,128,193,227,255,255,62,0,0,1,1,3,3,3,3,3,1,1,0,0,224,224,224,192,192,224,224,224,224,192,128,0,255,255,255,193,128,128,128,128,193,255,255,62,127,127,127,1,1,3,3,3,3,1,0,0,0,128,192,224,224,224,224,192,192,224,224,224,62,255,255,193,128,128,128,128,193,255,255,255,0,0,1,3,3,3,3,1,1,127,127,127,224,224,224,192,224,224,224,255,255,255,1,0,0,0,3,3,3,0,0,0,0,128,192,224,96,96,96,96,224,192,192,0,71,207,207,142,30,28,28,60,249,249,241,0,1,1,3,3,3,3,3,1,1,0,224,224,248,252,254,224,224,0,0,255,255,255,128,128,0,0,1,3,3,3,3,224,224,224,0,0,0,0,0,224,224,224,255,255,255,192,128,128,128,192,255,255,255,0,1,3,3,3,3,1,1,3,3,3,224,224,224,0,0,0,0,0,224,224,224,0,7,31,255,248,192,248,255,31,7,0,0,0,0,0,3,3,3,0,0,0,0,96,224,224,192,0,0,0,128,224,224,224,128,0,0,0,128,224,224,96,0,3,31,255,252,192,252,255,31,3,31,255,252,192,252,255,31,3,0,0,0,0,0,3,3,3,0,0,0,0,0,3,3,3,0,0,0,0,96,224,224,192,0,0,0,192,224,224,96,0,128,227,247,127,62,127,247,227,128,0,3,3,3,1,0,0,0,1,3,3,3,96,224,224,128,0,0,0,0,0,128,224,224,96,0,3,15,127,254,240,192,240,254,127,15,3,0,0,112,112,112,121,63,63,15,1,0,0,0,0,224,224,224,224,224,224,224,224,224,224,128,192,224,248,188,158,143,131,129,128,3,3,3,3,3,3,3,3,3,3,0,0,248,252,254,14,14,28,62,255,247,227,0,0,0,0,31,63,127,112,112,254,254,254,255,255,255,255,255,255,14,14,254,252,248,0,0,0,0,227,247,255,62,28,112,112,127,63,31,0,0,0,0,128,128,128,0,0,0,0,0,0,0,7,7,3,3,3,7,7,14,14,14,7,7,0,0,0,0,0,0,0,0,0,0,0,0,252,4,4,4,4,4,4,4,4,4,4,252,255,0,0,0,0,0,0,0,0,0,0,255,3,2,2,2,2,2,2,2,2,2,2,3]}}  # arial16/24 from Organelle_OS fonts.h


class Oled:
    def __init__(self):
        self.buf = bytearray(1024)      # page layout, like the hardware
        self.shown = bytes(1024)
        self.info_bar = True
        self.led = 0
        self.lock = threading.Lock()
        # virtual Organelle: controls and page state relayed by mirror.pd / mac-sim.pd (inrelay.py)
        self.keys = set()
        self.aux = False
        self.fs = False
        self.knobs = [0, 0, 0, 0]
        self.ctx = {"mode": 2, "mix-page": 0, "seq-page": 0, "synth-engine": 0, "syn-lfo-page": 0, "drum-kit": 0}
        self.caption = ("", "", 0.0)          # combination, what it does, when
        self.enc = (0, 0.0)                   # encoder position (turns counted) and when it last moved
        self.encbut = False

    # --- primitives (ported from OledScreen.cpp)
    def put(self, on, x, y):
        x &= 0x7F
        y &= 0x3F
        i = (y // 8) * 128 + x
        if on:
            self.buf[i] |= 1 << (y & 7)
        else:
            self.buf[i] &= ~(1 << (y & 7)) & 0xFF

    def get(self, x, y):
        x &= 0x7F
        y &= 0x3F
        return (self.buf[(y // 8) * 128 + x] >> (y & 7)) & 1

    def clear(self):
        self.buf[:] = bytes(1024)

    def fill_area(self, x, y, w, h, c):
        for i in range(min(w, 128)):
            for j in range(min(h, 64)):
                self.put(c, x + i, y + j)

    def box(self, x, y, w, h, c):
        w, h = min(w, 128), min(h, 64)
        for i in range(w):
            self.put(c, i + x, y)
            self.put(c, i + x, y + h - 1)
        for i in range(h):
            self.put(c, x, y + i)
            self.put(c, x + w - 1, y + i)

    def invert_area(self, x, y, w, h):
        for i in range(x, x + min(w, 128)):
            for j in range(y, y + min(h, 64)):
                self.put(not self.get(i, j), i, j)

    def line(self, x0, y0, x1, y1, c):
        x0 &= 0x7F; y0 &= 0x3F; x1 &= 0x7F; y1 &= 0x3F
        dy, dx = y1 - y0, x1 - x0
        sy = -1 if dy < 0 else 1
        sx = -1 if dx < 0 else 1
        dy, dx = abs(dy) << 1, abs(dx) << 1
        self.put(c, x0, y0)
        if dx > dy:
            f = dy - (dx >> 1)
            while x0 != x1:
                if f >= 0:
                    y0 += sy
                    f -= dx
                x0 += sx
                f += dy
                self.put(c, x0, y0)
        else:
            f = dx - (dy >> 1)
            while y0 != y1:
                if f >= 0:
                    x0 += sx
                    f -= dy
                y0 += sy
                f += dx
                self.put(c, x0, y0)

    def circle(self, h, k, r, c, filled=False):
        h &= 0x7F
        k &= 0x3F
        x, y, p = 0, r, 3 - 2 * r
        while True:
            if filled:
                self.line(h + x, k + y, h + x, k - y, c)
                self.line(h + y, k + x, h + y, k - x, c)
                self.line(h - x, k + y, h - x, k - y, c)
                self.line(h - y, k - x, h - y, k + x, c)
            else:
                for px, py in ((h + x, k + y), (h + y, k + x), (h + y, k - x), (h + x, k - y),
                               (h - x, k - y), (h - y, k - x), (h - y, k + x), (h - x, k + y)):
                    self.put(c, px, py)
            x += 1
            if p < 0:
                p += 4 * x + 6
            else:
                y -= 1
                p += 4 * (x - y) + 10
            if x > y:
                break

    def char(self, ch, x, y, c):
        o = min(max(ord(ch), 32), 127) - 32
        for i in range(5):
            col = FONT[o * 5 + i]
            for j in range(8):
                if (col >> j) & 1:
                    self.put(c, x + i, y + j)
        return 5

    def big_char(self, ch, x, y, c, name, rows, space):
        o = min(max(ord(ch), 32), 127)
        if o == 32:
            return space
        o -= 33
        f = BIG[name]
        w = f["w"][o + 1]
        off = f["o"][o] * rows
        for i in range(rows):
            for j in range(8):
                for k in range(w):
                    if (f["d"][off + k + i * w] >> j) & 1:
                        self.put(c, x + k, y + i * 8 + j)
        return w

    def println(self, text, x, y, size, c):
        # 8, 16 and 24 px fonts as in OledScreen::println (32 falls back to 24)
        for ch in text:
            if size == 16:
                x += self.big_char(ch, x, y, c, "arial16", 2, 4) + 2
            elif size >= 24:
                x += self.big_char(ch, x, y, c, "arial24", 3, 6) + 3
            else:
                x += self.char(ch, x, y, c) + 1

    def set_line(self, n, text):
        top = (n - 1) * 11 + 9
        if n == 1:
            for i in range(128):
                self.put(0, i, 8)
        for i in range(128):
            for j in range(11):
                self.put(0, i, top + j)
        text = text[:21]
        self.println(text, 2, top + 1, 8, 1)

    def draw_info_bar(self):
        for i in range(128):
            self.buf[i] = 0
        self.println("in    out", 2, 0, 8, 1)   # stand-in for the VU meters

    def show(self):
        # like the OS: on screen update, the info bar (if enabled) is drawn on top
        if self.info_bar:
            self.draw_info_bar()
        self.shown = bytes(self.buf)

    # --- message handling (same argument layout as Organelle_OS main.cpp)
    def handle(self, words):
        if not words:
            return
        if words[0] in ("send", "sendtyped"):
            words = words[1:]
        if not words:
            return
        path = words[0]
        args = words[1:]
        types = ""
        if path.startswith("/oled/g") and args and all(ch in "ifsb" for ch in args[0]) and not _num(args[0]):
            types, args = args[0], args[1:]           # drop the sendtyped type string
            # like the device: a number sent with type 's' arrives as a string formatted "%f" (1 -> "1.000000")
            args = [f"{float(a):f}" if i < len(types) and types[i] == "s" and _num(a) else a for i, a in enumerate(args)]
            # and a word sent in a number field ('f' / 'i') arrives as 0
            args = ["0" if i < len(types) and types[i] in "fi" and not _num(a) else a for i, a in enumerate(args)]
        elif path.startswith("/oled/g") and path not in ("/oled/gFrame", "/oled/gWaveform"):
            return        # like the device: sendtyped with no type string (e.g. "gPrintln 3 13 ...") draws nothing

        def ints(n):
            return [int(float(a)) for a in args[:n]]

        with self.lock:
            if path.startswith("/oled/line/"):
                n = int(path.rsplit("/", 1)[1])
                self.set_line(n, " ".join(_fmt(a) for a in args) + (" " if args else ""))
                self.show()
            elif path == "/oled/gClear":
                if ints(2)[1] == 1:
                    self.clear()
            elif path == "/oled/gShowInfoBar":
                self.info_bar = bool(ints(2)[1])
            elif path == "/oled/gFillArea":
                _, x, y, w, h, c = ints(6)
                self.fill_area(x, y, w, h, c)
            elif path == "/oled/gBox":
                _, x, y, w, h, c = ints(6)
                self.box(x, y, w, h, c)
            elif path == "/oled/gLine":
                _, a, b, c2, d, col = ints(6)
                self.line(a, b, c2, d, col)
            elif path == "/oled/gCircle":
                _, x, y, r, c = ints(5)
                self.circle(x, y, r, c)
            elif path == "/oled/gFilledCircle":
                _, x, y, r, c = ints(5)
                self.circle(x, y, r, c, filled=True)
            elif path == "/oled/gSetPixel":
                _, x, y, c = ints(4)
                self.put(c, x, y)
            elif path == "/oled/gFrame":
                # the whole screen as a 1024-byte blob, in the hardware's page layout (like the device: only a full blob)
                if len(args) == 1025:
                    self.buf[:] = bytes(int(float(a)) & 0xFF for a in args[1:])
            elif path == "/oled/gWaveform":
                # 128 y values, drawn as 127 connected lines (like the device: only a full blob)
                if len(args) == 129:
                    ys = [int(float(a)) & 0xFF for a in args[1:]]
                    for i in range(1, 128):
                        self.line(i - 1, ys[i - 1], i, ys[i], 1)
            elif path == "/oled/gInvertArea":
                _, x, y, w, h = ints(5)
                self.invert_area(x, y, w, h)
            elif path == "/oled/gInvert":
                if ints(2)[1] == 1:
                    self.buf[:] = bytes(b ^ 0xFF for b in self.buf)
            elif path == "/oled/gPrintln" and types and len(types) != len(args):
                pass                          # like the device (packOSC): more words than types -> nothing drawn
            elif path == "/oled/gPrintln":
                _, x, y, size, c = ints(5)
                self.println(" ".join(_fmt(a) for a in args[5:]) + " ", x, y, size, c)
            elif path == "/oled/gFlip":
                self.show()
            elif path == "/snap" and args:        # debug: save the screen as PNG
                with open(args[0] + ".png", "wb") as f:
                    f.write(png(self.shown))
            elif path == "/led":
                self.led = int(float(args[0])) % 8 if args else 0
            elif path.startswith("/dbg/"):            # probe readings from the device: printed with the page state
                print(time.strftime("%H:%M:%S"), path, " ".join(args), page_name(self.ctx), flush=True)
            elif path.startswith("/in/") or path.startswith("/ctx/"):
                self.control(path, [float(a) for a in args if _num(a)])

    def say(self, combo, what=""):
        self.caption = (combo, what, time.monotonic())

    def control(self, path, v):
        if not v:
            return
        if path.startswith("/ctx/"):
            self.ctx[path[5:]] = int(v[0])
        elif path == "/in/notes" and len(v) >= 2:
            n = int(v[0])
            if v[1] > 0:
                self.keys.add(n)
                if self.aux:
                    self.say("AUX + " + key_name(n), aux_key_function(n, self.ctx))
            else:
                self.keys.discard(n)
        elif path == "/in/aux":
            self.aux = v[0] > 0
        elif path == "/in/fs":
            self.fs = v[0] > 0
            if self.fs:
                piano = self.ctx["mode"] == 0 and self.ctx["synth-engine"] == 11
                self.say("FOOTSWITCH", "sustain pedal" if piano else "REC tape")
        elif path == "/in/knob" and len(v) >= 2 and 1 <= v[0] <= 4:
            k = int(v[0])
            self.knobs[k - 1] = v[1]
            if self.aux:
                self.say(f"AUX + KNOB {k}", aux_knob_function(k, self.ctx))
        elif path == "/in/enc":
            self.enc = (self.enc[0] + (1 if v[0] > 0 else -1), time.monotonic())
        elif path == "/in/encbut":
            self.encbut = v[0] > 0
            if self.encbut and self.aux:
                self.say("AUX + ENCODER", "remove project from list")

    def state(self):
        now = time.monotonic()
        combo, what, t = self.caption
        return {"pix": self.shown.hex(), "led": self.led, "keys": sorted(self.keys), "aux": self.aux, "fs": self.fs,
                "knobs": self.knobs, "enc": self.enc[0], "enct": now - self.enc[1], "encbut": self.encbut,
                "combo": combo, "what": what, "age": now - t if combo else 99, "page": page_name(self.ctx)}


NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ENGINES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS", "WAVE", "STRING", "ORGAN", "DRONE", "PIANO", "MALLET"]
MODES = ["SYNTH", "DRUM", "TAPE", "MIX", "SEQ", "PROJECTS"]       # 5 = encoder menu / album page
MIX_PAGES = ["MIX", "FX", "FILTER", "MASTER", "SEND", "VIS"]
SEQ_PAGES = ["TEMPO", "STEP", "TOMBOLA", "ENDLESS", "ARP"]


def key_name(n):
    """Key names as in the manual: the lower octave by letter (F, G#), the upper one with 5 (C5, A5)."""
    return NOTE[n % 12] + ("5" if n >= 72 else "")


def page_name(ctx):
    m = ctx["mode"]
    if m == 0:
        e = ENGINES[ctx["synth-engine"] % len(ENGINES)]
        return f"SYNTH {e}" + (" LFO" if ctx["syn-lfo-page"] else "")
    if m == 3:
        return "MIX " + MIX_PAGES[ctx["mix-page"] % 6] if ctx["mix-page"] else "MIX"
    if m == 4:
        return "SEQ " + SEQ_PAGES[ctx["seq-page"] % 5]
    return MODES[m] if 0 <= m < len(MODES) else ""


def aux_key_function(n, ctx):
    """What AUX + key does, from the page it was pressed on (the manual's tables)."""
    m, eng, sp = ctx["mode"], ctx["synth-engine"], ctx["seq-page"]
    if n == 60:
        return "next engine: " + ENGINES[(eng + 1) % len(ENGINES)] if m == 0 else "SYNTH page"
    if n == 61:
        return "DRUM page"
    if n == 62:
        return "TAPE page"
    if n == 63:
        return "next page: " + MIX_PAGES[(ctx["mix-page"] + 1) % 6] if m == 3 else "MIX page"
    if n == 64:
        return "next page: " + SEQ_PAGES[(sp + 1) % 5] if m == 4 else "SEQ page"
    glob = {65: "tape PLAY / STOP", 66: "tape REC / stop", 67: "REWIND to start", 68: "LOOP: start / end / off",
            69: "SAVE project", 78: "input MONITOR on / off", 79: "reverb FREEZE on / off", 81: "ALBUM record / stop",
            82: "OCTAVE down", 83: "OCTAVE up"}
    if n in glob:
        return glob[n]
    if n in (76, 77):                     # DRUM: into the selected slot; anywhere else: the SMPL sample
        what = ("WHOLE KIT (24 slices)" if ctx.get("drum-kit") else "DRUM slot") if m == 1 else "SAMPLE (SMPL)"
        return what + (": arm rec from input" if n == 76 else ": rec Nastro output")
    if n == 74:
        return "LFO page on / off" if m == 0 else ""
    if n == 80:
        return ("KIT mode off" if ctx.get("drum-kit") else "KIT mode: next rec = whole kit") if m == 1 else ""
    if n in (73, 75):
        if m == 2:
            return "move BACK" if n == 73 else "move FORWARD"
        if m == 5:
            return "ALBUM: 5 s back" if n == 73 else "ALBUM: 5 s forward"
        return ""
    seq = sp if m == 4 else -1
    if n == 72:                           # C5: the STEP sequence anywhere, except where the page has its own C5
        return {2: "TOMBOLA: pause / resume", 3: "ENDLESS: start / stop", 4: "ARP: HOLD on / off"}.get(
            seq, "STEP sequence: play / stop")
    if n in (70, 71):
        return {1: {70: "STEP: write a rest", 71: "STEP: clear pattern"},
                2: {70: "TOMBOLA: remove last ball", 71: "TOMBOLA: remove all balls"},
                3: {70: "ENDLESS: add a rest", 71: "ENDLESS: clear"},
                4: {71: "ARP: clear"}}.get(seq, {}).get(n, "")
    return ""


def aux_knob_function(k, ctx):
    m, eng = ctx["mode"], ctx["synth-engine"]
    if m == 0:
        if k == 1:
            return "SYNTH VOLUME"
        if ctx["syn-lfo-page"]:
            return ""
        if eng == 1:
            return {2: "SUB attack", 3: "SUB decay / release", 4: "SUB sustain"}[k]
        if eng == 4:
            return {2: "SAMPLE loop start", 3: "SAMPLE loop end"}.get(k, "")
        return ""
    if m == 1:
        return "DRUM VOLUME" if k == 1 else ""
    if m == 2:
        return "SPEED, continuous" if k == 1 else ""
    if m == 3:
        return {0: f"PAN track {k}", 1: "REVERB settings", 2: f"RESONANCE track {k}",
                4: f"REVERB SEND track {k}"}.get(ctx["mix-page"] % 6, "")
    if m == 4 and ctx["seq-page"] == 4 and k == 1:
        return "ARP probability"
    return ""


def _num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _fmt(a):
    # Pd sends floats; the OS prints them with %g. A number that went through a string field ('s') is already
    # "%f" text (see handle) and is printed as it is, like on the device.
    if _num(a) and not (len(a) > 7 and a[-7] == "." and a[-6:].isdigit()):
        return "%g" % float(a)
    return a


OLED = Oled()


def udp_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((os.environ.get("OLED_BIND", "127.0.0.1"), UDP_PORT))   # OLED_BIND=0.0.0.0: mirror from the Organelle
    while True:
        data, _ = sock.recvfrom(65536)
        for msg in data.decode("utf-8", "replace").split(";"):
            words = msg.replace("\\", "").split()
            try:
                OLED.handle(words)
            except Exception as e:  # never die on a malformed message
                print("bad message:", msg.strip(), e)


def png(buf, scale=4):
    w, h = 128 * scale, 64 * scale
    rows = []
    for y in range(64):
        row = bytearray()
        for x in range(128):
            on = (buf[(y // 8) * 128 + x] >> (y & 7)) & 1
            row += (b"\x00" if not on else b"\xff") * scale
        rows += [b"\x00" + bytes(row)] * scale
    raw = b"".join(rows)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Organelle OLED</title>
<style>
:root{--bg:#121416;--panel:#1d86a8;--panel2:#176f8c;--wood:#c47634;--wood2:#8f4e1e;--hot:#ffd36b;--txt:#bbb}
body{background:var(--bg);color:var(--txt);font:14px -apple-system,Helvetica,sans-serif;margin:0;overflow-x:hidden}
#wrap{width:1050px;margin:0 auto;padding:22px 0;transform-origin:top center}
#zoom{display:block;margin:0 auto 22px;image-rendering:pixelated;width:512px;height:256px;border:12px solid #000;
border-radius:6px;background:#000}
#dev{position:relative;width:1050px;height:340px;border-radius:16px;
background:linear-gradient(170deg,var(--panel) 0%,var(--panel2) 100%);box-shadow:0 14px 40px #000c,inset 0 1px 0 #ffffff30}
.knob,.key,#led,#oled{position:absolute;transform:translate(-50%,-50%)}
.knob svg{display:block;filter:drop-shadow(0 4px 4px #0008)}
.knob.hot svg{filter:drop-shadow(0 0 10px var(--hot))}
.num{position:absolute;font-size:12px;color:#0b3d4f;font-weight:600}
.key{width:50px;height:50px;border-radius:50%;background:radial-gradient(circle at 38% 32%,#e3a15f 0%,var(--wood) 45%,var(--wood2) 100%);
box-shadow:0 4px 6px #0009,inset 0 -2px 3px #0005;transition:background .05s,box-shadow .05s}
.key.on{background:radial-gradient(circle at 38% 32%,#fff6d8 0%,var(--hot) 55%,#d9962c 100%);box-shadow:0 0 20px var(--hot),0 2px 3px #0009}
.key span{position:absolute;top:56px;left:50%;transform:translateX(-50%);font-size:10px;color:#0b3d4fcc;white-space:nowrap}
#led{width:20px;height:20px;border-radius:50%;background:#222;box-shadow:0 0 0 2px #0003}
#oled{image-rendering:pixelated;width:192px;height:96px;border:6px solid #000;border-radius:3px;background:#000}
#page{position:absolute;right:18px;bottom:12px;font-size:12px;letter-spacing:.08em;color:#0b3d4f;font-weight:600}
#cap{height:110px;margin-top:22px;text-align:center;transition:opacity .4s}
#combo{font-size:46px;font-weight:700;color:#fff}
#what{font-size:28px;color:var(--hot);margin-top:6px}
</style></head><body><div id="wrap">
<canvas id="zoom" width="128" height="64"></canvas>
<div id="dev"><canvas id="oled" width="128" height="64" style="left:668px;top:80px"></canvas>
<div id="led" style="left:106px;top:177px"></div><div id="page"></div></div>
<div id="cap"><div id="combo"></div><div id="what"></div></div>
</div>
<script>
// layout measured from a photo of an Organelle 1 (keys towards the player)
const dev=document.getElementById('dev'),zc=document.getElementById('zoom').getContext('2d'),
oc=document.getElementById('oled').getContext('2d'),img=zc.createImageData(128,64);
const LED=['#222','#e33','#ec3','#3d4','#3dd','#36f','#c4e','#eee'];
function knob(x,y,d){const r=d/2,el=document.createElement('div');el.className='knob';el.style.left=x+'px';el.style.top=y+'px';
el.innerHTML=`<svg width="${d}" height="${d}" viewBox="${-r} ${-r} ${d} ${d}"><circle r="${r-1}" fill="#141414"/>
<circle r="${r-6}" fill="#1e1e1e"/><line class="ptr" x1="0" y1="${-r*0.25}" x2="0" y2="${-r+4}" stroke="#f2f2f2"
stroke-width="4" stroke-linecap="round"/></svg>`;dev.appendChild(el);return el;}
function label(x,y,t){const el=document.createElement('div');el.className='num';el.style.left=x+'px';el.style.top=y+'px';
el.textContent=t;dev.appendChild(el);}
const KX=[109,226,336,446],kn=[],last=[0,0,0,0],hotT=[0,0,0,0];
KX.forEach((x,k)=>{kn.push(knob(x,62,62));label(x+36,70,k+1);});
const enc=knob(818,62,62),vol=knob(972,62,62);
vol.querySelector('.ptr').setAttribute('transform','rotate(-40)');
const NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'],WHITE=[0,2,4,5,7,9,11],KEY={};
function key(x,y,name){const el=document.createElement('div');el.className='key';el.style.left=x+'px';el.style.top=y+'px';
el.innerHTML=`<span>${name}</span>`;dev.appendChild(el);return el;}
const AUX=key(106,262,'AUX'),X0=194,S=59.3;let wi=0;
for(let n=60;n<84;n++){const pc=n%12,nm=NAMES[pc]+(n>=72?'5':'');
if(WHITE.includes(pc)){KEY[n]=key(X0+wi*S,262,nm);wi++;}else KEY[n]=key(X0+(wi-0.5)*S,190,nm);}
const FS=document.createElement('div');FS.className='num';FS.style.cssText='left:930px;top:300px;font-size:12px';dev.appendChild(FS);
function fit(){const sc=Math.min(1,(innerWidth-32)/1050);document.getElementById('wrap').style.transform=`scale(${sc})`;}
addEventListener('resize',fit);fit();
async function tick(){try{const r=await fetch('/frame');const j=await r.json();
for(let y=0;y<64;y++)for(let x=0;x<128;x++){const b=parseInt(j.pix.substr(((y>>3)*128+x)*2,2),16);
const on=(b>>(y&7))&1,i=(y*128+x)*4;img.data[i]=on?235:0;img.data[i+1]=on?240:0;img.data[i+2]=on?255:0;img.data[i+3]=255;}
zc.putImageData(img,0,0);oc.putImageData(img,0,0);
const L=document.getElementById('led');L.style.background=LED[j.led];L.style.boxShadow=j.led?`0 0 14px ${LED[j.led]}`:'0 0 0 2px #0003';
const now=performance.now();
for(const n in KEY)KEY[n].classList.toggle('on',j.keys.includes(+n));
AUX.classList.toggle('on',j.aux);
FS.textContent=j.fs?'FOOTSWITCH':'';
for(let k=0;k<4;k++){const v=j.knobs[k];if(v!==last[k]){last[k]=v;hotT[k]=now;}
kn[k].querySelector('.ptr').setAttribute('transform',`rotate(${-140+2.8*v})`);kn[k].classList.toggle('hot',now-hotT[k]<600);}
enc.querySelector('.ptr').setAttribute('transform',`rotate(${j.enc*24})`);
enc.classList.toggle('hot',j.encbut||j.enct<0.3);
document.getElementById('page').textContent=j.page;
document.getElementById('combo').textContent=j.combo;document.getElementById('what').textContent=j.what;
document.getElementById('cap').style.opacity=j.age<2.5?1:Math.max(0,1-(j.age-2.5)/0.6);
}catch(e){}
setTimeout(tick,40);}tick();
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/frame":
            with OLED.lock:
                body = json.dumps(OLED.state()).encode()
            ctype = "application/json"
        elif self.path == "/frame.png":
            with OLED.lock:
                body = png(OLED.shown)
            ctype = "image/png"
        else:
            body, ctype = PAGE.encode(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    threading.Thread(target=udp_loop, daemon=True).start()
    print(f"OLED sim: http://localhost:{HTTP_PORT}  (listening for Pd on udp {UDP_PORT})")
    http.server.ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), Handler).serve_forever()
