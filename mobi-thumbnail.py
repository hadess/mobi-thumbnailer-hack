#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

EOF_RECORD = chr(0xe9) + chr(0x8e) + "\r\n"
""" The EOF record content. """

import sys
import array, struct, os, re, imghdr

from gi.repository import Gio
from gi.repository import GdkPixbuf

class unpackException(Exception):
	pass

class Sectionizer:
	def __init__(self, filename, perm):
		self.f = file(filename, perm)
		header = self.f.read(78)
		self.ident = header[0x3C:0x3C+8]
		self.num_sections, = struct.unpack_from('>H', header, 76)
		sections = self.f.read(self.num_sections*8)
		self.sections = struct.unpack_from('>%dL' % (self.num_sections*2), sections, 0)[::2] + (0xfffffff, )

	def loadSection(self, section):
		before, after = self.sections[section:section+2]
		self.f.seek(before)
		return self.f.read(after - before)

class mobiUnpack:
	def __init__(self, infile):
		self.sect = Sectionizer(infile, 'rb')
		if self.sect.ident != 'BOOKMOBI' and sect.ident != 'TEXtREAd':
			raise unpackException('invalid file format')

		self.header = self.sect.loadSection(0)
		self.records, = struct.unpack_from('>H', self.header, 0x8)
		self.length, self.type, self.codepage, self.unique_id, self.version = struct.unpack('>LLLLL', self.header[20:40])
		self.crypto_type, = struct.unpack_from('>H', self.header, 0xC)

	def getMetaData(self):
		extheader=self.header[16 + self.length:]

		metadata = {}
	
		def addValue(name, value):
			if name not in metadata:
				metadata[name] = [value]
			else:
				metadata[name].append(value)
	
		_length, num_items = struct.unpack('>LL', extheader[4:12])
		extheader = extheader[12:]
		pos = 0
		for _ in range(num_items):
			id, size = struct.unpack('>LL', extheader[pos:pos+8])
			content = extheader[pos + 8: pos + size]
			# 201 is CoverOffset
			if id == 201:
				name = "CoverOffset"
				if size == 9:
					value, = struct.unpack('B',content)
					addValue(name, str(value)) 
				elif size == 10:
					value, = struct.unpack('>H',content)
					addValue(name, str(value))
				elif size == 12:
					value, = struct.unpack('>L',content)
					addValue(name, str(value))
				else:
					print "Error: Value for %s has unexpected size of %s" % (name, size)
			else:
				''' print "Warning: Unknown metadata with id %s found" % id '''
				name = str(id) + ' (hex)'
				addValue(name, content.encode('hex'))
			pos += size
		return metadata

	@property
	def isEncrypted(self):
		if self.crypto_type != 0:
			return True
		return False

	@property
	def firstimg(self):
		if self.sect.ident != 'TEXtREAd':
			img, = struct.unpack_from('>L', self.header, 0x6C)
		else:
			img = self.records + 1
		return img

	@property
	def hasExth(self):
		exth_flag, = struct.unpack('>L', self.header[0x80:0x84])
		return exth_flag & 0x40

def unpackBook(infile, outfile):
	# Instantiate the mobiUnpack class
	mu = mobiUnpack(infile)
	if mu.isEncrypted:
		raise unpackException('file is encrypted')
	header = mu.header
	sect = mu.sect
	records = mu.records

	# if exth region exists then parse it for the metadata
	metadata = {}
	if mu.hasExth:
		metadata = mu.getMetaData()
	metadata['UniqueID'] = [str(mu.unique_id)]

	if 'CoverOffset' in metadata:
		imageNumber = int(metadata['CoverOffset'][0])
		data = sect.loadSection(imageNumber + mu.firstimg)

        memstream = Gio.MemoryInputStream.new_from_data (data, None)
		pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale (memstream, 256, -1, True, None)
		return pixbuf.savev (outfile, "png", [], [])
    else:
        print "Could not find cover in %s" % infile
        return False

def main(argv=sys.argv):
	if len(argv) < 3:
	    print "thumbnailer based on MobiUnpack 0.32"
	    print "  Copyright (c) 2009 Charles M. Hannum <root@ihack.net>"
	    print "  Copyright (c) 2013 Bastien Nocera <hadess@hadess.net>"
	    print "  With Additions by P. Durrant, K. Hendricks, S. Siebert, fandrieu and DiapDealer."
		print ""
		print "Description:"
		print "  Outputs the cover image of a mobi file."
		print "Usage:"
		print "  mobi-thumbnail.py infile outfile"
		return 1
	else:
        inuri, outuri = argv[1:]

        infile = Gio.File.new_for_commandline_arg (inuri)
        inpath = infile.get_path ()

        outfile = Gio.File.new_for_commandline_arg (outuri)
        outpath = outfile.get_path ()

        if unpackBook(inpath, outpath):
            return 0
        else:
            return 1

if __name__ == "__main__":
	sys.exit(main())
