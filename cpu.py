#!  /usr/bin/python

import struct

debug = False
printcode = True


fd = open("code","rb")

# Get eof 
fd.seek(0,2)
EOF = fd.tell()

# Reset position
fd.seek(0)

opts={0:"regs",1:"heap",2:"stack",3:"imm"}
regs = {"a":0,"b":0,"c":0,"d":0,"cmp_res":0,"cmp_g":0}
stack = list()
heap = dict()
video = list()

def displayvideo(): pass

def getstring(): 
	string=""
	c=fd.read(1)
	if c != "'": codeprint("Invalid string");exit(1)
	c=fd.read(1)
	string+=c
	while c != "'" and fd.tell() != EOF:
	  c=fd.read(1)
	  if c != "'": string+=c
	return string
  

def codeprint(*s):
	global printcode
	if not printcode: return
	print(s)
	
def handle_bin_op_str(code):
    
	global opts,stack,heap,regs

	dst=getbyte()

	if dst in opts.keys():
		if opts[dst] == "heap": 
			didx=getword()
	else: val=getword()

    ## Get src string
	s=getstring()
    
	if code == 0x90:
		codeprint("load string",s)
		res=s

	if opts[dst] == "heap": heap[didx]=res; codeprint("heap[",didx,"] = ",res)

def handle_bin_op(code):
    
	global opts,stack,heap,regs

	dst=getbyte()

	if dst in opts.keys():
	  if opts[dst] == "regs": 
		dreg=getreg()
		d=regs[dreg]
	  elif opts[dst] == "heap": 
		didx=getword()
		if code not in  [0x10]:
			d=heap[didx]
	  elif opts[dst] == "stack":
		didx=getword()
		if code not in  [0x10]:
			d=stack[didx]
	  elif opts[dst] == "imm": 
		print("Cannot have imm as dst")
		exit(1)
	else: val=getword()

	src=getbyte()
	if src in opts.keys():
	  if opts[src] == "regs": s=regs[getreg()]
	  elif opts[src] == "heap": s=heap[getword()]
	  elif opts[src] == "stack": s=stack[getword()]
	  elif opts[src] == "imm": s=getword()
	else: val=getword()
    
	if code == 0x06:
		codeprint("sub",d,"-",s)
		res=d-s
	elif code == 0x04:
		codeprint("add",d,"+",s)
		res=d+s
	elif code == 0x03:
		codeprint("mul",d,"*",s)
		res=d*s
	elif code == 0x05:
		codeprint("div",d,"/",s)
		res=d/s
	elif code == 0x10:
		codeprint("mov <--",s)
		res=s
	elif code == 0x24:
		codeprint("cmp ",d,s)
		res=(d==s)
		res2=(d>s)
		regs["cmp_res"]=res
		regs["cmp_g"]=res2
	elif code == 0x14:
		codeprint("and ",d,s)
		res=d&s
	elif code == 0x15:
		codeprint("or ",d,s)
		res=d|s
	elif code == 0x13:
		codeprint("xor ",d,s)
		res=d^s
	elif code == 0x17:
		codeprint("shl ",d,s)
		res=d<<s
	elif code == 0x19:
		codeprint("shr ",d,s)
		res=d>>s

	if code != 0x24:
		if opts[dst] == "regs": regs[dreg]=res; codeprint("regs[",dreg,"] = ",res)
		elif opts[dst] == "heap": heap[didx]=res; codeprint("heap[",didx,"] = ",res)
		elif opts[dst] == "stack": stack[didx]=res; codeprint("stack[",didx,"] = ",res)


def handle_un_op(code):
    
	global opts,stack,heap,regs

	dst=getbyte()

	if dst in opts.keys():
		if opts[dst] == "regs": 
			dreg=getreg()
			d=regs[dreg]
		elif opts[dst] == "heap": 
			didx=getword()
			if code not in [0x18]:
				d=heap[didx]
		elif opts[dst] == "stack":
			didx=getword()
			if code not in [0x18]:
				d=stack[didx]
		elif opts[dst] == "imm":
			d=getword()
	else:
		d=getword()

	if code == 0x16:
		res=stack.append(d)
		codeprint("push from ",opts[dst],":",d)
	elif code == 0x18:
		res=stack.pop()
		codeprint("pop to ",opts[dst])
	elif code == 0x29:
		res= -d
		codeprint("negate from ",opts[dst])
	elif code == 0x20:
		res= d+1
		codeprint("inc from ",opts[dst])
	elif code == 0x22:
		res= d-1
		codeprint("dec from ",opts[dst])
	elif code == 0x28:
		res= ~d
		codeprint("not from ",opts[dst])
	
	if code not in [0x16]:
		if opts[dst] == "regs": regs[dreg]=res; codeprint("regs[",dreg,"] = ",res)
		elif opts[dst] == "heap": heap[didx]=res; codeprint("heap[",didx,"] = ",res)
		elif opts[dst] == "stack": stack[didx]=res; codeprint("stack[",didx,"] = ",res)
    
