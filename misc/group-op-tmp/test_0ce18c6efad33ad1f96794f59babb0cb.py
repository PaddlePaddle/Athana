import os
os.environ['FLAGS_cinn_new_group_scheduler'] = '1'
os.environ['FLAGS_group_schedule_tiling_first'] = '1'
os.environ['FLAGS_prim_all'] = 'true'
os.environ['FLAGS_prim_enable_dynamic'] = '1'
os.environ['FLAGS_enable_pir_api'] = '1'
os.environ['FLAGS_cinn_bucket_compile'] = '1'

import unittest
import numpy as np
import paddle

def NumCurrentUnittestOperations():
    return 9 # number-of-ops

def GetPaddleDebugNumAllowedOps():
    try:
        return int(os.getenv('PADDLE_DEBUG_NUM_ALLOWED_OPS'))
    except:
        return None

def GetEnvVarEnableJit():
    enable_jit = os.getenv('PADDLE_DEBUG_ENABLE_JIT')
    return enable_jit not in {
        "0",
        "False",
        "false",
        "OFF",
    }

def GetEnvVarEnableCinn():
    enable_cinn = os.getenv('PADDLE_DEBUG_ENABLE_CINN')
    return enable_cinn not in {
        "0",
        "False",
        "false",
        "OFF",
    }


paddle_debug_num_allowed_ops = GetPaddleDebugNumAllowedOps()

if type(paddle_debug_num_allowed_ops) is not int:
    def EarlyReturn(i):
        return False
else:
    def EarlyReturn(i):
        return i >= paddle_debug_num_allowed_ops

class GroupOp(paddle.nn.Layer):
    def __init__(self):
        super().__init__()

    def forward(self, arg_0, arg_1):
        args = [arg_0, arg_1]
        for op_idx, op_func in enumerate(self.get_op_funcs()):
            if EarlyReturn(op_idx):
                return args
            args = op_func(*args)
        return args

    def get_op_funcs(self):
        return [
            self.op_exp_0,
            self.op_subtract_0,
            self.op_reduce_sum_0,
            self.op_scale_0,
            self.op_full_0,
            self.op_greater_than_0,
            self.op_full_1,
            self.op_less_than_0,
            self.op_logical_and_0,
        ]

    def op_exp_0(self, arg_0, arg_1):

        # EarlyReturn(0)
    
        #    op: pd_op.exp
        #  type: (1x-1x768xf32) <- (1x-1x768xf32)
        # shape: ([1, S0, 768]) <- ([1, S0, 768])
        #  data: (None) <- (None)
        exp_0 = paddle.exp(arg_0)

        return [arg_0, arg_1, exp_0]

    def op_subtract_0(self, arg_0, arg_1, exp_0):

        # EarlyReturn(1)
    
        #    op: pd_op.subtract
        #  type: (1x-1x768xf32) <- (1x-1x768xf32, 1x-1x768xf32)
        # shape: ([1, S0, 768]) <- ([1, S0, 768], [1, S0, 768])
        #  data: (None) <- (None, None)
        subtract_0 = exp_0 - arg_0

        return [arg_1, subtract_0]

    def op_reduce_sum_0(self, arg_1, subtract_0):

        # EarlyReturn(2)
    
        #    op: cinn_op.reduce_sum
        #  type: (xf32) <- (1x-1x768xf32)
        # shape: ([]) <- ([1, S0, 768])
        #  data: (None) <- (None)
        reduce_sum_0 = paddle.sum(subtract_0, keepdim=False, axis=[])

        return [arg_1, subtract_0, reduce_sum_0]

    def op_scale_0(self, arg_1, subtract_0, reduce_sum_0):

        # EarlyReturn(3)
    
        #    op: cinn_op.scale
        #  type: (1xf32) <- (1xf32)
        # shape: ([1]) <- ([1])
        #  data: (None) <- (None)
        scale_0 = arg_1 * 1 + 1

        return [subtract_0, reduce_sum_0, scale_0]

    def op_full_0(self, subtract_0, reduce_sum_0, scale_0):

        # EarlyReturn(4)
    
        #    op: pd_op.full
        #  type: (1xf32) <- ()
        # shape: ([1]) <- ()
        #  data: ([0]) <- ()
        full_0 = paddle.full(shape=[1], dtype='float32', fill_value=0)

        return [subtract_0, reduce_sum_0, scale_0, full_0]

    def op_greater_than_0(self, subtract_0, reduce_sum_0, scale_0, full_0):

        # EarlyReturn(5)
    
        #    op: pd_op.greater_than
        #  type: (1xb) <- (xf32, 1xf32)
        # shape: ([1]) <- ([], [1])
        #  data: (None) <- (None, [0])
        greater_than_0 = reduce_sum_0 > full_0

        return [subtract_0, scale_0, greater_than_0]

    def op_full_1(self, subtract_0, scale_0, greater_than_0):

        # EarlyReturn(6)
    
        #    op: pd_op.full
        #  type: (1xf32) <- ()
        # shape: ([1]) <- ()
        #  data: ([1]) <- ()
        full_1 = paddle.full(shape=[1], dtype='float32', fill_value=1)

        return [subtract_0, scale_0, greater_than_0, full_1]

    def op_less_than_0(self, subtract_0, scale_0, greater_than_0, full_1):

        # EarlyReturn(7)
    
        #    op: pd_op.less_than
        #  type: (1xb) <- (1xf32, 1xf32)
        # shape: ([1]) <- ([1], [1])
        #  data: (None) <- (None, [1])
        less_than_0 = scale_0 < full_1

        return [subtract_0, scale_0, greater_than_0, less_than_0]

    def op_logical_and_0(self, subtract_0, scale_0, greater_than_0, less_than_0):

        # EarlyReturn(8)
    
        #    op: pd_op.logical_and
        #  type: (1xb) <- (1xb, 1xb)
        # shape: ([1]) <- ([1], [1])
        #  data: (None) <- (None, None)
        logical_and_0 = paddle.logical_and(greater_than_0, less_than_0)

        return [subtract_0, scale_0, logical_and_0]


