# Nuthouse01 - 07/24/2020 - v4.63
# This code is free to use and re-distribute, but I cannot be held responsible for damages that it may or may not cause.
#####################


try:
	from . import nuthouse01_core as core
	from . import nuthouse01_pmx_parser as pmxlib
	from . import model_shift
	from . import morph_scale
except ImportError as eee:
	try:
		import nuthouse01_core as core
		import nuthouse01_pmx_parser as pmxlib
		import model_shift
		import morph_scale
	except ImportError as eee:
		print(eee.__class__.__name__, eee)
		print("ERROR: failed to import some of the necessary files, all my scripts must be together in the same folder!")
		print("...press ENTER to exit...")
		input()
		exit()
		core = pmxlib = model_shift = morph_scale = None


# when debug=True, disable the catchall try-except block. this means the full stack trace gets printed when it crashes,
# but if launched in a new window it exits immediately so you can't read it.
DEBUG = False


helptext = '''=================================================
model_scale:
Scale the entire model around 0,0,0 by some X,Y,Z value.
This also scales all vertex and bone morphs by the same amount, so you don't need to do that separately.

Output: PMX file '[modelname]_scale.pmx'
'''




def main(moreinfo=True):
	# prompt PMX name
	core.MY_PRINT_FUNC("Please enter name of PMX input file:")
	input_filename_pmx = core.MY_FILEPROMPT_FUNC(".pmx")
	pmx = pmxlib.read_pmx(input_filename_pmx, moreinfo=moreinfo)
	
	# to shift the model by a set amount:
	# first, ask user for X Y Z
	
	# create the prompt popup
	scale_str = core.MY_GENERAL_INPUT_FUNC(
		lambda x: (model_shift.is_3float(x) is not None),
		["Enter the X,Y,Z amount to scale this model by:",
		 "Three decimal values separated by commas.",
		 "Empty input will quit the script."])
	
	# if empty, quit
	if scale_str == "":
		core.MY_PRINT_FUNC("quitting")
		return None
	# use the same func to convert the input string
	scale = model_shift.is_3float(scale_str)
	
	####################
	# what does it mean to scale the entire model?
	# scale vertex position, sdef params
	# ? scale vertex normal vectors, then normalize? need to convince myself of this interaction
	# scale bone position, tail offset
	# scale fixedaxis and localaxis vectors, then normalize
	# scale vert morph, bone morph
	# scale rigid pos, size
	# scale joint pos, movelimits
	
	for v in pmx.verts:
		# vertex position
		for i in range(3):
			v.pos[i] *= scale[i]
		# vertex normal
		for i in range(3):
			v.norm[i] *= scale[i]
		# then re-normalize the normal vector
		L = core.my_euclidian_distance(v.norm)
		if L != 0:
			v.norm = [n / L for n in v.norm]
		# c, r0, r1 params of every SDEF vertex
		if v.weighttype == 3:
			for param in v.weight_sdef:
				for i in range(3):
					param[i] *= scale[i]
				
	for b in pmx.bones:
		# bone position
		for i in range(3):
			b.pos[i] *= scale[i]
		# bone tail if using offset mode
		if not b.tail_type:
			for i in range(3):
				b.tail[i] *= scale[i]
		# scale fixedaxis and localaxis vectors, then normalize
		if b.has_fixedaxis:
			for i in range(3):
				b.fixedaxis[i] *= scale[i]
			# then re-normalize
			L = core.my_euclidian_distance(b.fixedaxis)
			if L != 0:
				b.fixedaxis = [n / L for n in b.fixedaxis]
		# scale fixedaxis and localaxis vectors, then normalize
		if b.has_localaxis:
			for i in range(3):
				b.localaxis_x[i] *= scale[i]
			for i in range(3):
				b.localaxis_z[i] *= scale[i]
			# then re-normalize
			L = core.my_euclidian_distance(b.localaxis_x)
			if L != 0:
				b.localaxis_x = [n / L for n in b.localaxis_x]
			L = core.my_euclidian_distance(b.localaxis_z)
			if L != 0:
				b.localaxis_z = [n / L for n in b.localaxis_z]

	for m in pmx.morphs:
		# vertex morph and bone morph (only translate, not rotate)
		if m.morphtype in (1,2):
			morph_scale.morph_scale(m, scale, bone_mode=1)
			
	for rb in pmx.rigidbodies:
		# rigid body position
		for i in range(3):
			rb.pos[i] *= scale[i]
		# rigid body size
		for i in range(3):
			rb.size[i] *= scale[i]

	for j in pmx.joints:
		# joint position
		for i in range(3):
			j.pos[i] *= scale[i]
		# joint min slip
		for i in range(3):
			j.movemin[i] *= scale[i]
		# joint max slip
		for i in range(3):
			j.movemax[i] *= scale[i]

	# that's it? that's it!
	
	# write out
	output_filename_pmx = input_filename_pmx[0:-4] + "_scale.pmx"
	output_filename_pmx = core.get_unused_file_name(output_filename_pmx)
	pmxlib.write_pmx(output_filename_pmx, pmx, moreinfo=moreinfo)
	core.MY_PRINT_FUNC("Done!")
	return None


if __name__ == '__main__':
	print("Nuthouse01 - 07/24/2020 - v4.63")
	if DEBUG:
		# print info to explain the purpose of this file
		core.MY_PRINT_FUNC(helptext)
		core.MY_PRINT_FUNC("")
		
		main()
		core.pause_and_quit("Done with everything! Goodbye!")
	else:
		try:
			# print info to explain the purpose of this file
			core.MY_PRINT_FUNC(helptext)
			core.MY_PRINT_FUNC("")
			
			main()
			core.pause_and_quit("Done with everything! Goodbye!")
		except (KeyboardInterrupt, SystemExit):
			# this is normal and expected, do nothing and die normally
			pass
		except Exception as ee:
			# if an unexpected error occurs, catch it and print it and call pause_and_quit so the window stays open for a bit
			print(ee)
			core.pause_and_quit("ERROR: something truly strange and unexpected has occurred, sorry, good luck figuring out what tho")
