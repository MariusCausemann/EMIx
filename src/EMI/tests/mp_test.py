from numpy import isclose
import time
from dolfin import *
from multiphenics import *
from sys   import argv

N = int(argv[1])
print("N = ", N)
P = 1

# Mesh generation
mesh = UnitIntervalMesh(N)

class Left(SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary and abs(x[0] - 0.) < DOLFIN_EPS

class Right(SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary and abs(x[0] - 1.) < DOLFIN_EPS

boundaries = MeshFunction("size_t", mesh, mesh.topology().dim() - 1)
boundaries.set_all(0)
left = Left()
left.mark(boundaries, 1)
right = Right()
right.mark(boundaries, 1)

x0 = SpatialCoordinate(mesh)[0]

def run_standard():

    # Define a function space
    V = FunctionSpace(mesh, "Lagrange", P)
    u = TrialFunction(V)
    v = TestFunction(V)

    # Create the matrix for the LHS
    a = inner(grad(u), grad(v))*dx + u*v*dx

    # Create the vector for the RHS
    f = 100*sin(20*x0)*v*dx

    tic = time.perf_counter()   
    A = assemble(a)
    F = assemble(f)
    print(f"Assemble in run_standard() in: {time.perf_counter() - tic:0.4f} seconds")   

    # Apply boundary conditions
    bc = DirichletBC(V, Constant(0.), boundaries, 1)
    bc.apply(A)
    bc.apply(F)

    # Solve the linear system
    U = Function(V)    

    tic = time.perf_counter()  
    solve(A, U.vector(), F)
    print(f"Solve in run_standard() in: {time.perf_counter() - tic:0.4f} seconds")   

    # Return the solution
    # return U


def run_block():


    # Define a block function space
    tic = time.perf_counter()
    V = FunctionSpace(mesh, "Lagrange", P)
    VV = BlockFunctionSpace([V, V])
    uu = BlockTrialFunction(VV)
    vv = BlockTestFunction(VV)
    (u1, u2) = block_split(uu)
    (v1, v2) = block_split(vv)

    print(f"Spaces in run_block() in: {time.perf_counter() - tic:0.4f} seconds")   

    # Create the block matrix for the block LHS
    aa = [[1*inner(grad(u1), grad(v1))*dx + 1*u1*v1*dx, 2*inner(grad(u2), grad(v1))*dx + 2*u2*v1*dx],
          [3*inner(grad(u1), grad(v2))*dx + 3*u1*v2*dx, 4*inner(grad(u2), grad(v2))*dx + 4*u2*v2*dx]]
    
    # Create the block vector for the block RHS
    ff = [300*sin(20*x0)*v1*dx,
          700*sin(20*x0)*v2*dx]
    

    tic = time.perf_counter()
    AA = block_assemble(aa)
    FF = block_assemble(ff)
    print(f"Assemble in run_block() in: {time.perf_counter() - tic:0.4f} seconds")   

    tic = time.perf_counter()
    # Apply block boundary conditions
    bc1 = DirichletBC(VV.sub(0), Constant(0.), boundaries, 1)
    bc2 = DirichletBC(VV.sub(1), Constant(0.), boundaries, 1)
    bcs = BlockDirichletBC([bc1,bc2])
    bcs.apply(AA)
    bcs.apply(FF)

    print(f"bcs() in: {time.perf_counter() - tic:0.4f} seconds")   

    # Solve the block linear system
    UU = BlockFunction(VV)

    tic = time.perf_counter()  
    block_solve(AA, UU.block_vector(), FF)
    print(f"Solve in run_block() in: {time.perf_counter() - tic:0.4f} seconds")   

    UU1, UU2 = UU

    # Return the block solution
    # return UU1, UU2

# test
run_standard()
run_block()
