#!/bin/sh
#
# Script for building and installing the Microsoft Fonts
#

# Build
mkdir ~/rpmbuild
mkdir ~/rpmbuild/BUILD
mkdir -p ~/rpmbuild/RPMS/noarch
rpmbuild -bb msttcorefonts-2.0-1.spec

# Install
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/msttcorefonts-2.0-1.noarch.rpm
sudo /sbin/service xfs reload

# Verify
xlsfonts | grep ^-microsoft

# Copy where ImageMagick can use them
sudo mkdir /usr/share/fonts/default/TrueType
sudo cp /usr/share/fonts/msttcorefonts/arial.ttf /usr/share/fonts/default/TrueType/.

# Notice
echo
echo "  You can now do an `rm -r ~/rpmbuild` if you like."
echo