class TestGroupOp(unittest.TestCase):
    def setUp(self):
        paddle.seed(2024)
        self.prepare_data()

    def prepare_data(self):
        self.inputs = [
            paddle.to_tensor([-1], dtype='float32').reshape([1]),
            paddle.zeros([1], dtype='bool'),
        ]
        for input in self.inputs:
          input.stop_gradient = True

    def apply_to_static(self, net, use_cinn):
        build_strategy = paddle.static.BuildStrategy()
        input_spec = [
            paddle.static.InputSpec(shape=[1], dtype='float32'),
            paddle.static.InputSpec(shape=[1], dtype='bool'),
        ]
        build_strategy.build_cinn_pass = use_cinn
        return paddle.jit.to_static(
            net,
            input_spec=input_spec,
            build_strategy=build_strategy,
            full_graph=True,
        )

    def train(self, use_cinn):
        net = GroupOp()
        net.eval()
        if GetEnvVarEnableJit():
            net = self.apply_to_static(net, use_cinn)
        out = net(*self.inputs)
        return out

    def test_train(self):
        dy_outs = self.train(use_cinn=False)
        cinn_outs = self.train(use_cinn=GetEnvVarEnableCinn())

        for cinn_out, dy_out in zip(cinn_outs, dy_outs):
          if type(cinn_out) is list and type(dy_out) is list:
            for x, y in zip(cinn_out, dy_out):
              self.assert_all_close(x, y)
          else:
            self.assert_all_close(cinn_out, dy_out)

    def assert_all_close(self, x, y):
        if (hasattr(x, "numpy") and hasattr(y, "numpy")):
            x_numpy = x.numpy()
            y_numpy = y.numpy()
            assert x_numpy.dtype == y_numpy.dtype
            if IsInteger(x_numpy.dtype):
                np.testing.assert_equal(x_numpy, y_numpy)
            else:
                tol = GetTolerance(x_numpy.dtype)
                np.testing.assert_allclose(x_numpy, y_numpy, atol=tol, rtol=tol)
        else:
            assert x == y

def GetTolerance(dtype):
    if dtype == np.float16:
        return GetFloat16Tolerance()
    if dtype == np.float32:
        return GetFloat32Tolerance()
    return 1e-6

def GetFloat16Tolerance():
    try:
        return float(os.getenv('PADDLE_DEBUG_FLOAT16_TOL'))
    except:
        return 1e-3

def GetFloat32Tolerance():
    try:
        return float(os.getenv('PADDLE_DEBUG_FLOAT32_TOL'))
    except:
        return 1e-6

def IsInteger(dtype):
    return np.dtype(dtype).char in np.typecodes['AllInteger']

if __name__ == '__main__':
    unittest.main()