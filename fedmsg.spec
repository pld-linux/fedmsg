# TODO
# - --daemonize crashes (works under systemd only): https://github.com/fedora-infra/fedmsg/issues/302

# Conditional build:
%bcond_with	tests		# build with tests

Summary:	Tools for Fedora Infrastructure real-time messaging
Name:		fedmsg
Version:	0.17.0
Release:	1
License:	LGPL v2+
Group:		Applications/Networking
Source0:	http://pypi.python.org/packages/source/f/fedmsg/%{name}-%{version}.tar.gz
# Source0-md5:	a56ffea38fd83d1f1c2592363e6f764b
Source1:	%{name}-tmpfiles.conf
Source2:	%{name}-gateway.init
Source3:	%{name}-hub.init
Source4:	%{name}-irc.init
Source5:	%{name}-relay.init
Patch1:		config.patch
URL:		https://github.com/fedora-infra/fedmsg
BuildRequires:	python-devel
BuildRequires:	python-setuptools
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.710
%if %{with tests}
BuildRequires:	python-mock
BuildRequires:	python-nose
BuildRequires:	python-six
# Only for the test-replay test which is patched out
BuildRequires:	python-M2Crypto
BuildRequires:	python-arrow
BuildRequires:	python-bunch
BuildRequires:	python-daemon
BuildRequires:	python-fabulous
BuildRequires:	python-fedora
BuildRequires:	python-m2ext
BuildRequires:	python-moksha-hub >= 1.3.2
BuildRequires:	python-psutil
BuildRequires:	python-pygments
BuildRequires:	python-requests
#BuidlRequires:  python-sqlalchemy
%endif
Requires:	python-M2Crypto >= 0.22.5
Requires:	python-arrow
#Requires:	python-daemon
#Requires:	python-fabulous
#Requires:	python-fedora
Requires:	python-kitchen
Requires:	python-m2ext
Requires:	python-moksha-hub >= 1.3.2
Requires:	python-psutil
Requires:	python-pygments
Requires:	python-requests
#Requires:	python-simplejson
Requires:	python-six
Requires:	python-zmq
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Python API used around Fedora Infrastructure to send and receive
messages with zeromq. Includes some CLI tools.

%package announce
Summary:	The fedmsg-announce command
Group:		Applications/Networking
Requires:	%{name} = %{version}-%{release}

%description announce
This package contains the fedmsg-announce command for sending
announcements.

%package collectd
Summary:	A fedmsg plugin for collectd
Group:		Applications/Networking
Requires:	%{name} = %{version}-%{release}

%description collectd
This package contains the fedmsg-collectd command which produces
output suitable for consumption by a collectd plugin.

%package hub
Summary:	The FedMsg Hub
Group:		Applications/Networking
Requires:	rc-scripts >= 0.4.0.20
Requires(post,preun):	/sbin/chkconfig
Requires:	%{name} = %{version}-%{release}

%description hub
This package contains configuration and init scripts for the FedMsg
hub.

%package relay
Summary:	The FedMsg Relay
Group:		Applications/Networking
Requires:	%{name} = %{version}-%{release}
Requires:	rc-scripts >= 0.4.0.20
Requires(post,preun):	/sbin/chkconfig

%description relay
This package contains configuration and init scripts for the FedMsg
relay.

%package irc
Summary:	The FedMsg IRC Bot
Group:		Applications/Networking
Requires:	%{name} = %{version}-%{release}
Requires:	rc-scripts >= 0.4.0.20
Requires(post,preun):	/sbin/chkconfig

%description irc
This package contains configuration and init scripts for the FedMsg
IRC bot.

%package gateway
Summary:	The FedMsg Gateway daemon
Group:		Applications/Networking
Requires:	%{name} = %{version}-%{release}
Requires:	rc-scripts >= 0.4.0.20
Requires(post,preun):	/sbin/chkconfig

%description gateway
This package contains configuration and init scripts for the FedMsg
Gateway. It will rebroadcast messages from the bus to a specially
designated ZMQ pub socket. Useful for repeating messages outside a
firewall.

%prep
%setup -q
%patch1 -p1

# This only got shipped with fedmsg-0.6.3
rm -f fedmsg.d/_tweet-real.py

# These are failing in mock for fedora.  Investigate why.
# We probably just need a new BuildReq
rm -f fedmsg/tests/test_replay.py
rm -f fedmsg/tests/test_crypto_gpg.py

# Also, sqlalchemy is required for those tests we're knocking out,
# so knock it out too.
sed -i "/'sqlalchemy.*$/d" setup.py

sed -i "/cryptography/d" setup.py
sed -i "/daemon/d" setup.py

# Temporarily disable signature validation while the timestamp precision bug is
# worked out upstream. -- https://github.com/fedora-infra/fedmsg/pull/186
sed -i "s/validate_signatures=True/validate_signatures=False/g" fedmsg.d/ssl.py

# Copy the development config into the tests dir for the check section
cp -rf fedmsg.d fedmsg/tests/

%build
%py_build

# Create this temporary symlink that's only needed for the test suite.
ln -s fedmsg/tests/test_certs dev_certs

# Unfortunately, neither of these tests will run on koji since they require
# some network connectivity.  With a note of sadness, we destroy them.
rm fedmsg/tests/test_hub.py
rm fedmsg/tests/test_threads.py

