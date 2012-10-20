all:

install:	

	# create all required dirs
	mkdir -p $(DESTDIR)/usr/sbin
	mkdir -p $(DESTDIR)/usr/lib/unifi_lab
	chmod 755 $(DESTDIR)/usr/lib/unifi_lab

	# copy all files and symlink them to into the path
	cp unifi_lab.py $(DESTDIR)/usr/lib/unifi_lab/unifi_lab
	chmod 755 $(DESTDIR)/usr/lib/unifi_lab/unifi_lab

	cp unifi_lab_ctlrobj.py $(DESTDIR)/usr/lib/unifi_lab/unifi_lab_ctlrobj.py
	
	# relative symlinks to make packaging easier
	@cd $(DESTDIR)/usr/bin/; \
	[ -h unifi_lab ] && rm unifi_lab; \
	ln -s ../lib/unifi_lab/unifi_lab .
    
	# now copy the config, but don't overwrite any preexisting config
	# first: unifi_lab.ini
	@if [ -a $(DESTDIR)/etc/unifi_lab/unifi_lab.ini ]; then \
		cp unifi_lab_production.ini $(DESTDIR)/etc/unifi_lab/unifi_lab.ini.install; \
		chmod 600 $(DESTDIR)/etc/unifi_lab.ini.install; \
	else \
		mkdir -p $(DESTDIR)/etc/unifi_lab; \
		chmod 755 $(DESTDIR)/etc/unifi_lab; \
		cp unifi_lab_production.ini $(DESTDIR)/etc/unifi_lab/unifi_lab.ini; \
		chmod 600 $(DESTDIR)/etc/unifi_lab/unifi_lab.ini; \
	fi

        # second: unifi_lab_mac_auth.list
        @if [ -a $(DESTDIR)/etc/unifi_lab/unifi_lab_mac_auth.list ]; then \
                cp unifi_lab_mac_auth.list $(DESTDIR)/etc/unifi_lab/unifi_lab_mac_auth.list.install; \
                chmod 644 $(DESTDIR)/etc/unifi_lab_mac_auth.list.install; \
        else \
                cp unifi_lab_mac_auth.list $(DESTDIR)/etc/unifi_lab/unifi_lab_mac_auth.list; \
                chmod 644 $(DESTDIR)/etc/unifi_lab/unifi_lab_mac_auth.list; \
        fi


build:

clean:

