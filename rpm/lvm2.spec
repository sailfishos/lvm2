# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# This spec file has been adapted for Mer builds from default upstream
# spec file and include files.

%global _default_pid_dir /run
%global _default_dm_run_dir /run
%global _default_run_dir /run/lvm
%global _default_locking_dir /run/lock/lvm
# Install UDEV rules to /lib/udev/rules.d instead of /usr/... because of our
# systemd installation looking for the rules there.
%global _udevbasedir /lib/udev
%global _udevdir %{_udevbasedir}/rules.d

%define enableif() \
%global configure_flags %{?configure_flags} --%(if test %1 -gt 0; then echo enable-%2; else echo disable-%2; fi)

# Default Mer settings.
# NOTE: 1. Udev rule for operation completion is broken, fix if you enable udev
# NOTE: 2. Systemd services have not been tested. In Mer we are not restarting
#          systems on install phase so we should reconsider all those when this
#          gets enabled.
# NOTE: 3. We use LVM2's version also for device mapper due to how Mer releasing
#          works (git tag is the version string for all packages in git repo).
#          So make sure when there is device-mapper feature dependency that you
#          "Require" to the tagged git version numbers, not to VERSION_DM

%global enable_profiling 0
%global enable_udev 1
%global enable_systemd 0
%global enable_lvmetad 0

Summary: Userland logical volume management tools
Name: lvm2
Version: 2.02.177
Release: 1
License: GPLv2
Group: System/Base
URL: http://www.sourceware.org/lvm2
Source0: %{name}-%{version}.tar.bz2

BuildRequires: ncurses-devel
BuildRequires: kmod
# libudev lives now in systemd so require systemd-devel when udev support
# is enabled too.
%if %{enable_systemd}%{enable_udev}
BuildRequires: pkgconfig(systemd)
%endif
Requires: %{name}-libs = %{version}-%{release}


%description
LVM2 includes all of the support for handling read/write operations on
physical volumes (hard disks, RAID-Systems, magneto optical, etc.,
multiple devices (MD), see mdadd(8) or even loop devices, see
losetup(8)), creating volume groups (kind of virtual disks) from one
or more physical volumes and creating one or more logical volumes
(kind of logical partitions) in volume groups.

# PatchN: nnn.patch goes here


%package doc
Summary:   Documentation for %{name}
Group:     Documentation
Requires:  %{name} = %{version}-%{release}

%description doc
Man pages for %{name} and device-mapper.


%prep
%setup -n %{name}-%{version}/%{name}

# UDEV_SYNC doesn't work in initramfs because we don't have udev there yet.
# Should be enabled after fixing UDEV in initramfs.
#% enableif %{enable_udev} udev_sync
# Disabling udev_sync by default disables UDEV rules installing too.
# But we need it.
%enableif %{enable_udev} udev-rules
%enableif %{enable_profiling} profiling
%enableif %{enable_lvmetad} lvmetad

%build
%configure \
  --with-default-dm-run-dir=%{_default_dm_run_dir} \
  --with-default-run-dir=%{_default_run_dir} \
  --with-default-pid-dir=%{_default_pid_dir} \
  --with-default-locking-dir=%{_default_locking_dir} \
  --with-usrlibdir=%{_libdir} \
  --enable-lvm1_fallback \
  --enable-fsadm \
  --with-pool=internal \
  --with-user= \
  --with-group= \
  --with-device-uid=0 \
  --with-device-gid=6 \
  --with-device-mode=0660 \
  --with-cache=internal \
  --with-thin=internal \
  --with-thin_check=%{_sbindir}/thin_check \
  --with-thin_check=%{_sbindir}/thin_check \
  --with-thin_repair=%{_sbindir}/thin_repair \
  --with-thin_dump=%{_sbindir}/thin_dump \
  --enable-pkgconfig \
  --enable-applib \
  --enable-cmdlib \
  --enable-dmeventd \
  --disable-readline \
