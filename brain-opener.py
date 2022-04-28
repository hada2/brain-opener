#!/usr/bin/python

import sys, time, re
import curses

CELLSIZE = 0x10000
SKIP_INTERVAL = 500

class Machine:
    def __init__(self, filename):
        self.cell       = [0]*CELLSIZE*2
        self.position   = CELLSIZE
        self.cellLow    = CELLSIZE
        self.cellHigh   = CELLSIZE
        self.refreshCount = 0
        self.stack = []
        self.outBuf = ""
        self.code = open(filename).read()
        self.code = re.sub("[^+-><[].,]", "", self.code)

    def execute(self, stdscr, pc):
        ins = self.code[pc]

        if ins == "+":
            self.cell[self.position] += 1
            self.cell[self.position] &= 0xFF
            self.refreshCount += 1
            pcNext = pc + 1
        elif ins == "-":
            self.cell[self.position] -= 1
            self.cell[self.position] &= 0xFF
            self.refreshCount += 1
            pcNext = pc + 1
        elif ins == ">":
            self.position += 1
            self.cellHigh = max(self.cellHigh, self.position)
            pcNext = pc + 1
        elif ins == "<":
            self.position -= 1
            self.cellLow = min(self.cellLow, self.position)
            pcNext = pc + 1
        elif ins == "[":
            if self.cell[self.position] != 0:
                self.stack.append(pc)
                pcNext = pc + 1
            else:
                self.stack.append(pc)
                pcNext = self.exitLoop(pc)
        elif ins == "]":
            if self.cell[self.position] != 0:
                pcNext = self.stack.pop(-1)
            else:
                self.stack.pop(-1)
                pcNext = pc + 1
        elif ins == ".":
            self.outBuf += chr(self.cell[self.position])
            self.refreshCount += 1
            pcNext = pc + 1
        elif ins == ",":
            stdscr.addstr(1,  0, "input")
            input_num = stdscr.getkey()
            stdscr.clear()
            self.cell[self.position] = ord(input_num) if input_num else 0xa
            self.cell[self.position] &= 0xFF
            self.refreshCount += 1
            pcNext = pc + 1

        return pcNext

    def isActive(self, pc):
        return pc < len(self.code)

    def needRefresh(self, pcNext):
        return self.refreshCount % SKIP_INTERVAL == 0 or self.cell[pcNext] in [".", ","]

    def exitLoop(self, n):
        nestCnt = 1

        while nestCnt > 0:
            n += 1
            if self.code[n] == "[": nestCnt += 1
            if self.code[n] == "]": nestCnt -= 1

        return n

    def genHexDumpString(self):
        hexDump = ""

        start = self.cellLow - (self.cellLow % 16)
        end = self.cellHigh - (self.cellHigh % 16) + 16

        for i in range(start, end, 16):
            hexDump += f"{i:08x}  "

            for j in range(16):
                hexDump += " " if j == 8 else ""
                hexDump += f"{self.cell[i+j]:02x} "

            hexDump += "  "

            for j in range(16):
                hexDump += " " if j == 8 else ""
                c = self.cell[i+j]
                c = chr(c) if 0x20 <= c < 0x7F else "."
                hexDump += f"{c}"

            hexDump += "\n"

        return hexDump

    def showScreen(self, stdscr, pc):
        line = f"pc={pc}, code='{self.code[pc]}', "
        line += f"pos={self.position:x}, val={self.cell[self.position]}"
        line = line.ljust(100, " ")
        outMessage = self.outBuf.ljust(100, " ")
        hexDump = self.genHexDumpString()

        stdscr.addstr(0,  0, line)
        stdscr.addstr(2,  0, "="*78)
        stdscr.addstr(3,  0, outMessage)
        stdscr.addstr(7,  0, "="*78)
        stdscr.addstr(8,  0, hexDump)
        line_num = hexDump.count("\n")
        stdscr.addstr(line_num+8,  0, "="*78)

        stdscr.refresh()

def main(stdscr):
    pc = 0
    machine = Machine(sys.argv[1])

    while machine.isActive(pc):
        # break
        if pc in []: # put breakpoint here
            stdscr.addstr(1,  0, "break")
            stdscr.getkey()
            stdscr.clear()

        pcNext = machine.execute(stdscr, pc)

        if machine.needRefresh(pcNext):
            machine.showScreen(stdscr, pc)

        pc = pcNext

    input("")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        exit(1)

    curses.wrapper(main)




