
from nmigen import *
from nmigen_cocotb import run
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
from random import getrandbits

class Stream(Record):
    def __init__(self, width, **kwargs):
        Record.__init__(self, [('data', width), ('valid', 1), ('ready', 1)], **kwargs)

    def accepted(self):
        return self.valid & self.ready

    class Driver:
        def __init__(self, clk, dut, prefix):
            self.clk = clk
            self.data = getattr(dut, prefix + 'data')
            self.valid = getattr(dut, prefix + 'valid')
            self.ready = getattr(dut, prefix + 'ready')

        async def send(self, data):
            self.valid <= 1
            for d in data:
                self.data <= d
                await RisingEdge(self.clk)
                while self.ready.value == 0:
                    await RisingEdge(self.clk)
            self.valid <= 0

        async def recv(self, count):
            self.ready <= 1
            data = []
            for _ in range(count):
                await RisingEdge(self.clk)
                while self.valid.value == 0:
                    await RisingEdge(self.clk)
                data.append(self.data.value.integer)
            self.ready <= 0
            return data


class Adder(Elaboratable):
    def __init__(self, width):
        self.a = Stream(width, name='a')
        self.b = Stream(width, name='b')
        self.r = Stream(width + 1, name='r')

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        with m.If(self.r.accepted()):
            sync += self.r.valid.eq(0)

        comb += self.a.ready.eq((~self.r.valid) | (self.r.accepted()))   
        comb += self.b.ready.eq((~self.r.valid) | (self.r.accepted()))   

        with m.If(self.a.accepted() & self.b.accepted()):
            sync += [self.r.valid.eq(1), self.r.data.eq(self.a.data + self.b.data)]

        return m

async def init_test(dut):
    cocotb.fork(Clock(dut.clk, 2, 'ns').start()) # 500 millones p/seg
    dut.rst <= 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst <= 0

## 1er test
@cocotb.test(stage = 0)
async def test_duplicador(dut):
    await init_test(dut)

    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    N = 2 ** len(dut.a__data)
    mask = int('1' * (len(dut.a__data) + 1), 2)

    data_a = [_ for _ in range(N)]
    data_b = [_ for _ in range(N)]
    expected = [(2*i) & mask for i in range(N)]
    cocotb.fork(stream_input_b.send(data_b))
    cocotb.fork(stream_input_a.send(data_a))

    recved = await stream_output.recv(N)
    assert recved == expected

## Otro test
@cocotb.test(stage = 1)
async def test_iguales(dut):
    await init_test(dut)

    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    N = 2**len(dut.a__data)
    mask = int('1' * (len(dut.a__data) + 1), 2)

    data_a = [_ for _ in range(N)]
    data_b = [0 for _ in range(N)]
    expected = [d_a & mask for d_a in data_a]

    cocotb.fork(stream_input_b.send(data_b))
    cocotb.fork(stream_input_a.send(data_a))

    recved = await stream_output.recv(N)

    assert recved == expected

@cocotb.test(stage = 3)
async def test_negativos(dut):
    await init_test(dut)

    N = 100
    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')
    
    width = len(dut.a__data)

    data_a = [getrandbits(width) for _ in range(N)]
    data_b = [getrandbits(width) for _ in range(N)]
    # Todos los nros a negativo. De esta manera evito ponerle un negativo a un 0. 
    for a, b in zip(data_a, data_b):
        if a != 0 or b != 0:
            a = -a
            b = -b

    mask = int('1' * (len(dut.a__data) + 1), 2)
    expected = [(d_a + d_b) & mask for d_a, d_b in zip(data_a, data_b)]

    cocotb.fork(stream_input_a.send(data_a))
    cocotb.fork(stream_input_b.send(data_b))
    recved = await stream_output.recv(N)

    #print('a = {} \nb = {}'.format(data_a, data_b))
    #print('Esperado: {}'.format(expected))
    #print('Recibido: {}'.format(recved))

    assert recved == expected

## 4to test
@cocotb.test(stage = 4)
async def test_positivo_negativo(dut):
    await init_test(dut)

    stream_input_a = Stream.Driver(dut.clk, dut, 'a__')
    stream_input_b = Stream.Driver(dut.clk, dut, 'b__')
    stream_output = Stream.Driver(dut.clk, dut, 'r__')

    N = 100
    width = len(dut.a__data)
    mask = int('1' * (width + 1), 2)
    mask1 = int('1' * (width ), 2)

    data_a = [getrandbits(width) for _ in range(N)]
    data_b = [-getrandbits(width) for _ in range(N)]
    for d_b in data_b:
        if d_b != 0 :
            d_b = -d_b

    expected = [(d_a + (d_b & mask1)) & mask for d_a, d_b in zip(data_a, data_b)]
    cocotb.fork(stream_input_b.send(data_b))
    cocotb.fork(stream_input_a.send(data_a))

    recved = await stream_output.recv(N)
    #print('a = {} \nb = {}'.format(data_a, data_b))
    #print('Esperado: {}'.format(expected))
    #print('Recibido: {}'.format(recved))

    assert recved == expected

if __name__ == '__main__':
    core = Adder(4)
    run(
        core, 'ej1',
        ports=
        [
            *list(core.a.fields.values()),
            *list(core.r.fields.values()),
            *list(core.b.fields.values())
        ],
        vcd_file='adder.vcd'
    )  
