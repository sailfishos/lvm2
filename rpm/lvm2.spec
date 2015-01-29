# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# NB. This specfile is a work in progress. It is currently used by the
# continuous integration system driven by nix and hydra to create and test RPMs
# on Fedora, CentOS and RHEL systems. It is not yet ready for deployment of LVM
# on those systems.

# A macro to pull in an include file from an appropriate location.
%define import() %include %(test -e %{S:%1} && echo %{S:%1} || echo %{_sourcedir}/%1)

%import macros.inc

##############################################################
# Defaults (rawhide)... 

%global enable_profiling 0
%global enable_udev 0
%global enable_systemd 0
%global enable_cmirror 0


# TODO %global req_dm_persistent device-mapper-persistent-data >= 0.1.4
%with cache internal
%with thin internal
%with thin_check %{_sbindir}/thin_check
%with thin_repair %{_sbindir}/thin_repair
%with thin_dump %{_sbindir}/thin_dump

%global buildreq_udev systemd-devel
%global req_udev udev >= 181-1

%service lvmetad 0

##############################################################

%if %{fedora} == 16 || %{rhel} == 6
%global enable_systemd 0

%global buildreq_udev libudev-devel
%global buildreq_cluster openaislib-devel >= 1.1.1-1, clusterlib-devel >= 3.0.6-1, corosynclib-devel >= 1.2.0-1

%global req_udev udev >= 158-1
%global req_cluster openais >= 1.1.1-1, cman >= 3.0.6-1, corosync >= 1.2.0-1

%global _udevbasedir /lib/udev
%global _udevdir %{_udevbasedir}/rules.d
%endif

%if %{fedora} == 16
%with cache none
%with thin none
%with thin_check
%with thin_repair
%with thin_dump
%endif

##############################################################

%if %{fedora} == 17
%global buildreq_udev systemd-devel

%global req_udev udev >= 181-1
%global req_dm_persistent device-mapper-persistent-data >= 0.1.4
%endif

##############################################################
# same as FC 16 above, only with older udev

%if %{rhel} == 6
%define req_udev udev >= 147-2
%global req_dm_persistent device-mapper-persistent-data >= 0.1.4
%endif

##############################################################

# Do not reset Release to 1 unless both lvm2 and device-mapper
# versions are increased together.

%define device_mapper_version 1.02.93

Summary: Userland logical volume management tools
Name: lvm2
Version: 2.02.115
Release: 4%{?dist}
License: GPLv2
Group: System Environment/Base
URL: http://sources.redhat.com/lvm2
Source0: %{name}-%{version}.tar.bz2
Source91: source.inc
Source92: build.inc
Source93: packages.inc
Source94: macros.inc

BuildRequires: ncurses-devel
BuildRequires: readline-devel
BuildRequires: module-init-tools
BuildRequires: pkgconfig

# Expands to nothing unless at least 2 arguments are given
%define maybe() \
%if %(test -n "%{?2}" && echo 1 || echo 0) \
%* \
%endif
%define ifwith() \
%if %(if echo %{with_flags} | grep -q %1; then echo 1; else echo 0; fi)

BuildRequires: systemd-devel
%maybe BuildRequires: %{?buildreq_cluster}

%description
LVM2 includes all of the support for handling read/write operations on
physical volumes (hard disks, RAID-Systems, magneto optical, etc.,
multiple devices (MD), see mdadd(8) or even loop devices, see
losetup(8)), creating volume groups (kind of virtual disks) from one
or more physical volumes and creating one or more logical volumes
(kind of logical partitions) in volume groups.

# PatchN: nnn.patch goes here

%prep
%setup -n %{name}-%{version}/%{name}

%import build.inc
%import packages.inc

%changelog
