all: mobi-thumbnail.py mobi-thumbnail.thumbnailer

install: mobi-thumbnail.py mobi-thumbnail.thumbnailer
	install -m 0755 mobi-thumbnail.py /usr/bin/
	install -m 0644 mobi-thumbnail.thumbnailer /usr/share/thumbnailers/