def getbyte(): 
	global last,fd
	if fd.tell() == EOF: return None 
	return struct.unpack(">B",fd.read(1))[0]

def getword(): 
	global last,fd
	if fd.tell() == EOF: return None 
	return struct.unpack(">H",fd.read(2))[0]

def getreg():
	global last,fd
	regopts = ["a","b","c","d"]
	if fd.tell() == EOF: return None
	opt = struct.unpack(">B",fd.read(1))[0]
	if opt > len(regopts): 
		print("Invalid register option", opt, " at byte", fd.tell())
		exit(1)
	return regopts[opt-1]

while True:
	ins = getbyte()

	if ins == None:
		break
	if ins == 0x00:
		codeprint("np")
		pass
	elif ins == 0x03:
		# Mul
		handle_bin_op(ins)
	elif ins == 0x05:
		# Div
		handle_bin_op(ins)
	elif ins == 0x04:
		# Add
		handle_bin_op(ins)
	elif ins == 0x06:
		# Sub
		handle_bin_op(ins)
	elif ins == 0x10:
        # Mov
		handle_bin_op(ins)
	elif ins == 0x24:
		# Cmp 
		handle_bin_op(ins)
	elif ins == 0x13:
		# Xor
		handle_bin_op(ins)
	elif ins == 0x14:
		# And
		handle_bin_op(ins)
	elif ins == 0x15:
		# Or
		handle_bin_op(ins)
	elif ins == 0x16:
		# Push
		handle_un_op(ins)
	elif ins == 0x17:
		# Shl
		handle_bin_op(ins)
	elif ins == 0x19:
		# Shr
		handle_bin_op(ins)
	elif ins == 0x18:
		# Pop
		handle_un_op(ins)
	elif ins == 0x20:
		# Inc
		handle_un_op(ins)
	elif ins == 0x22:
		# Dec
		handle_un_op(ins)
	elif ins == 0x28:
		# Not
		handle_un_op(ins)
	elif ins == 0x29:
		# Neg
		handle_un_op(ins)
	elif ins == 0x40:
		loc = getword()
		codeprint("jz to byte: ",loc)
		if regs["cmp_res"]: 
			fd.seek(loc); 
			codeprint("Seeking to byte",fd.tell())
	elif ins == 0x42:
		loc = getword()
		codeprint("jp to byte: ",loc)
		fd.seek(loc); 
		codeprint("Seeking to byte",fd.tell())
	elif ins == 0x41:
		loc = getword()
		codeprint("jl to byte: ",loc)
		if not regs["cmp_res"]: 
			if not regs["cmp_g"]:
				fd.seek(loc); 
				codeprint("Seeking to byte",fd.tell())
	elif ins == 0x43:
		loc = getword()
		codeprint("jg to byte: ",loc)
		if not regs["cmp_res"]: 
			if regs["cmp_g"]:
				fd.seek(loc); 
				codeprint("Seeking to byte",fd.tell())
	elif ins == 0x44:
		loc = getword()
		codeprint("jn to byte: ",loc)
		if not regs["cmp_res"]: 
			fd.seek(loc); 
			codeprint("Seeking to byte",fd.tell())
	elif ins == 0x60:
		x = getword()
		y = getword()
		color = set(getbyte(),getbyte(),getbyte())
		if None in [x,y,color]: 
			print("X, Y, or Color is missing")
			exit(1)
		codeprint("set color and coords x,y,color",x,y,color)
		video.append([x,y,color])
	elif ins == 0x70:
		displayvideo()
	elif ins == 0x90:
		# load string
		handle_bin_op_str(ins)
	else:
		print("Invalid instruction ",ins)
		exit(1)

	if debug:
		print("REGS: ",regs)
		print("STACK: ",stack)
		print("HEAP: ",heap)

print("REGS: ",regs)
print("STACK: ",stack)
print("HEAP: ",heap)

fd.close()
