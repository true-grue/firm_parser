# libFirm parser
# Author: Peter Sovietov

from raddsl_parse import *

comment = seq(a("#"), many(non(a("\n"))))
ws = many(alt(space, comment))
num = seq(quote(opt(a("-")), some(digit)), to(1, int))
L = alt(letter, a("_"))
name = quote(seq(L, many(alt(L, digit))))
string = seq(a('"'), quote(many(alt(non(one_of('"\\')), seq(a("\\"), any)))),
             a('"'))
hexnum = seq(quote(some(alt(digit, one_of("abcdefABCDEF")))),
             to(1, lambda x: int(x, 16)))


def token(f): return memo(seq(ws, f))


def k(t): return token(quote(a(t)))


def o(t): return seq(k(t), drop)


def attrs(n): return to(1, lambda a: dict(zip(n, a)))


def switch(s):
    n = s.out.pop()
    return group(repeat(group(num, mode, hexnum, mode, hexnum), n))(s)


num = token(num)
hexnum = token(hexnum)
name = token(name)
string = token(string)
mode = string
typeref = alt(num, k("unknown"), k("code"))
lst = group(o("["), many(alt(num, name)), o("]"))
unop = seq(num, num)
binop = seq(num, num, num)
ANCHOR = """
end_block start_block end start frame initial_mem args no_mem
""".split()
NODES = dict(
    Anchor=seq(lst, attrs(ANCHOR)),
    Add=binop,
    Address=num,
    Alloc=seq(num, num, num, num),
    And=binop,
    Bitcast=seq(num, num, mode),
    Block=lst,
    Call=seq(num, num, num, typeref, name, name, lst),
    Cmp=seq(num, num, num, num),
    Cond=seq(num, num, name),
    CopyB=seq(num, num, num, num, typeref, name),
    Const=seq(mode, hexnum),
    Conv=seq(num, num, mode),
    Div=seq(num, num, num, num, mode, num, name, name),
    End=lst,
    Eor=binop,
    IJmp=unop,
    Jmp=num,
    Load=seq(num, num, num, mode, typeref, name, name, name, name),
    Member=binop,
    Minus=unop,
    Mod=seq(num, num, num, num, mode, name, name),
    Mul=binop,
    Mulh=binop,
    Mux=seq(num, num, num, num),
    NoMem=empty,
    Not=unop,
    Or=binop,
    Pin=unop,
    Phi=seq(num, mode, name, lst),
    Proj=seq(num, mode, num),
    Return=seq(num, num, lst),
    Shl=binop,
    Shr=binop,
    Shrs=binop,
    Start=empty,
    Store=seq(num, num, num, num, typeref, name, name, name, name),
    Sub=binop,
    Switch=seq(num, num, num, num, switch),
    Sync=seq(num, lst),
    Unknown=mode
)


def do_node(s): return NODES[s.out[-2]](s)


def args(s):
    flags, outs, ins = s.out.pop(), s.out.pop(), s.out.pop()
    s.out.append(flags)
    return seq(group(repeat(num, ins)), group(repeat(num, outs)))(s)


def compound(s): return seq(repeat(init, s.out.pop()))(s)


int_mode = group(k("int_mode"), string, name, num, num, num)
ref_mode = group(k("reference_mode"), string, name, num, num, string, num)
float_mode = group(k("float_mode"), string, name, num, num, num)
modes = group(k("modes"), o("{"), many(alt(int_mode, ref_mode, float_mode)),
              o("}"))
TY_PRIMITIVE = """
typ size align state flags mode
""".split()
TY_ARRAY = """
typ size align state flags element_type array_size
""".split()
TY_COMPOUND = """
typ size align state flags ident
""".split()
TY_POINTER = """
typ size align state flags points_to
""".split()
TY_METHOD = """
typ size align state flags calling_convention additional_properties
variadic params results
""".split()
ty_prim = seq(group(k("primitive"), num, num, name, num, string),
              attrs(TY_PRIMITIVE))
ty_array = seq(group(k("array"), num, num, name, num, num, num),
               attrs(TY_ARRAY))
ty_class = seq(group(k("class"), num, num, name, num, string),
               attrs(TY_COMPOUND))
ty_segment = seq(group(k("segment"), num, num, name, num, string),
                 attrs(TY_COMPOUND))
ty_pointer = seq(group(k("pointer"), num, num, name, num, num),
                 attrs(TY_POINTER))
ty_method = seq(group(k("method"), num, num, name, num, num, num,
                      num, num, num, args), attrs(TY_METHOD))
ty_struct = seq(group(k("struct"), num, num, name, num, string),
                attrs(TY_COMPOUND))
ty_union = seq(group(k("union"), num, num, name, num, string),
               attrs(TY_COMPOUND))
ty = group(k("type"), num, alt(
           ty_prim, ty_array, ty_class, ty_segment, ty_pointer, ty_method,
           ty_struct, ty_union))
init_null = group(k("IR_INITIALIZER_NULL"))
init_const = group(k("IR_INITIALIZER_CONST"), num)
init_tarval = group(k("IR_INITIALIZER_TARVAL"), string, hexnum)
init_compound = group(k("IR_INITIALIZER_COMPOUND"), num, compound)
init = alt(init_null, init_const, init_tarval, init_compound)
ENT_NORMAL = """
ident ld_ident visibility linkage typ owner volatility
initializer init
""".split()
ENT_METHOD = """
ident ld_ident visibility linkage typ owner volatility
additional_properties
""".split()
COMPOUND_MEMBER = """
ident ld_ident visibility linkage typ owner volatility
offset bitfield_offset bitfield_size
""".split()
PARAMETER = """
visibility linkage typ owner volatility
number offset bitfield_offset bitfield_size
""".split()
ent_init = alt(k("none"), seq(name, init))
ent_normal = group(
    k("entity"),
    num, group(string, string, name, lst,
               num, num, name, ent_init), attrs(ENT_NORMAL))
ent_method = group(
    k("method"),
    num, group(string, string, name, lst,
               num, num, name, num), attrs(ENT_METHOD))
ent_member = group(
    k("compound_member"),
    num, group(string, string, name, lst,
               num, num, name, num, num, num), attrs(COMPOUND_MEMBER))
ent_parameter = group(
    k("parameter"),
    num, group(name, lst,
               num, num, name, num, num, num, num), attrs(PARAMETER))
entity = alt(ent_normal, ent_method, ent_member, ent_parameter)
unknown = group(k("unknown"), num, to(0, lambda: dict(typ=None)))
typegraph = group(k("typegraph"), o("{"), many(alt(ty, entity, unknown)),
                  o("}"))
node = group(name, guard(lambda x: x in NODES.keys()), num, do_node)
nodes = group(many(node))
irg = group(k("irg"), num, num, o("{"), nodes, o("}"))
constirg = group(k("constirg"), num, o("{"), nodes, o("}"))
segment_type = group(k("segment_type"), name, num)
asm = group(k("asm"), string)
program = group(k("program"), o("{"), many(alt(segment_type, asm)), o("}"))
main = seq(many(alt(modes, typegraph, irg, constirg, program)), ws, end)


def parse(text, error):
    s = Stream(text)
    return s.out if main(s) else error(s)
