#!/bin/sh

# NOTE: we copy everything from the redhat /spec folder and do changes here.
# If the changes start piling up more and this becomes unmaintainable,
# we can move to just modifying the current lvm2.spec directly and stop using
# this script.

# Copy default red hat spec files for us
cp ../lvm2/spec/* .

# Get current version string, and set it as lvm2 version
LVM_VERSION=$(cat ../lvm2/VERSION | cut -d '(' -f 1)
sed -i "/Version:/c\Version: $LVM_VERSION" source.inc

# Get device mapper version and set it correctly into the spec files
DM_VERSION=$(cat ../lvm2/VERSION_DM | cut -d '-' -f 1)
sed -i "/%define device_mapper_version/c\%define device_mapper_version $DM_VERSION" source.inc

# Disable the cluster mirroring stuff
sed -i "/%global buildreq_cluster corosync-devel/d" source.inc
sed -i "/%global req_cluster corosync/d" source.inc
sed -i "/%with clvmd corosync/d" source.inc
sed -i "/%global enable_cmirror 1/c\%global enable_cmirror 0" source.inc

# Disable udev requirement and systemd services
sed -i "/%global enable_udev 1/c\%global enable_udev 0" source.inc
sed -i "/%global enable_systemd 1/c\%global enable_systemd 0" source.inc

# Disable metad.. slight performance hit for simplified setup effort.
sed -i "/%service lvmetad 1/c\%service lvmetad 0" source.inc

# Make buildrequires explicit, as OBS cannot parse things behind macros :(
sed -i "/%maybe BuildRequires: %{?buildreq_udev}/c\BuildRequires: systemd-devel" source.inc

# Disable buildrequires for libsepol-devel and libselinux-devel.
# This seems to build fine without, so probably some red hat build env thing.
# If we'd keep these, we'd need to move selinux stuff to mer-core
sed -i "/libselinux-devel/d" source.inc

# In mer systemctl and generic units are in main systemd package
sed -i "s/systemd-units/systemd/" packages.inc

# Replace the import line with actual content of source.inc.
# This is needed for the BuildRequires parsing on OBS to work.
sed -i -e '/%import source.inc/{r source.inc' -e 'd}' lvm2.spec

# Replace Source0 with Mer OBS friendly naming.
sed -i "/Source0:/c\Source0: %{name}-%{version}.tar.bz2" lvm2.spec

# Fix setup line for OBS
sed -i "/%setup -q -n/c\%setup -n %{name}-%{version}/%{name}" lvm2.spec

# For local mb builds, one can comment above setup line and uncomment this one:
#sed -i "/%setup -q -n/c\%setup -n %{name}/%{name}" lvm2.spec

