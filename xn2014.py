import os
import argparse
import struct

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        
        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        #read instruction memory
        #return 32 bit hex val
        startPos = (ReadAddress//4)*4
        content = []
        for i in range(4):
            content += self.IMem[startPos+i]
        content = hex(int(''.join(content),2))
        return content
        # pass
          
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        numRemain = MemSize-len(self.DMem)
        for i in range(numRemain):
            self.DMem.append('00000000')

    def readInstr(self, ReadAddress):
        #read data memory
        #return 32 bit hex val
        startPos = (ReadAddress//4)*4
        content = []
        for i in range(4):
            content += self.DMem[startPos+i]
        content = hex(self.getImmValue(''.join(content)))
        return content
        # pass

    def getImmValue(self, imm):
        # extend the imm value to 32 bit binary string
        # then convert to signed integer
        result = 0
        for i in range(len(imm)):
            if i==0:
                result += -(2**(len(imm)-1))*int(imm[i])
            else:
                result += 2**(len(imm)-1-i)*int(imm[i])
        return result

    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        startPos = (Address//4)*4
        # convert hex value to binary value, truncate the 0b, fill with length 32
        BinaryData = bin(int(WriteData,16))[2:].zfill(32)
        for i in range(4):
            self.DMem[startPos+i] = BinaryData[8*i:8*i+8]
        # pass
                     
    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = ['0x00000000' for i in range(32)]
    
    def readRF(self, Reg_addr):
        # Fill in
        if Reg_addr>=0 and Reg_addr<32:
            return self.Registers[Reg_addr]
        else:
            print("Read Register Number Out Of Bound")
        # pass
    
    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in
        # Wrt_reg_data is a hex str value
        if Reg_addr>=0 and Reg_addr<32:
            self.Registers[Reg_addr] = Wrt_reg_data
        else:
            print("Write Register Number Out Of Bound")
        # pass
         
    def outputRF(self, cycle):
        # solve negative number: two's complement
        op = ["-"*70+"\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        # output in hex format
        # op.extend([str(val)+"\n" for val in self.Registers])
        # output in binary format
        op.extend([self.getSigned32bit(val)+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

    def getSigned32bit(self, hex_str):
        # return binary str, 32bit, signed
        int_value = int(hex_str,16)
        if int_value >=0:
            return bin(int_value)[2:].zfill(32)
        else:
            return bin(int_value & 0xffffffff)[2:].zfill(32)
        # pass    

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": True, "Instr": ''}
        self.EX = {"nop": True, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False,  "rd_mem": 0, 
                   "wrt_mem": 0, "alu_op": 0, "alu_control":0, "wrt_enable": 0}
        self.MEM = {"nop": True, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, 
                   "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": True, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.numInstructions = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

    def getImmValue(self, imm):
        # extend the imm value to 32 bit binary string
        # then convert to signed integer
        result = 0
        for i in range(len(imm)):
            if i==0:
                result += -(2**(len(imm)-1))*int(imm[i])
            else:
                result += 2**(len(imm)-1-i)*int(imm[i])
        return result

    

class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"

    def step(self):
        # Your implementation
        self.halted = False
        # IF stage
        self.numInstructions += 1
        instruction = bin(int(self.ext_imem.readInstr(self.state.IF.get("PC")),16))[2:].zfill(32)
        # PC + 4
        if self.state.IF["PC"]<len(self.ext_imem.IMem)-4 and instruction[25:32]!='1111111':
            self.nextState.IF["PC"] = self.state.IF["PC"] + 4
        else:
            self.nextState.IF["PC"] = self.state.IF["PC"]
        # ID stage
        # R-type instructions[6:0]
        if instruction[25:32] == '0110011':
            # add, sub
            rs2 = int(instruction[7:12],2)
            rs1 = int(instruction[12:17],2)
            rd = int(instruction[20:25],2)
            if instruction[17:20] == '000':
                # add
                if instruction[0:7] == '0000000':
                    addResult = int(self.myRF.readRF(rs2),16) + int(self.myRF.readRF(rs1),16)
                    addResult = hex(addResult)
                    self.myRF.writeRF(rd,addResult)
                    # pass
                # sub
                else:
                    subResult = int(self.myRF.readRF(rs1),16) - int(self.myRF.readRF(rs2),16)
                    subResult = hex(subResult)
                    self.myRF.writeRF(rd,subResult)
                    # pass
            # xor
            elif instruction[17:20] == '100':
                result = int(self.myRF.readRF(rs2),16)^int(self.myRF.readRF(rs1),16)
                result = hex(result)
                self.myRF.writeRF(rd, result)
                # pass
            # or
            elif instruction[17:20] == '110':
                result = int(self.myRF.readRF(rs2),16)|int(self.myRF.readRF(rs1),16)
                result = hex(result)
                self.myRF.writeRF(rd,result)
                # pass
            # and
            elif instruction[17:20] == '111':
                result = int(self.myRF.readRF(rs2),16)&int(self.myRF.readRF(rs1),16)
                result = hex(result)
                self.myRF.writeRF(rd,result)
                # pass
        # I-type instruction[6:0]
        elif instruction[25:32] == '0010011':
            imm = self.getImmValue(instruction[0:12])
            rs1 = int(instruction[12:17],2)
            rd = int(instruction[20:25],2)
            # addi
            if instruction[17:20] == '000':
                result = int(self.myRF.readRF(rs1),16) + imm
                result = hex(result)
                self.myRF.writeRF(rd, result)
                # pass
            # xori
            elif instruction[17:20] == '100':
                result = int(self.myRF.readRF(rs1),16) ^ imm
                result = hex(result)
                self.myRF.writeRF(rd, result)
                # pass
            # ori
            elif instruction[17:20] == '110':
                result = int(self.myRF.readRF(rs1),16) | imm
                result = hex(result)
                self.myRF.writeRF(rd, result)
                # pass
            # andi
            elif instruction[17:20] == '111':
                result = int(self.myRF.readRF(rs1),16) & imm
                result = hex(result)
                self.myRF.writeRF(rd, result)
                # pass
        # JAL instruction[6:0]
        elif instruction[25:32] == '1101111':
            # rearrange imm num here
            imm = instruction[0]+instruction[12:19]+instruction[11]+instruction[1:11]+'0'
            imm = self.getImmValue(imm)
            rd = int(instruction[20:25],2)
            self.myRF.writeRF(rd, hex(self.state.IF["PC"]+4))
            self.nextState.IF["PC"] = self.state.IF["PC"] + imm
            # pass
        # U-type instruction[6:0]
        elif instruction[25:32] == '1100011':
            # beq
            imm = instruction[0]+instruction[24]+instruction[1:7]+instruction[20:24]+'0'
            imm = self.getImmValue(imm)
            rs2 = int(instruction[7:12],2)
            rs1 = int(instruction[12:17],2)
            if instruction[17:20] == '000':
                if self.myRF.readRF(rs1)==self.myRF.readRF(rs2):
                    self.nextState.IF["PC"] = self.state.IF["PC"] + imm
                # pass
            # bne 
            elif instruction[17:20] == '001':
                if self.myRF.readRF(rs1)!=self.myRF.readRF(rs2):
                    self.nextState.IF["PC"] = self.state.IF["PC"] + imm
                # pass
        # LW instruction
        elif instruction[25:32] == '0000011':
            imm = self.getImmValue(instruction[0:12])
            rs1 = int(instruction[12:17],2)
            rd = int(instruction[20:25],2)
            readAddress = int(self.myRF.readRF(rs1),16) + imm
            self.myRF.writeRF(rd,self.ext_dmem.readInstr(readAddress))
            # pass
        # SW instruction
        elif instruction[25:32] == '0100011':
            imm = instruction[0:7]+instruction[20:25]
            imm = self.getImmValue(imm)
            rs2 = int(instruction[7:12],2)
            rs1 = int(instruction[12:17],2)
            writeAddress = int(self.myRF.readRF(rs1),16) + imm
            content = hex(int(self.myRF.readRF(rs2),16))
            self.ext_dmem.writeDataMem(writeAddress, content)
            # pass
        # Halt
        elif instruction[25:32] == '1111111':
            self.nextState.IF["nop"] = True
            # pass

        #-----------------------
        if self.state.IF["nop"]:
            self.halted = True
            
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
            
        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.nextState = State() #Brand New State
        self.cycle += 1
        
    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/FS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_FS.txt"
        self.endOfFile = False

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------
        if self.state.WB["nop"] == False:
            if self.state.WB["wrt_enable"] == 1:
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], hex(self.state.WB["Wrt_data"]))
        # --------------------- MEM stage --------------------
        self.nextState.WB["nop"] = self.state.MEM["nop"]
        if self.state.MEM["nop"] == False:
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"] # if wrt_enable is false, then this must be a SW instruction
            self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"] # if wrt is enabled, then write to Wrt_reg_addr, else ignore
            if self.state.MEM["rd_mem"] == 1: # LW instruction
                # wrt_reg_addr is an integer

                self.nextState.WB["Wrt_data"] = int(self.ext_dmem.readInstr(self.state.MEM["ALUresult"]),16)
                self.nextState.WB["Rs"] = self.state.MEM["Rs"]
                self.nextState.WB["Rt"] = self.state.MEM["Rt"]
            elif self.state.MEM["wrt_mem"] == 1: # SW instruction
                self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"],hex(self.state.MEM["Store_data"])) # put Store_data to ALUresult which has the write address
            # else must be R type or I type, has no access to memory,(MEM stage do nothing) move on the WB
            else:
                 self.nextState.WB["Wrt_data"] = self.state.MEM["ALUresult"]
        # --------------------- EX stage ---------------------
        self.nextState.MEM["nop"] = self.state.EX["nop"]
        if self.state.EX["nop"] == False:
            if self.state.EX["alu_op"] == 0b10: # R-type
                if self.state.EX["alu_control"]==0b0010: # add
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + self.state.EX["Read_data2"]
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = self.state.EX["Rt"]
                    self.nextState.MEM["Store_data"] = 0
                    self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                    self.nextState.MEM["rd_mem"] = 0
                    self.nextState.MEM["wrt_mem"] = 0
                    self.nextState.MEM["wrt_enable"] = 1
                elif self.state.EX["alu_control"]==0b0110: #subtract
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] - self.state.EX["Read_data2"]
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = self.state.EX["Rt"]
                    self.nextState.MEM["Store_data"] = 0
                    self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                    self.nextState.MEM["rd_mem"] = 0
                    self.nextState.MEM["wrt_mem"] = 0
                    self.nextState.MEM["wrt_enable"] = 1
                elif self.state.EX["alu_control"]==0b1111: #xor
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ self.state.EX["Read_data2"]
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = self.state.EX["Rt"]
                    self.nextState.MEM["Store_data"] = 0
                    self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                    self.nextState.MEM["rd_mem"] = 0
                    self.nextState.MEM["wrt_mem"] = 0
                    self.nextState.MEM["wrt_enable"] = 1
                elif self.state.EX["alu_control"]==0b0001: #or
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] | self.state.EX["Read_data2"]
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = self.state.EX["Rt"]
                    self.nextState.MEM["Store_data"] = 0
                    self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                    self.nextState.MEM["rd_mem"] = 0
                    self.nextState.MEM["wrt_mem"] = 0
                    self.nextState.MEM["wrt_enable"] = 1
                elif self.state.EX["alu_control"]==0b0000: #and
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] & self.state.EX["Read_data2"]
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = self.state.EX["Rt"]
                    self.nextState.MEM["Store_data"] = 0
                    self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                    self.nextState.MEM["rd_mem"] = 0
                    self.nextState.MEM["wrt_mem"] = 0
                    self.nextState.MEM["wrt_enable"] = 1
            elif self.state.EX["alu_op"] == 0b00: #I-type, LW and SW
                if self.state.EX["wrt_mem"]==0 and self.state.EX["rd_mem"]==0: # no mem operation -> must be I type
                    if self.state.EX["alu_control"] == 0b0010: # addi
                        self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + self.state.EX["Imm"]
                        self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                        self.nextState.MEM["Rt"] = 0
                        self.nextState.MEM["Store_data"] = 0
                        self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                        self.nextState.MEM["rd_mem"] = 0
                        self.nextState.MEM["wrt_mem"] = 0
                        self.nextState.MEM["wrt_enable"] = 1
                    elif self.state.EX["alu_control"] == 0b1111: # xori
                        self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ self.state.EX["Imm"]
                        self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                        self.nextState.MEM["Rt"] = 0
                        self.nextState.MEM["Store_data"] = 0
                        self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                        self.nextState.MEM["rd_mem"] = 0
                        self.nextState.MEM["wrt_mem"] = 0
                        self.nextState.MEM["wrt_enable"] = 1
                    elif self.state.EX["alu_control"] == 0b0001: # ori
                        self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] | self.state.EX["Imm"]
                        self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                        self.nextState.MEM["Rt"] = 0
                        self.nextState.MEM["Store_data"] = 0
                        self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                        self.nextState.MEM["rd_mem"] = 0
                        self.nextState.MEM["wrt_mem"] = 0
                        self.nextState.MEM["wrt_enable"] = 1
                    elif self.state.EX["alu_control"] == 0b0000: # andi
                        self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] & self.state.EX["Imm"]
                        self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                        self.nextState.MEM["Rt"] = 0
                        self.nextState.MEM["Store_data"] = 0
                        self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                        self.nextState.MEM["rd_mem"] = 0
                        self.nextState.MEM["wrt_mem"] = 0
                        self.nextState.MEM["wrt_enable"] = 1
                elif self.state.EX["rd_mem"]==1 and self.state.EX["wrt_enable"] == 1: # read memory and write register -> LW instruction
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + self.state.EX["Imm"] # read memory address
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = 0
                    self.nextState.MEM["Store_data"] = 0
                    self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                    self.nextState.MEM["rd_mem"] = 1
                    self.nextState.MEM["wrt_mem"] = 0
                    self.nextState.MEM["wrt_enable"] = 1
                elif self.state.EX["wrt_mem"]==1: # write to memory -> SW instruction
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + self.state.EX["Imm"] # write memory address
                    self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                    self.nextState.MEM["Rt"] = 0
                    self.nextState.MEM["Store_data"] = self.state.EX["Read_data2"] # rs2/rt content to write to memory address
                    self.nextState.MEM["Wrt_reg_addr"] = 0
                    self.nextState.MEM["rd_mem"] = 0
                    self.nextState.MEM["wrt_mem"] = 1
                    self.nextState.MEM["wrt_enable"] = 0
            else: #branch option: if branch condition not met, (jal, beq, bne), continue pipeline, no mem op, no wb op.
                self.nextState.MEM["rd_mem"] = 0 
                self.nextState.MEM["wrt_mem"] = 0
                self.nextState.MEM["wrt_enable"] = 0
        
        # --------------------- ID stage ---------------------
        self.nextState.EX["nop"] = self.state.ID["nop"]
        if self.state.ID["nop"] == False:
            instruction = self.state.ID["Instr"] #bin str
            # R-type instructions[6:0]
            if instruction[25:32] == '0110011':
                # add, sub
                self.nextState.EX["Rs"] = int(instruction[12:17],2)
                self.nextState.EX["Rt"] = int(instruction[7:12],2)
                self.nextState.EX["Wrt_reg_addr"] = int(instruction[20:25],2)
                self.nextState.EX["is_I_type"] = False
                self.nextState.EX["Read_data1"] = int(self.myRF.readRF(int(instruction[12:17],2)),16)
                self.nextState.EX["Read_data2"] = int(self.myRF.readRF(int(instruction[7:12],2)),16)
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 1
                self.nextState.EX["alu_op"] = 0b10 # R-type
                if instruction[17:20] == '000':
                    # add
                    if instruction[0:7] == '0000000':
                        self.nextState.EX["alu_control"] = 0b0010
                        # pass
                    # sub
                    else:
                        self.nextState.EX["alu_control"] = 0b0110
                        # pass
                # xor
                elif instruction[17:20] == '100':
                    self.nextState.EX["alu_control"] = 0b1111 # xor
                    # pass
                # or
                elif instruction[17:20] == '110':
                    self.nextState.EX["alu_control"] = 0b0001 
                    # pass
                # and
                elif instruction[17:20] == '111':
                    self.nextState.EX["alu_control"] = 0b0000 
                    # pass
            # I-type instruction[6:0]
            elif instruction[25:32] == '0010011':
                imm = self.getImmValue(instruction[0:12])
                self.nextState.EX["Imm"] = imm
                self.nextState.EX["Rs"] = int(instruction[12:17],2) # 1st register only
                self.nextState.EX["Rt"] = 0                          # 1st register only
                self.nextState.EX["Wrt_reg_addr"] = int(instruction[20:25],2)
                self.nextState.EX["is_I_type"] = True
                self.nextState.EX["Read_data1"] = int(self.myRF.readRF(int(instruction[12:17],2)),16)
                self.nextState.EX["Read_data2"] = 0
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 1
                self.nextState.EX["alu_op"] = 0b00 # I-type
                # addi
                if instruction[17:20] == '000':
                    self.nextState.EX["alu_control"] = 0b0010
                    # pass
                # xori
                elif instruction[17:20] == '100':
                    self.nextState.EX["alu_control"] = 0b1111 #xor
                    # pass
                # ori
                elif instruction[17:20] == '110':
                    self.nextState.EX["alu_control"] = 0b0001 
                    # pass
                # andi
                elif instruction[17:20] == '111':
                    self.nextState.EX["alu_control"] = 0b0000 
                    # pass
            # JAL instruction[6:0]
            # if hit, change PC, then install nop in the following process
            elif instruction[25:32] == '1101111':
                # rearrange imm num here
                imm = instruction[0]+instruction[12:19]+instruction[11]+instruction[1:11]+'0'
                imm = self.getImmValue(imm)
                # Next EX set to nop
                self.nextState.EX["nop"] = True
                self.nextState.EX["Imm"] = 0
                self.nextState.EX["Rs"] = 0
                self.nextState.EX["Rt"] = 0                          # 1st register only
                self.nextState.EX["Wrt_reg_addr"] = int(instruction[20:25],2)
                self.nextState.EX["is_I_type"] = False
                self.nextState.EX["Read_data1"] = 0 # Here you should get PC value PC+4
                self.nextState.EX["Read_data2"] = 0
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 0
                self.nextState.EX["alu_op"] = 0b11 # JAL
                self.nextState.ID["nop"] = True
                if self.endOfFile:
                    self.nextState.IF["PC"] = imm + self.state.IF["PC"] 
                else:
                    self.nextState.IF["PC"] = imm + self.state.IF["PC"] - 4
                self.myRF.writeRF(self.nextState.EX["Wrt_reg_addr"], hex(self.state.IF["PC"]))
                # pass
            # U-type instruction[6:0]
            elif instruction[25:32] == '1100011':
                imm = instruction[0]+instruction[24]+instruction[1:7]+instruction[20:24]+'0'
                imm = self.getImmValue(imm)
                self.nextState.EX["Imm"] = 0
                self.nextState.EX["Rs"] = int(instruction[12:17],2)
                self.nextState.EX["Rt"] = int(instruction[7:12],2)
                self.nextState.EX["Wrt_reg_addr"] = 0
                self.nextState.EX["is_I_type"] = False
                self.nextState.EX["Read_data1"] = int(self.myRF.readRF(int(instruction[12:17],2)),16)
                self.nextState.EX["Read_data2"] = int(self.myRF.readRF(int(instruction[7:12],2)),16)
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 0
                self.nextState.EX["alu_op"] = 0b01 # Branch
                # self.nextState.MEM["ALUresult"] = imm + self.state.IF["PC"] - 4 # will overwrite result in MEM stage
                # Need extra data hazard detection because the data is compared in this stage.
                # ------------------- Hazard Examination -----------------
                # EX/MEM forwarding
                if self.state.EX["wrt_enable"] == 1:
                    if self.state.EX["rd_mem"] == 0: # R-type
                        if self.nextState.EX["Rs"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rs"]!=0:
                            self.nextState.EX["Read_data1"] = self.nextState.MEM["ALUresult"]
                        elif self.nextState.EX["Rt"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rt"]!=0:
                            self.nextState.EX["Read_data2"] = self.nextState.MEM["ALUresult"]
                    # Load-use-data hazard: stall and reload
                    elif self.state.EX["rd_mem"] == 1: #LW instruction # stall
                        if (self.nextState.EX["Rs"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rs"]!=0) or (self.nextState.EX["Rt"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rt"]!=0):
                            self.nextState.EX["nop"] = True   # insert bubble, next cycle ALU doesn't do anything, MEM proceeds as usual
                            self.nextState.EX["wrt_enable"] = 0 # flush signals, not going to detect hazard again
                            self.nextState.EX["wrt_mem"] = 0
                            self.nextState.EX["rd_mem"] = 0
                            self.state.IF["PC"] = self.state.IF["PC"]-4 # Reload this same instruction
                # MEM/WB forwarding 
                # 1. from load-use data hazard stall, after waiting for one cycle, now mem data is ready
                # 2. or no stall needed, memory data ready
                # 3. EX result ready, wait until WB stage to forward
                if self.state.MEM["wrt_enable"] == 1:
                    if self.nextState.EX["Rs"] == self.state.MEM["Wrt_reg_addr"] and self.nextState.EX["Rs"]!=0:
                        self.nextState.EX["Read_data1"] = self.nextState.WB["Wrt_data"]
                    elif self.nextState.EX["Rt"] == self.state.MEM["Wrt_reg_addr"] and self.nextState.EX["Rt"]!=0:
                        self.nextState.EX["Read_data2"] = self.nextState.WB["Wrt_data"]
                #-------------------- End of Hazard Examination ------------
                # beq
                if instruction[17:20] == '000':
                    if self.nextState.EX["Read_data1"] == self.nextState.EX["Read_data2"]:
                        self.nextState.ID["nop"] = True
                        if self.endOfFile:
                            self.nextState.IF["PC"] = imm + self.state.IF["PC"] 
                        else:
                            self.nextState.IF["PC"] = imm + self.state.IF["PC"] - 4
                #pass
                # bne 
                elif instruction[17:20] == '001':
                    if self.nextState.EX["Read_data1"] != self.nextState.EX["Read_data2"]:
                        self.nextState.ID["nop"] = True
                        if self.endOfFile:
                            self.nextState.IF["PC"] = imm + self.state.IF["PC"] 
                        else:
                            self.nextState.IF["PC"] = imm + self.state.IF["PC"] - 4     
                    #pass
            # LW instruction
            elif instruction[25:32] == '0000011':
                imm = self.getImmValue(instruction[0:12])
                self.nextState.EX["Imm"] = imm
                self.nextState.EX["Rs"] = int(instruction[12:17],2)
                self.nextState.EX["Rt"] = 0
                self.nextState.EX["Wrt_reg_addr"] = int(instruction[20:25],2)
                self.nextState.EX["is_I_type"] = False
                self.nextState.EX["Read_data1"] = int(self.myRF.readRF(int(instruction[12:17],2)),16)
                self.nextState.EX["Read_data2"] = 0
                self.nextState.EX["rd_mem"] = 1
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 1
                self.nextState.EX["alu_op"] = 0b00 # LW
                # self.nextState.EX["alu_src"] = 0 # get imm and PC and replace PC = PC+imm, store original PC in Rd(Wrt_reg_addr)
                # self.nextState.EX["pc_src"] = 0
                # pass
            # SW instruction
            elif instruction[25:32] == '0100011':
                imm = instruction[0:7]+instruction[20:25]
                imm = self.getImmValue(imm)
                self.nextState.EX["Imm"] = imm
                self.nextState.EX["Rs"] = int(instruction[12:17],2)
                self.nextState.EX["Rt"] = int(instruction[7:12],2)
                self.nextState.EX["Wrt_reg_addr"] = 0
                self.nextState.EX["is_I_type"] = False
                self.nextState.EX["Read_data1"] = int(self.myRF.readRF(int(instruction[12:17],2)),16)
                self.nextState.EX["Read_data2"] = int(self.myRF.readRF(int(instruction[7:12],2)),16)
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 1
                self.nextState.EX["wrt_enable"] = 0
                self.nextState.EX["alu_op"] = 0b00 # SW
                # pass
            # Halt
            elif instruction[25:32] == '1111111':
                self.nextState.IF["nop"] = True
                self.state.IF["nop"] = True
                self.nextState.ID["nop"] = True
                self.state.ID["nop"] = True
                self.nextState.EX["nop"] = True
                if self.nextState.MEM["rd_mem"]==0 and self.nextState.MEM["wrt_mem"]==0 and self.nextState.MEM["wrt_enable"]==0:
                    self.nextState.MEM["nop"] = True
                if self.nextState.WB["wrt_enable"] ==0:
                    self.nextState.WB["nop"] = True
                # next time will not end here at all, IF still always have nop now
                self.nextState.IF["PC"] = self.state.IF["PC"] 
            # pass
            # ------------------- Hazard Examination -----------------
            # EX/MEM forwarding
            if self.state.EX["wrt_enable"] == 1:
                if self.state.EX["rd_mem"] == 0: # R-type
                    if self.nextState.EX["Rs"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rs"]!=0:
                        self.nextState.EX["Read_data1"] = self.nextState.MEM["ALUresult"]
                    elif self.nextState.EX["Rt"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rt"]!=0:
                        self.nextState.EX["Read_data2"] = self.nextState.MEM["ALUresult"]
                # Load-use-data hazard: stall and reload
                elif self.state.EX["rd_mem"] == 1: #LW instruction # stall
                    if (self.nextState.EX["Rs"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rs"]!=0) or (self.nextState.EX["Rt"] == self.state.EX["Wrt_reg_addr"] and self.nextState.EX["Rt"]!=0):
                        self.nextState.EX["nop"] = True   # insert bubble, next cycle ALU doesn't do anything, MEM proceeds as usual
                        self.nextState.EX["wrt_enable"] = 0 # flush signals, not going to detect hazard again
                        self.nextState.EX["wrt_mem"] = 0
                        self.nextState.EX["rd_mem"] = 0
                        self.state.IF["PC"] = self.state.IF["PC"]-4 # Reload this same instruction
            # MEM/WB forwarding 
            # 1. from load-use data hazard stall, after waiting for one cycle, now mem data is ready
            # 2. or no stall needed, memory data ready
            # 3. EX result ready, wait until WB stage to forward
            if self.state.MEM["wrt_enable"] == 1:
                if self.nextState.EX["Rs"] == self.state.MEM["Wrt_reg_addr"] and self.nextState.EX["Rs"]!=0:
                    self.nextState.EX["Read_data1"] = self.nextState.WB["Wrt_data"]
                elif self.nextState.EX["Rt"] == self.state.MEM["Wrt_reg_addr"] and self.nextState.EX["Rt"]!=0:
                    self.nextState.EX["Read_data2"] = self.nextState.WB["Wrt_data"]
            #-------------------- End of Hazard Examination ------------
        
        # --------------------- IF stage ---------------------
        if self.state.IF["nop"] == False:
            self.nextState.ID["Instr"] = bin(int(self.ext_imem.readInstr(self.state.IF.get("PC")),16))[2:].zfill(32)
            # PC + 4
            if self.nextState.IF["PC"]==0:
                # Really important, if beq or bne set nextState.ID["nop"], don't change again
                self.nextState.ID["nop"] = self.state.IF["nop"]
                if self.state.IF["PC"]<len(self.ext_imem.IMem)-4 and self.nextState.ID["Instr"][25:32]!='1111111':
                    self.endOfFile = False
                    self.nextState.IF["PC"] = self.state.IF["PC"] + 4
                else:
                    self.endOfFile = True
                    self.nextState.IF["PC"] = self.state.IF["PC"]
        else: # can only land here from ID.halt 111111
            self.nextState.IF["nop"] = self.state.IF["nop"] # Loop IF stage with True nop
            self.nextState.ID["nop"] = self.state.IF["nop"] # Set next ID to nop too
            self.nextState.IF["PC"] = self.state.IF["PC"]
        #---------------------- End Cycle --------------------
        # self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.nextState = State()
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

if __name__ == "__main__": 
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            # print Performance Metrics Result
            resPath = ioDir + "/" + "PerformanceMetrics_result.txt"
            with open(resPath, "w") as rp:
                rp.writelines("Single Stage Core Performance Metrics-----------------------------\n")
                rp.writelines("Number of cycles taken: "+str(ssCore.cycle)+"\n")
                rp.writelines("Cycles per instruction: "+str(ssCore.cycle/(ssCore.numInstructions-1))+"\n")
                rp.writelines("Instructions per cycle: "+str((ssCore.numInstructions-1)/ssCore.cycle)+"\n\n\n")
                rp.writelines("Five Stage Core Performance Metrics-----------------------------\n")
                rp.writelines("Number of cycles taken: "+str(fsCore.cycle)+"\n")
                rp.writelines("Cycles per instruction: "+str(fsCore.cycle/(ssCore.numInstructions-1))+"\n")
                rp.writelines("Instructions per cycle: "+str((ssCore.numInstructions-1)/fsCore.cycle)+"\n\n\n")
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()