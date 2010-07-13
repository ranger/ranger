# Feed this with data from mime.types or other file extension databases
# Then feed the output of this file to ranger/ext/fast_typetest.py

container_extensions = """
7z ace ar arc bz bz2 cab cpio cpt dgc dmg gz iso jar msi pkg rar
shar tar tbz tgz xar xz zip
"""

video_extensions = """
3gpp asf asx avi axv dif div divx dl dv fli flv gl lsf lsx mkv mng mov
movie mp4 mpe mpeg mpg mpv mxu ogm ogv qt wm wmv wmx wvx
"""

image_extensions = """
art bmp cdr cdt cpt cr2 crw djv djvu erf gif ico ief jng jpe jpeg jpg
nef orf pat pbm pcx pgm png pnm ppm psd ras rgb svg svgz tif tiff
wbmp xbm xpm xwd
"""

audio_extensions = """
aif aifc aiff amr au awb axa flac gsm kar m3u m4a mid midi mp+ mp2
mp3 mpc mpega mpga mpp oga ogg pls ra ram rm sd2 sid snd spx wav wax wma
"""

def splitlines(string, limit=75, first=True):
	if len(string) > limit:
		pos = string.rfind(' ', 0, limit)
		if first: limit -= 8  # reduce the limit to make room for the TAB
		return string[:pos] + "\n\t" + splitlines(string[pos+1:], limit, False)
	return string

def dump(varname, extensions):
	print(splitlines(varname + " = set(" + \
			str(list(sorted(set(extensions.split())))) + ")"))

for key, val in locals().copy().items():
	if key.endswith('_extensions'):
		dump(key, val)
		print()