%if %{enable_udev}
  --with-udevdir=%{_udevdir} \
%endif
  %{configure_flags}

make %{?_smp_mflags}
%{?extra_build_commands}

%install
make install DESTDIR=$RPM_BUILD_ROOT
make install_system_dirs DESTDIR=$RPM_BUILD_ROOT
%if %{enable_systemd}
make install_systemd_units DESTDIR=$RPM_BUILD_ROOT
make install_tmpfiles_configuration DESTDIR=$RPM_BUILD_ROOT
%endif

mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}/
install -m0644 -t $RPM_BUILD_ROOT%{_docdir}/%{name}-%{version}/ \
    INSTALL README VERSION* WHATS_NEW* doc/lvm_fault_handling.txt \
    udev/12-dm-permissions.rules

%check
%{?check_commands}

### MAIN PACKAGE (lvm2)

%post
/sbin/ldconfig
%if %{enable_systemd}
/bin/systemctl daemon-reload > /dev/null 2>&1 || :
/bin/systemctl enable lvm2-monitor.service > /dev/null 2>&1 || :
%if %{enable_lvmetad}
/bin/systemctl enable lvm2-lvmetad.socket > /dev/null 2>&1 || :
%endif
%endif

%preun
%if %{enable_systemd}
if [ "$1" = 0 ]; then
  /bin/systemctl --no-reload disable lvm2-monitor.service > /dev/null 2>&1 || :
  /bin/systemctl stop lvm2-monitor.service > /dev/null 2>&1 || :
  %if %{enable_lvmetad}
  /bin/systemctl --no-reload disable lvm2-lvmetad.lvmetad > /dev/null 2>&1 || :
  /bin/systemctl stop lvm2-lvmetad.lvmetad > /dev/null 2>&1 || :
  %endif
fi
%endif

%postun
%if %{enable_systemd}
/bin/systemctl daemon-reload > /dev/null 2>&1 || :

if [ $1 -ge 1 ]; then
  /bin/systemctl try-restart lvm2-monitor.service > /dev/null 2>&1 || :
  %if %{enable_lvmetad}
  /bin/systemctl try-restart lvm2-lvmetad.service > /dev/null 2>&1 || :
  %endif
fi
%endif

# files in the main package

%files
%defattr(-,root,root,-)
%license COPYING COPYING.LIB
%{_sbindir}/fsadm
%{_sbindir}/lvchange
%{_sbindir}/lvconvert
%{_sbindir}/lvcreate
%{_sbindir}/lvdisplay
%{_sbindir}/lvextend
%{_sbindir}/lvm
%{_sbindir}/lvmconfig
%{_sbindir}/lvmdiskscan
%{_sbindir}/lvmdump
%{_sbindir}/lvmsadc
%{_sbindir}/lvmsar
%{_sbindir}/lvreduce
%{_sbindir}/lvremove
%{_sbindir}/lvrename
%{_sbindir}/lvresize
%{_sbindir}/lvs
%{_sbindir}/lvscan
%{_sbindir}/pvchange
%{_sbindir}/pvck
%{_sbindir}/pvcreate
%{_sbindir}/pvdisplay
%{_sbindir}/pvmove
%{_sbindir}/pvremove
%{_sbindir}/pvresize
%{_sbindir}/pvs
%{_sbindir}/pvscan
%{_sbindir}/vgcfgbackup
%{_sbindir}/vgcfgrestore
%{_sbindir}/vgchange
%{_sbindir}/vgck
%{_sbindir}/vgconvert
%{_sbindir}/vgcreate
%{_sbindir}/vgdisplay
%{_sbindir}/vgexport
%{_sbindir}/vgextend
%{_sbindir}/vgimport
%{_sbindir}/vgimportclone
%{_sbindir}/vgmerge
%{_sbindir}/vgmknodes
%{_sbindir}/vgreduce
%{_sbindir}/vgremove
%{_sbindir}/vgrename
%{_sbindir}/vgs
%{_sbindir}/vgscan
%{_sbindir}/vgsplit
%{_sbindir}/lvmconf
%{_sbindir}/blkdeactivate
%if %{enable_lvmetad}
 %{_sbindir}/lvmetad
%endif
%if %{enable_udev}
 %{_udevdir}/11-dm-lvm.rules
 %if %{enable_lvmetad}
  %{_udevdir}/69-dm-lvm-metad.rules
 %endif
%endif
%dir %{_sysconfdir}/lvm
%ghost %{_sysconfdir}/lvm/cache/.cache
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/lvm.conf
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/lvmlocal.conf
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/cache-mq.profile
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/cache-smq.profile
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/lvmdbusd.profile
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/command_profile_template.profile
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/metadata_profile_template.profile
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/thin-generic.profile
%config %verify(not md5 mtime size) %{_sysconfdir}/lvm/profile/thin-performance.profile
%dir %{_sysconfdir}/lvm/backup
%dir %{_sysconfdir}/lvm/cache
%dir %{_sysconfdir}/lvm/archive
%if %{enable_systemd}
 %config %{_prefix}/lib/tmpfiles.d/%{name}.conf
 %{_unitdir}/lvm2-monitor.service
 %if %{enable_lvmetad}
  %{_unitdir}/lvm2-lvmetad.socket
  %{_unitdir}/lvm2-lvmetad.service
  %{_unitdir}/lvm2-pvscan@.service
  %{_unitdir}/blk-availability.service
 %endif
%endif

##############################################################################
# Library and Development subpackages
##############################################################################
%package devel
Summary: Development libraries and headers
Group: Development/Libraries
License: LGPLv2
Requires: %{name} = %{version}-%{release}
Requires: device-mapper-devel >= %{version}-%{release}
Requires: device-mapper-event-devel >= %{version}-%{release}

%description devel
This package contains files needed to develop applications that use
the lvm2 libraries.

%files devel
%defattr(-,root,root,-)
%{_libdir}/liblvm2app.so
%{_libdir}/liblvm2cmd.so
%{_includedir}/lvm2app.h
%{_includedir}/lvm2cmd.h
%{_libdir}/pkgconfig/lvm2app.pc
%{_libdir}/libdevmapper-event-lvm2.so

%package libs
Summary: Shared libraries for lvm2
License: LGPLv2
Group: System/Libraries
Requires: device-mapper-event >= %{version}-%{release}

%description libs
This package contains shared lvm2 libraries for applications.

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%files libs
%defattr(-,root,root,-)
%attr(755,root,root) %{_libdir}/liblvm2app.so.*
%attr(755,root,root) %{_libdir}/liblvm2cmd.so.*
%attr(755,root,root) %{_libdir}/libdevmapper-event-lvm2.so.*
%dir %{_libdir}/device-mapper
%{_libdir}/device-mapper/libdevmapper-event-lvm2mirror.so
%{_libdir}/device-mapper/libdevmapper-event-lvm2snapshot.so
%{_libdir}/device-mapper/libdevmapper-event-lvm2raid.so
%{_libdir}/device-mapper/libdevmapper-event-lvm2thin.so
%{_libdir}/libdevmapper-event-lvm2thin.so
%{_libdir}/libdevmapper-event-lvm2mirror.so
%{_libdir}/libdevmapper-event-lvm2snapshot.so
%{_libdir}/libdevmapper-event-lvm2raid.so

##############################################################################
# Device-mapper subpackages
##############################################################################
%package -n device-mapper
Summary: Device mapper utility
Release: %{release}
License: GPLv2
Group: System/Base
URL: http://sources.redhat.com/dm
Requires: device-mapper-libs = %{version}-%{release}
Requires: util-linux >= 2.15
%if %{enable_udev}
Requires: udev >= 181-1
%endif

