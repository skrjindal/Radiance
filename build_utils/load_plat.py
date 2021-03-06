from __future__ import division, print_function, unicode_literals

import os
import sys
import re
import platform
try: import configparser # Py3
except ImportError:
	import ConfigParser as configparser # Py2

_platdir = 'platform'


def read_plat(env, fn):
	envdict = env.Dictionary().copy()
	# can't feed configparser the original dict, because it also
	# contains non-string values.
	for k,v in list(envdict.items()): # make a list, so we can change the dict.
		if not isinstance(v, str):
			del envdict[k]
	cfig = configparser.ConfigParser(envdict)
	cfig.read(fn)
	buildvars = [['CC',
			'TIFFINCLUDE', # where to find preinstalled tifflib headers
			'TIFFLIB',     # where to find a preinstalled tifflib library
			], # replace
			['CPPPATH', 'CPPDEFINES', 'CPPFLAGS', 'CCFLAGS',
			'LIBS', 'LIBPATH', 'LINKFLAGS',
			'EZXML_CPPDEFINES', # build flags specific to ezxml.c
			]] # append
	vars = [
		['install',
			['RAD_BASEDIR', 'RAD_BINDIR', 'RAD_RLIBDIR', 'RAD_MANDIR'],
			[]],
		['code',
			[   # replace
			],
			[   # append
			'RAD_COMPAT',     # theoretically obsolete (src/common/strcmp.c)
			'RAD_MATHCOMPAT', # erf.c floating point error function
			'RAD_ARGSCOMPAT', # fixargv0.c for Windows
			'RAD_NETCOMPAT',  # [win_]netproc.c for ranimate
			'RAD_MLIB',       # usually 'm', or any fastlib available
			'RAD_SOCKETLIB',  # ws_2_32 on Windows (VC links it automatically)
			'RAD_PROCESS',    # our process abstraction and win_popen()
			'RAD_PCALLS',     # more custom process abstraction
			]],
	]
	if env.get('RAD_DEBUG',0) not in(0,'0','','n','no','false',False,None):
		vars.insert(0, ['debug'] + buildvars)
		print('Processing DEBUG version')
	else:
		vars.insert(0, ['build'] + buildvars)
		print('Processing RELEASE version')
	for section in vars:
		if cfig.has_section(section[0]):
			for p in section[1]: # single items to replace
				try: v = cfig.get(section[0], p)
				except configparser.NoOptionError: continue
				if section[0] in ('install','build','debug'):
					if '{' in v:
						v = subst_sysenvvars(v, env)
				env[p] = v
				#print('%s: %s' % (p, env[p]))
			for p in section[2]: # multiple items to append
				try:
					v = cfig.get(section[0], p)
					if section[0] in ('build','debug') and '{' in v:
						v = subst_sconsvars(v, env)
					#print('%s: %s - %s' % (section[0], p, v))
				except configparser.NoOptionError: continue
				env.Append(*[], **{p:env.Split(v)})
				#apply(env.Append,[],{p:env.Split(v)})

def combine_instpaths(env):
	# XXX Check that basedir exists?
	for k in ['RAD_BINDIR', 'RAD_RLIBDIR', 'RAD_MANDIR']:
		if (env.has_key('RAD_BASEDIR') and env.has_key(k)
				and not os.path.isabs(env[k])):
			env[k] = os.path.join(env['RAD_BASEDIR'],env[k])



def subst_sysenvvars(s, env):
	try: return s.format(**os.environ)
	except KeyError: return s

def subst_sconsvars(s, env,
		pat=re.compile('({[a-z0-9_]+})', re.I)):
	l = pat.split(s)
	nl = []
	for ss in l:
		if ss.startswith('{') and ss.endswith('}'):
			v = env.get(ss[1:-1])
			#print(ss, v)
			if v:
				if v.startswith('#'):
					v = str(env.Dir(v))
				nl.append(v)
				continue
		nl.append(ss)
	return ''.join(nl)


def identify_plat(env):
	memmodel, binformat = platform.architecture()
	platsys = platform.system()
	print('Detected platform "%s" (%s).' % (platsys, memmodel))
	cfgname = platsys + '_' + memmodel[:2]
	env['CFG_PLATSYS'] = platsys
	env['CFG_MEMMODEL'] = memmodel[:2]
	env['CFG_PATHFILE'] = os.path.join('#scbuild', cfgname, 'install_paths.py')
	env['CFG_OPTFILE']  = os.path.join('#scbuild', cfgname, 'build_opts.py')


def load_plat(env, testenv):
	platsys = testenv['CFG_PLATSYS']
	memmodel = testenv['CFG_MEMMODEL']
	cfgname = platsys + '_' + memmodel[:2]

	env['RAD_BUILDBIN'] = os.path.join('#scbuild', cfgname, 'bin')
	env['RAD_BUILDLIB'] = os.path.join('#scbuild', cfgname, 'lib')
	env['RAD_BUILDOBJ'] = os.path.join('#scbuild', cfgname, 'obj')

	cust_pfn = os.path.join(_platdir, cfgname + '_custom.cfg')
	if os.path.isfile(cust_pfn):
		print('Reading configuration "%s"' % cust_pfn)
		read_plat(env, cust_pfn)
		return 1
	pfn = os.path.join(_platdir, cfgname + '.cfg')
	if os.path.isfile(pfn):
		print('Reading configuration "%s"' % pfn)
		read_plat(env, pfn)
		return 1

	if os.name == 'posix':
		pfn = os.path.join(_platdir, 'posix.cfg')
		if os.path.isfile(pfn):
			print('No platform specific configuration found.\n')
			print('Reading generic configuration "%s".' % pfn)
			read_plat(env, pfn)
			return 1

	print('Platform "%s", system "%s" not supported yet'
			% (os.name, sys.platform))
	sys.exit(2)

# vi: set ts=4 sw=4 :
