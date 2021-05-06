from nmigen import *
from nmigen_cocotb import run
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clocl import Clock
from random import getrandbits

class Stream(Record):
	def __init__(self, width, **kwargs):
		# Define los buses:
		Record.__init__(self, [('data', width), ('valid', 1), ('ready', 1)], **kwargs)

	# Devuelve 1 si valid y ready estan seteados.
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
		self.a = Stream(width, name = 'a')
		self.b = Stream(width, name = 'b')
		self.r = Stream(width, name = 'r')