%description -n device-mapper
This package contains the supporting userspace utility, dmsetup,
for the kernel device-mapper.

%files -n device-mapper
%defattr(-,root,root,-)
%license COPYING COPYING.LIB
%attr(755,root,root) %{_sbindir}/dmsetup
%attr(755,root,root) %{_sbindir}/dmstats
%if %{enable_udev}
%dir %{_udevbasedir}
%dir %{_udevdir}
%{_udevdir}/10-dm.rules
%{_udevdir}/13-dm-disk.rules
%{_udevdir}/95-dm-notify.rules
%endif

%package -n device-mapper-devel
Summary: Development libraries and headers for device-mapper
Release: %{release}
License: LGPLv2
Group: Development/Libraries
Requires: device-mapper = %{version}-%{release}

%description -n device-mapper-devel
This package contains files needed to develop applications that use
the device-mapper libraries.

%files -n device-mapper-devel
%defattr(-,root,root,-)
%{_libdir}/libdevmapper.so
%{_includedir}/libdevmapper.h
%{_libdir}/pkgconfig/devmapper.pc

%package -n device-mapper-libs
Summary: Device-mapper shared library
Release: %{release}
License: LGPLv2
Group: System/Libraries
Requires: device-mapper = %{version}-%{release}

%description -n device-mapper-libs
This package contains the device-mapper shared library, libdevmapper.

%post -n device-mapper-libs -p /sbin/ldconfig

%postun -n device-mapper-libs -p /sbin/ldconfig

%files -n device-mapper-libs
%attr(755,root,root) %{_libdir}/libdevmapper.so.*

%package -n device-mapper-event
Summary: Device-mapper event daemon
Group: System/Base
Release: %{release}
Requires: device-mapper = %{version}-%{release}
Requires: device-mapper-event-libs = %{version}-%{release}
%if %{enable_systemd}
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif

%description -n device-mapper-event
This package contains the dmeventd daemon for monitoring the state
of device-mapper devices.

%post -n device-mapper-event
%if %{enable_systemd}
/bin/systemctl daemon-reload > /dev/null 2>&1 || :
/bin/systemctl enable dm-event.socket > /dev/null 2>&1 || :
%endif

%preun -n device-mapper-event
%if %{enable_systemd}
if [ "$1" = 0 ]; then
	/bin/systemctl --no-reload disable dm-event.service dm-event.socket > /dev/null 2>&1 || :
	/bin/systemctl stop dm-event.service dm-event.socket> /dev/null 2>&1 || :
fi
%endif

%postun -n device-mapper-event
%if %{enable_systemd}
/bin/systemctl daemon-reload > /dev/null 2>&1 || :
if [ $1 -ge 1 ]; then
	/bin/systemctl reload dm-event.service > /dev/null 2>&1 || :
fi
%endif

%files -n device-mapper-event
%defattr(-,root,root,-)
%{_sbindir}/dmeventd
%if %{enable_systemd}
%{_unitdir}/dm-event.socket
%{_unitdir}/dm-event.service
%endif

%package -n device-mapper-event-libs
Summary: Device-mapper event daemon shared library
Release: %{release}
License: LGPLv2
Group: System/Libraries

%description -n device-mapper-event-libs
This package contains the device-mapper event daemon shared library,
libdevmapper-event.

%post -n device-mapper-event-libs -p /sbin/ldconfig

%postun -n device-mapper-event-libs -p /sbin/ldconfig

%files -n device-mapper-event-libs
%attr(755,root,root) %{_libdir}/libdevmapper-event.so.*

%package -n device-mapper-event-devel
Summary: Development libraries and headers for the device-mapper event daemon
Release: %{release}
License: LGPLv2
Group: Development/Libraries
Requires: device-mapper-event = %{version}-%{release}

%description -n device-mapper-event-devel
This package contains files needed to develop applications that use
the device-mapper event library.

