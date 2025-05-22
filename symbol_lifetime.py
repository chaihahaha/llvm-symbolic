import sympy as sp
from llvmlite import ir, binding

# Initialize LLVM
binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()

# Sample SymPy assignments
assignments = [
    ('A', 'B + C + D'),
    ('E', 'A + C + D'),
    ('F', 'E + B + C')
]

# LLVM IR Type for double
float_type = ir.DoubleType()

# Create an LLVM module and function
module = ir.Module(name="symbolic_optimization")
func_type = ir.FunctionType(ir.VoidType(), [])
function = ir.Function(module, func_type, name="compute")
block = function.append_basic_block(name="entry")
builder = ir.IRBuilder(block)

# Dictionary to map variable names to their allocated pointers in LLVM IR
var_map = {}

# Allocate memory for each variable only once
for lhs, rhs in assignments:
    if lhs not in var_map:
        var_map[lhs] = builder.alloca(float_type, name=lhs)
    for s in sp.sympify(rhs).free_symbols:
        s = str(s)
        if s not in var_map:
            var_map[s] = builder.alloca(float_type, name=s)
print('var_map', var_map)
# Convert SymPy assignments to LLVM IR
for lhs, expr_str in assignments:
    expr = sp.sympify(expr_str)
    print('expr',expr, expr.args)
    rhs_value = None

    # Recursively build the LLVM IR for the right-hand side of the expression
    def build_expr(e):
        if isinstance(e, sp.Symbol):
            # Load existing variable
            print('symbol', e)
            return builder.load(var_map[e.name])
        elif isinstance(e, sp.Add):
            # Handle addition by recursively evaluating the terms
            lhs = build_expr(e.args[0])
            rhs = build_expr(e.args[1])
            print('lhs rhs', lhs, rhs)
            return builder.fadd(lhs, rhs)
        elif isinstance(e, sp.Mul):
            # Handle multiplication similarly
            lhs = build_expr(e.args[0])
            rhs = build_expr(e.args[1])
            print('mul lhs rhs', lhs, rhs)
            return builder.fmul(lhs, rhs)
        # Extend to handle other operations (e.g., subtraction, division) if needed

    # Get the computed value for the right-hand side
    rhs_value = build_expr(expr)
    
    # Store the result in the left-hand side variable
    builder.store(rhs_value, var_map[lhs])

# Print the generated LLVM IR
print("Generated LLVM IR:")
print(module)

# Save the unoptimized IR to a .ll file
with open("unoptimized_module.ll", "w") as f:
    f.write(str(module))

#opt -mem2reg -O2 unoptimized_module.ll -o optimized_module.ll

#from llvmlite import binding
#
## Load the optimized IR file into llvmlite
#with open("optimized_module.ll", "r") as f:
#    optimized_ir = f.read()
#
## Parse the optimized IR into an llvmlite module
#optimized_module = binding.parse_assembly(optimized_ir)
#optimized_module.verify()
#
## Print the optimized IR
#print("Optimized LLVM IR:")
#print(optimized_module)


