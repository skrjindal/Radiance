/* Copyright (c) 1986 Regents of the University of California */

#ifndef lint
static char SCCSid[] = "$SunId$ LBL";
#endif

/*
 *  t_func.c - routine for procedural textures.
 *
 *     4/8/86
 */

#include  "ray.h"

/*
 *	A procedural texture perturbs the surface normal
 *  at the point of intersection with an object.  It has
 *  the form:
 *
 *	modifier texfunc name
 *	4+ xvarname yvarname zvarname filename xf
 *	0
 *	n A1 A2 ..
 *
 *  Filename is the name of the file where the variable definitions
 *  can be found.  The list of real arguments can be accessed by
 *  definitions in the file.  The xf is a transformation to get
 *  from the original coordinates to the current coordinates.
 */

typedef struct {
	struct {
		double  sca;		/* scale factor */
		double  xfm[4][4];	/* transformation matrix */
	}  fore, back;
}  XFORM;


t_func(m, r)			/* compute texture for ray */
register OBJREC  *m;
register RAY  *r;
{
#define  mxf	((XFORM *)m->os)
	extern double  varvalue();
	extern int  errno;
	FVECT  disp;
	register int  i;
	register char  **sa;

	if (m->oargs.nsargs < 4)
		objerror(m, USER, "bad # arguments");
	sa = m->oargs.sarg;

	if (mxf == NULL) {
		mxf = (XFORM *)malloc(sizeof(XFORM));
		if (mxf == NULL)
			goto memerr;
		mxf->fore.sca = 1.0;
		setident4(mxf->fore.xfm);
		if (xf(mxf->fore.xfm, &mxf->fore.sca,
			m->oargs.nsargs-4, sa+4) != m->oargs.nsargs-4)
			objerror(m, USER, "bad transform");
		if (mxf->fore.sca < 0.0)
			mxf->fore.sca = -mxf->fore.sca;
		mxf->back.sca = 1.0;
		setident4(mxf->back.xfm);
		invxf(mxf->back.xfm, &mxf->back.sca,
				m->oargs.nsargs-4, sa+4);
		if (mxf->back.sca < 0.0)
			mxf->back.sca = -mxf->back.sca;
	}

	setmap(m, r, mxf->back.sca, mxf->back.xfm);

	if (!vardefined(sa[0]))
		loadfunc(sa[3]);
	errno = 0;
	for (i = 0; i < 3; i++)
		disp[i] = varvalue(sa[i]);
	if (errno) {
		objerror(m, WARNING, "compute error");
		return;
	}
	if (mxf->fore.xfm == NULL)
		for (i = 0; i < 3; i++)
			r->pert[i] += disp[i];
	else
		for (i = 0; i < 3; i++)
			r->pert[i] += (	disp[0]*mxf->fore.xfm[0][i] +
					disp[1]*mxf->fore.xfm[1][i] +
					disp[2]*mxf->fore.xfm[2][i] )
						/ mxf->fore.sca;
	return;
memerr:
	error(SYSTEM, "out of memory in t_func");
#undef  mxf
}