%if %{with tests}
%check
%if 0%{?rhel} && 0%{?rhel} <= 6
# Check section removed until a RHEL6 bug with python-repoze-what-plugins-sql
# can be fixed.  It causes a fatal error in the test suite.
# https://bugzilla.redhat.com/show_bug.cgi?id=813925
%else
PYTHONPATH=$(pwd) python setup.py test
%endif
%endif

%install
rm -rf $RPM_BUILD_ROOT
%py_install \
    --install-data=%{_datadir} \
	--root $RPM_BUILD_ROOT

%{__rm} -r $RPM_BUILD_ROOT%{py_sitescriptdir}/fedmsg/tests

%py_postclean

install -d $RPM_BUILD_ROOT{/etc/{logrotate.d,rc.d/init.d},%{_sysconfdir}/fedmsg.d,%{systemdtmpfilesdir},%{systemdunitdir},/var/{run,log}/fedmsg}
cp -p fedmsg.d/*.py $RPM_BUILD_ROOT%{_sysconfdir}/fedmsg.d

install -p %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/fedmsg-gateway
install -p %{SOURCE3} $RPM_BUILD_ROOT/etc/rc.d/init.d/fedmsg-hub
install -p %{SOURCE4} $RPM_BUILD_ROOT/etc/rc.d/init.d/fedmsg-irc
install -p %{SOURCE5} $RPM_BUILD_ROOT/etc/rc.d/init.d/fedmsg-relay

cp -p initsys/systemd/fedmsg-hub.service $RPM_BUILD_ROOT%{systemdunitdir}
cp -p initsys/systemd/fedmsg-relay.service $RPM_BUILD_ROOT%{systemdunitdir}
cp -p initsys/systemd/fedmsg-irc.service $RPM_BUILD_ROOT%{systemdunitdir}
cp -p initsys/systemd/fedmsg-gateway.service $RPM_BUILD_ROOT%{systemdunitdir}

# Logrotate configuration
cp -p logrotate $RPM_BUILD_ROOT/etc/logrotate.d/fedmsg

# tmpfiles.d
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{systemdtmpfilesdir}/%{name}.conf

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 313 -r fedmsg
%useradd -u 313  -r -s /sbin/nologin -d %{_datadir}/%{name} -M -c 'FedMsg' -g fedmsg fedmsg

%post hub
/sbin/chkconfig --add fedmsg-hub
%service fedmsg-hub restart

%preun hub
if [ "$1" = "0" ]; then
	%service fedmsg-hub stop
	/sbin/chkconfig --del fedmsg-hub
fi

%post relay
/sbin/chkconfig --add fedmsg-relay
%service fedmsg-relay restart

%preun relay
if [ "$1" = "0" ]; then
	%service fedmsg-relay stop
	/sbin/chkconfig --del fedmsg-relay
fi

%post irc
/sbin/chkconfig --add fedmsg-irc
%service fedmsg-irc restart

%preun irc
if [ "$1" = "0" ]; then
	%service fedmsg-irc stop
	/sbin/chkconfig --del fedmsg-irc
fi

%post gateway
/sbin/chkconfig --add fedmsg-gateway
%service fedmsg-gateway restart

%preun gateway
if [ "$1" = "0" ]; then
	%service fedmsg-gateway stop
	/sbin/chkconfig --del fedmsg-gateway
fi

%files
%defattr(644,root,root,755)
%doc doc/* README.rst LICENSE
%dir %{_sysconfdir}/fedmsg.d
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/base.py*
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/endpoints.py*
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/logging.py*
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/ssl.py*
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/relay.py*
%config(noreplace) %verify(not md5 mtime size) /etc/logrotate.d/fedmsg
%attr(755,root,root) %{_bindir}/fedmsg-logger
%attr(755,root,root) %{_bindir}/fedmsg-tail
%attr(755,root,root) %{_bindir}/fedmsg-trigger
%attr(755,root,root) %{_bindir}/fedmsg-config
%attr(755,root,root) %{_bindir}/fedmsg-dg-replay
%attr(755,fedmsg,fedmsg) %dir /var/log/fedmsg
%attr(775,fedmsg,fedmsg) %dir /var/run/fedmsg
%dir %{py_sitescriptdir}/fedmsg
%{py_sitescriptdir}/fedmsg/*.py[co]
%{py_sitescriptdir}/fedmsg/commands
%{py_sitescriptdir}/fedmsg/consumers
%{py_sitescriptdir}/fedmsg/crypto
%{py_sitescriptdir}/fedmsg/encoding
%{py_sitescriptdir}/fedmsg/meta
%{py_sitescriptdir}/fedmsg/replay
%{py_sitescriptdir}/fedmsg/text
%{py_sitescriptdir}/fedmsg-%{version}-py*.egg-info
%{systemdtmpfilesdir}/%{name}.conf

%files announce
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fedmsg-announce

%files collectd
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fedmsg-collectd

%files hub
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fedmsg-hub
%attr(754,root,root) /etc/rc.d/init.d/fedmsg-hub
%{systemdunitdir}/fedmsg-hub.service

%files relay
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fedmsg-relay
%attr(754,root,root) /etc/rc.d/init.d/fedmsg-relay
%{systemdunitdir}/fedmsg-relay.service

%files irc
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fedmsg-irc
%attr(754,root,root) /etc/rc.d/init.d/fedmsg-irc
%{systemdunitdir}/fedmsg-irc.service

%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/ircbot.py*

%files gateway
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fedmsg-gateway
%attr(754,root,root) /etc/rc.d/init.d/fedmsg-gateway
%{systemdunitdir}/fedmsg-gateway.service
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fedmsg.d/gateway.py*
