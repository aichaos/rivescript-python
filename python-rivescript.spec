%global srcname rivescript
%global sum A Chatterbot Scripting Language
%global desc A scripting language to make it easy to write responses for a chatterbot.

Name:           python-%{srcname}
Version:        1.14.2
Release:        1%{?dist}
Summary:        %{sum}

License:        MIT
URL:            http://pypi.python.org/pypi/%{srcname}
Source0:        http://pypi.python.org/packages/source/r/%{srcname}/%{srcname}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python2-devel python3-devel

%description
%{desc}


%package -n python2-%{srcname}
Summary:        %{sum}
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
%{desc}


%package -n python3-%{srcname}
Summary:       %{sum}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
%{desc}


%prep
%autosetup -n %{srcname}-%{version}

%build
%py2_build
%py3_build

%install
# Must do the Python2 install first because the scripts in /usr/bin are
# overwritten with every setup.py install, and in general we want the
# Python3 version to be the default.
%py2_install
%py3_install

%check
%{__python2} setup.py test
%{__python3} setup.py test

# Note that there is no %%files section for the unversioned python module if
# we are building for several python runtimes
%files -n python2-%{srcname}
%license LICENSE
%doc README.md
%{python2_sitelib}/*

%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/*

%changelog
