from athena.generators.autogen_op_name_and_arg_names import op_name_x_arg_names


def GetCOpsArgNames(op_name):
    ret = op_name2arg_names.get(op_name, None)
    if ret is not None:
        return ret
    if op_name[-1] != "_":
        return None
    return op_name2arg_names.get(op_name[0:-1], None)


op_name2args = {op_name: args for op_name, *args in op_name_x_arg_names}

op_name2arg_names = {
    op_name: [a[1] for a in args] for op_name, *args in op_name_x_arg_names
}
