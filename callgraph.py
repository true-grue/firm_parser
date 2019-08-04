# Call graph construction example

import sys
from firm_parser import parse


def locate(s):
    line = s.buf.count("\n", 0, s.epos)
    col = s.epos - (s.buf.rfind("\n", 0, s.epos) + 1)
    return line, col


def error(msg, s):
    line, col = locate(s)
    print("%d:%d: %s" % (line + 1, col + 1, msg))
    sys.exit(1)


def parse_ir(source):
    return parse(source, lambda s: error("error!", s))


def process_ir(ir):
    names = {}
    funcs = {}
    for g in ir:
        if g[0] == "typegraph":
            for t in g:
                if t[0] == "method":
                    names[t[1]] = t[2]["ident"]
        elif g[0] == "irg":
            funcs[g[1]] = g[3]
    return names, funcs


def build_graph(names, funcs):
    graph = {}
    for idx in funcs:
        addrs = {}
        lst = []
        for f in funcs[idx]:
            if f[0] == "Address" and f[2] in names:
                addrs[f[1]] = names[f[2]]
        for f in funcs[idx]:
            if f[0] == "Call" and f[4] in addrs:
                name = addrs[f[4]]
                if name not in lst:
                    lst.append(name)
        graph[names[idx]] = lst
    return graph


def import_to_gv(graph):
    lines = ["digraph {"]
    for s in graph:
        for d in graph[s]:
            lines.append("%s -> %s;" % (s, d))
    lines.append("}")
    return "\n".join(lines)


with open(sys.argv[1]) as f:
    source = f.read()

ir = parse_ir(source)
names, funcs = process_ir(ir)
graph = build_graph(names, funcs)
print(import_to_gv(graph))
