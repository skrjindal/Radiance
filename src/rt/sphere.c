/* Copyright (c) 1986 Regents of the University of California */

#ifndef lint
static char SCCSid[] = "$SunId$ LBL";
#endif

/*
 *  sphere.c - compute ray intersection with spheres.
 *
 *     8/19/85
 */

#include  "ray.h"

#include  "otypes.h"


o_sphere(so, r)			/* compute intersection with sphere */
OBJREC  *so;
register RAY  *r;
{
	double  a, b, c;	/* coefficients for quadratic equation */
	double  root[2];	/* quadratic roots */
	int  nroots;
	double  t;
	register double  *ap;
	register int  i;

	if (so->oargs.nfargs != 4 || so->oargs.farg[3] <= FTINY)
		objerror(so, USER, "bad arguments");

	ap = so->oargs.farg;

	/*
	 *	We compute the intersection by substituting into
	 *  the surface equation for the sphere.  The resulting
	 *  quadratic equation in t is then solved for the
	 *  smallest positive root, which is our point of
	 *  intersection.
	 *	Because the ray direction is normalized, a is always 1.
	 */

	a = 1.0;		/* compute quadratic coefficients */
	b = c = 0.0;
	for (i = 0; i < 3; i++) {
		t = r->rorg[i] - ap[i];
		b += 2.0*r->rdir[i]*t;
		c += t*t;
	}
	c -= ap[3] * ap[3];

	nroots = quadratic(root, a, b, c);	/* solve quadratic */
	
	for (i = 0; i < nroots; i++)		/* get smallest positive */
		if ((t = root[i]) > FTINY)
			break;
	if (i >= nroots)
		return(0);			/* no positive root */

	if (t < r->rot) {			/* found closer intersection */
		r->ro = so;
		r->rot = t;
						/* compute normal */
		a = ap[3];
		if (so->otype == OBJ_BUBBLE)
			a = -a;			/* reverse */
		for (i = 0; i < 3; i++) {
			r->rop[i] = r->rorg[i] + r->rdir[i]*t;
			r->ron[i] = (r->rop[i] - ap[i]) / a;
		}
		r->rod = -DOT(r->rdir, r->ron);
	}
	return(1);
}