%files -n device-mapper-event-devel
%defattr(-,root,root,-)
%{_libdir}/libdevmapper-event.so
%{_includedir}/libdevmapper-event.h
%{_libdir}/pkgconfig/devmapper-event.pc

%files doc
%defattr(-,root,root,-)
%{_mandir}/man7/lvmcache.7.gz
%{_mandir}/man7/lvmraid.7.gz
%{_mandir}/man7/lvmreport.7.gz
%{_mandir}/man7/lvmsystemid.7.gz
%{_mandir}/man7/lvmthin.7.gz
%{_mandir}/man5/lvm.conf.5.gz
%{_mandir}/man8/fsadm.8.gz
%{_mandir}/man8/lvchange.8.gz
%{_mandir}/man8/lvconvert.8.gz
%{_mandir}/man8/lvcreate.8.gz
%{_mandir}/man8/lvdisplay.8.gz
%{_mandir}/man8/lvextend.8.gz
%{_mandir}/man8/lvm.8.gz
%{_mandir}/man8/lvmconf.8.gz
%{_mandir}/man8/lvm-config.8.gz
%{_mandir}/man8/lvm-fullreport.8.gz
%{_mandir}/man8/lvm-lvpoll.8.gz
%{_mandir}/man8/lvmconf.8.gz
%{_mandir}/man8/lvmconfig.8.gz
%{_mandir}/man8/lvmdiskscan.8.gz
%{_mandir}/man8/lvmdump.8.gz
%{_mandir}/man8/lvmsadc.8.gz
%{_mandir}/man8/lvmsar.8.gz
%{_mandir}/man8/lvreduce.8.gz
%{_mandir}/man8/lvremove.8.gz
%{_mandir}/man8/lvrename.8.gz
%{_mandir}/man8/lvresize.8.gz
%{_mandir}/man8/lvs.8.gz
%{_mandir}/man8/lvscan.8.gz
%{_mandir}/man8/pvchange.8.gz
%{_mandir}/man8/pvck.8.gz
%{_mandir}/man8/pvcreate.8.gz
%{_mandir}/man8/pvdisplay.8.gz
%{_mandir}/man8/pvmove.8.gz
%{_mandir}/man8/pvremove.8.gz
%{_mandir}/man8/pvresize.8.gz
%{_mandir}/man8/pvs.8.gz
%{_mandir}/man8/pvscan.8.gz
%{_mandir}/man8/vgcfgbackup.8.gz
%{_mandir}/man8/vgcfgrestore.8.gz
%{_mandir}/man8/vgchange.8.gz
%{_mandir}/man8/vgck.8.gz
%{_mandir}/man8/vgconvert.8.gz
%{_mandir}/man8/vgcreate.8.gz
%{_mandir}/man8/vgdisplay.8.gz
%{_mandir}/man8/vgexport.8.gz
%{_mandir}/man8/vgextend.8.gz
%{_mandir}/man8/vgimport.8.gz
%{_mandir}/man8/vgimportclone.8.gz
%{_mandir}/man8/vgmerge.8.gz
%{_mandir}/man8/vgmknodes.8.gz
%{_mandir}/man8/vgreduce.8.gz
%{_mandir}/man8/vgremove.8.gz
%{_mandir}/man8/vgrename.8.gz
%{_mandir}/man8/vgs.8.gz
%{_mandir}/man8/vgscan.8.gz
%{_mandir}/man8/vgsplit.8.gz
%{_mandir}/man8/blkdeactivate.8.gz
%{_mandir}/man8/lvm-dumpconfig.8.gz
%{_mandir}/man8/dmeventd.8.gz
%{_mandir}/man8/dmsetup.8.gz
%{_mandir}/man8/dmstats.8.gz
%if %{enable_udev}
 %if %{enable_lvmetad}
  %{_mandir}/man8/lvmetad.8.gz
 %endif
%endif
%doc %{_docdir}/%{name}-%{version}
