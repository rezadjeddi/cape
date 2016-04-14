#ifndef _PC_TRI_H
#define _PC_TRI_H

PyObject *
pc_WriteTri(PyObject *self, PyObject *args);
char doc_WriteTri[] =
"Write a Cart3D triangulation to :file:`Components.pyCart.tri` file\n"
"\n"
":Call:\n"
"    >>> pc.WriteTri(P, T)\n"
":Inputs:\n"
"    *P*: :class:`numpy.ndarray` (:class:`float`) (*nNode*, 3)\n"
"        Matrix of nodal coordinates\n"
"    *T*: :class:`numpy.ndarray` (:class:`int`) (*nTri*, 3)\n"
"        Matrix of of nodal indices for each triangle\n"
":Versions:\n"
"   * 2014-01-02 ``@ddalle``: First version\n";


PyObject *
pc_WriteCompID(PyObject *self, PyObject *args);
char doc_WriteCompID[] =
"Write component ID numbers to :file:`Components.pyCart.tri`\n"
"\n"
":Call:\n"
"    >>> pc.WriteCompID(C)\n"
":Inputs:\n"
"    *C*: :class:`numpy.ndarray` (:class:`int`) (*nTri*)\n"
"        Vector of component IDs\n"
":Versions:\n"
"   * 2014-01-02 ``@ddalle``: First version\n";


PyObject *
pc_WriteTriQ(PyObject *self, PyObject *args);
char doc_WriteTriQ[] =
"Write ``.triq`` file to :file:`Components.pyCart.tri`\n"
"\n"
":Call:\n"
"    >>> pc.WriteTriQ(P, T, C, Q)\n"
":Inputs:\n"
"    *P*: :class:`numpy.ndarray` (:class:`float`) (*nNode*, 3)\n"
"        Matrix of nodal coordinates\n"
"    *T*: :class:`numpy.ndarray` (:class:`int`) (*nTri*, 3)\n"
"        Matrix of of nodal indices for each triangle\n"
"    *C*: :class:`numpy.ndarray` (:class:`int`) (*nTri*)\n"
"        Vector of component IDs\n"
"    *Q*: :class:`numpy.ndarray` (:class:`float`) (*nNode*, *nq*)\n"
"        Matrix of states at each node\n"
":Versions:\n"
"    * 2015-09-24 ``@ddalle``: First version\n";

PyObject *
pc_WriteSurf(PyObject *self, PyObject *args);
char doc_WriteSurf[] =
"Write AFLR3 surface file to :file:`Components.pyCart.surf`\n"
"\n"
":Call:\n"
"    >>> pc_WriteSurf(P, blds, bldel, T, CT, BCT, Q, CQ, BCQ)\n"
":Inputs:\n"
"    *P*: :class:`numpy.ndarray` (:class:`float`) (*nNode*, 3)\n"
"        Matrix of nodal coordinates\n"
"    *T*: :class:`numpy.ndarray` (:class:`int`) (*nTri*, 3)\n"
"        Matrix of of nodal indices for each triangle\n"
"    *CT*: :class:`numpy.ndarray` (:class:`int`) (*nTri*)\n"
"        Vector of component IDs for each triangle\n"
"    *BCT*: :class:`numpy.ndarray` (:class:`int`) (*nTri*)\n"
"        Vector of AFLR3 boundary condition flags for each triangle\n"
"    *Q*: :class:`numpy.ndarray` (:class:`int`) (*nQuad*, 4)\n"
"        Matrix of of nodal indices for each quadrangle\n"
"    *CQ*: :class:`numpy.ndarray` (:class:`int`) (*nQuad*)\n"
"        Vector of component IDs for each quadrangle\n"
"    *BCQ*: :class:`numpy.ndarray` (:class:`int`) (*nQuad*)\n"
"        Vector of AFLR3 boundary condition flags for each quadrangle\n"
":Versions:\n"
"    * 2016-04-13 ``@ddalle``: First version\n";

PyObject *
pc_WriteTriSTL(PyObject *self, PyObject *args);
char doc_WriteTriSTL[] = 
"Write ``.stl`` file to :file:`Components.pyCart.stl`\n"
"\n"
":Call:\n"
"    >>> pc.WriteTriSTL(P, T, N)\n"
":Inputs:\n"
"    *P*: :class:`numpy.ndarray` (:class:`float`) (*nNode*, 3)\n"
"        Matrix of nodal coordinates\n"
"    *T*: :class:`numpy.ndarray` (:class:`int`) (*nTri*, 3)\n"
"        Matrix of of nodal indices for each triangle\n"
"    *N*: :class:`numpy.ndarray` (:class:`int`) (*nTri*, 3)\n"
"        Vector of triangle normals\n"
":Versions:\n"
"    * 2015-11-23 ``@ddalle``: First version\n";
#endif
