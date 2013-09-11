#!/usr/bin/make -f

PACKAGE=$(shell python setup.py --name)
UPSTREAM_VERSION=$(shell python setup.py --version)
DEBIAN_VERSION=1

SOURCE_DIR=deb_dist/$(PACKAGE)-$(UPSTREAM_VERSION)

MY_LOCATION = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
VIRT_DIR = $(MY_LOCATION)virtualenv

# Add packages (separated by spaces) here that are listed in debian/control but we don't generate a .deb file for.
SKIP_PACKAGES=

# Build dependencies
APT_FILE_VERSION=$(shell dpkg --status apt-file 2>/dev/null | grep ^Version | sed 's/^Version:[ ]*//' || echo '')

all:

listpackages:
	@cd $(SOURCE_DIR); dh_listpackages $(addprefix --no-package=,$(SKIP_PACKAGES))

$(VIRT_DIR): $(VIRT_DIR)/bin/activate
$(VIRT_DIR)/bin/activate:
	test -d $(VIRT_DIR) || virtualenv --no-site-packages $(VIRT_DIR)
	touch $(VIRT_DIR)/bin/activate

test: $(VIRT_DIR)
	. $(VIRT_DIR)/bin/activate; python setup.py test

checkbuilddeps:
	@test -n "$(APT_FILE_VERSION)" || ( echo "Package apt-file is not installed"; exit 1 )

stdeb: stdeb.stamp
stdeb.stamp: $(VIRT_DIR)
	. $(VIRT_DIR)/bin/activate; pip --environment $(VIRT_DIR) install stdeb
	touch stdeb.stamp

debianize: $(VIRT_DIR) stdeb
	apt-file update
	test -d $(SOURCE_DIR) || ( . $(VIRT_DIR)/bin/activate; python setup.py --command-packages=stdeb.command sdist_dsc --debian-version $(DEBIAN_VERSION) )

build: checkbuilddeps debianize
	cd $(SOURCE_DIR); unset LD_LIBRARY_PATH; $(PUMP) dpkg-buildpackage -b -uc -us -rfakeroot $(JOBS_CMD)

deb: build
	mv deb_dist/*.deb ..

clean:
	test ! -d $(SOURCE_DIR) || (cd $(SOURCE_DIR) && fakeroot debian/rules clean)
	rm -f ../python-$(PACKAGE)_*.deb
	rm -f *.changes
	rm -rf deb_dist
	rm -rf $(VIRT_DIR)
	rm -f stdeb.stamp
	rm -rf *.egg

distclean: clean


