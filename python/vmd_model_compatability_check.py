# Nuthouse01 - 06/27/2020 - v4.50
# This code is free to use and re-distribute, but I cannot be held responsible for damages that it may or may not cause.
#####################

# second, wrap custom imports with a try-except to catch it if files are missing
try:
	from . import nuthouse01_core as core
	from . import nuthouse01_vmd_parser as vmdlib
	from . import nuthouse01_pmx_parser as pmxlib
except ImportError as eee:
	try:
		import nuthouse01_core as core
		import nuthouse01_vmd_parser as vmdlib
		import nuthouse01_pmx_parser as pmxlib
	except ImportError as eee:
		print(eee.__class__.__name__, eee)
		print("ERROR: failed to import some of the necessary files, all my scripts must be together in the same folder!")
		print("...press ENTER to exit...")
		input()
		exit()
		core = vmdlib = pmxlib = None




# when debug=True, disable the catchall try-except block. this means the full stack trace gets printed when it crashes,
# but if launched in a new window it exits immediately so you can't read it.
DEBUG = False



helptext = '''=================================================
vmd_model_compatability_check:
This tool will check the compabability of a given model (PMX) with a given dance motion (VMD).
This means checking whether the model supports all the bones and/or morphs the VMD dance is trying to use.
All bone/morph names are compared using the JP names.

This requires both a PMX model and a VMD motion to run.
Outputs: morph compatability summary text file '[dancename]_morph_compatability_with_[modelname].txt'
         bone compatability summary text file '[dancename]_bone_compatability_with_[modelname].txt'
'''


def main(moreinfo=True):
	# prompt PMX name
	core.MY_PRINT_FUNC("Please enter name of PMX input file:")
	input_filename_pmx = core.MY_FILEPROMPT_FUNC(".pmx")
	pmx = pmxlib.read_pmx(input_filename_pmx, moreinfo=moreinfo)
	realbones = pmx[5]		# get bones
	realmorphs = pmx[6]		# get morphs
	modelname_jp = pmx[0][1]
	modelname_en = pmx[0][2]
	
	# prompt VMD file name
	core.MY_PRINT_FUNC("Please enter name of VMD dance input file:")
	input_filename_vmd = core.MY_FILEPROMPT_FUNC(".vmd")
	nicelist_in, bonedict, morphdict = vmdlib.read_vmd(input_filename_vmd, getdict=True, moreinfo=moreinfo)
	
	core.MY_PRINT_FUNC("")
	
	# must use same encoding as I used when the VMD was unpacked, since the hex bytes only have meaning in that encoding
	core.set_encoding("shift_jis")
	
	##############################################
	# check morph compatability
	
	# build list of morphs used in the dance VMD
	morphs_in_vmd = list(morphdict.keys())
	
	# build list of ALL morphs in the PMX
	# first item of pmxmorph is the jp name
	morphs_in_model = [pmxmorph[0] for pmxmorph in realmorphs]
	
	# ensure that the VMD contains at least some morphs, to prevent zero-divide error
	if len(morphs_in_vmd) == 0:
		core.MY_PRINT_FUNC("Skipping morph compatability check: VMD '%s' does not contain any morphs that are used in a significant way." % input_filename_vmd)
	elif len(morphs_in_model) == 0:
		core.MY_PRINT_FUNC("Skipping morph compatability check: PMX '%s' does not contain any morphs." % input_filename_pmx)
	else:
		
		# convert all these names to bytes
		morphs_in_model_b = [core.encode_string_with_escape(a) for a in morphs_in_model]
		
		matching_morphs = {}
		missing_morphs = {}
		# iterate over list of morphs
		for vmdmorph in morphs_in_vmd:
			# question: does "vmdmorph" match something in "morphs_in_model"?
			# BUT, doing comparison in bytes-space to handle escape characters: vmdmorph_b vs morphs_in_model_b
			vmdmorph_b = core.encode_string_with_escape(vmdmorph)
			# NOTE: MMD does not try to use "begins-with" matching like I had hoped/assumed, it only looks for exact matches
			# return list of ALL matches, this way i can raise an error if there are multiple matches
			# exact match
			modelmorphmatch_b = [a for a in morphs_in_model_b if a == vmdmorph_b]
			
			# copy the key,val in one of the dicts depending on results of matching attempt
			if len(modelmorphmatch_b) == 0:
				# MISS! key is the VMD morph name since that's the best clue Ive got
				missing_morphs[vmdmorph] = morphdict[vmdmorph]
			elif len(modelmorphmatch_b) == 1:
				# MATCH! key is the PMX morph name it matched against, since it might be a longer version wtihout escape char
				matching_morphs[core.decode_bytes_with_escape(modelmorphmatch_b[0])] = morphdict[vmdmorph]
			else:
				# more than 1 morph was a match!?
				core.MY_PRINT_FUNC("Warning: VMDmorph '%s' matched multiple PMXmorphs, its behavior is uncertain. Assuming it matches against the first." % vmdmorph)
				modelmorphmatch = [core.decode_bytes_with_escape(a) for a in modelmorphmatch_b]
				core.MY_PRINT_FUNC(modelmorphmatch)
				matching_morphs[modelmorphmatch[0]] = morphdict[vmdmorph]
		
		# display results!
		core.MY_PRINT_FUNC("This model supports {} / {} = {:.1%} of the MORPHS in '{}'".format(
			len(matching_morphs), len(morphs_in_vmd), len(matching_morphs) / len(morphs_in_vmd), input_filename_vmd))
			
		# convert the dicts to lists and sort for printing
		missing_morphs_list = list(missing_morphs.items())
		missing_morphs_list.sort(key=core.get1st)  # sort by name as tiebreaker
		missing_morphs_list.sort(key=core.get2nd, reverse=True)  # sort in-place descending by 2nd element as primary
		
		matching_morphs_list = list(matching_morphs.items())
		matching_morphs_list.sort(key=core.get1st)  # sort by name as tiebreaker
		matching_morphs_list.sort(key=core.get2nd, reverse=True)  # sort in-place descending by 2nd element as primary
		
		# since only jap names are available, printing to screen won't help. must write to a file.
		# format:
		# "vmd_dance_file", -----
		# "num_morphs_missing", #
		# "missing_morph_name", "num_times_used"
		# list
		# "num_morphs_matching", #
		# "matching_morph_name", "num_times_used"
		# list
		
		rawlist_out = [
			["vmd_dance_file", "'" + input_filename_vmd + "'"],
			["modelname_jp", "'" + modelname_jp + "'"],
			["modelname_en", "'" + modelname_en + "'"],
			["num_morphs_missing", len(missing_morphs)]
		]
		if len(missing_morphs) != 0:
			rawlist_out.append(["missing_morph_name", "num_times_used"])
			rawlist_out += missing_morphs_list
		rawlist_out.append(["num_morphs_matching", len(matching_morphs)])
		if len(matching_morphs) != 0:
			rawlist_out.append(["matching_morph_name", "num_times_used"])
			rawlist_out += matching_morphs_list
		
		# write out
		output_filename_morph = "%s_morph_compatability_with_%s.txt" % \
							  (input_filename_vmd[0:-4], core.get_clean_basename(input_filename_pmx))
		output_filename_morph = core.get_unused_file_name(output_filename_morph)
		core.MY_PRINT_FUNC("...writing result to file '%s'..." % (core.get_clean_basename(output_filename_morph) + ".txt"))
		core.write_rawlist_to_txt(output_filename_morph, rawlist_out, use_jis_encoding=False)
		core.MY_PRINT_FUNC("done!")
	
	##############################################
	# check bone compatability
	core.MY_PRINT_FUNC("")
	
	# build list of bones used in the dance VMD
	bones_in_vmd = list(bonedict.keys())
	
	# build list of ALL bones in the PMX
	# first item of pmxbone is the jp name
	bones_in_model = [pmxbone[0] for pmxbone in realbones]
	
	# ensure that the VMD contains at least some bones, to prevent zero-divide error
	if len(bones_in_vmd) == 0:
		core.MY_PRINT_FUNC("Skipping bone compatability check: VMD '%s' does not contain any bones that are used in a significant way." % input_filename_vmd)
	elif len(bones_in_model) == 0:
		core.MY_PRINT_FUNC("Skipping bone compatability check: PMX '%s' does not contain any bones." % input_filename_pmx)
	else:
		
		# convert all these names to bytes
		bones_in_model_b = [core.encode_string_with_escape(a) for a in bones_in_model]
		
		matching_bones = {}
		missing_bones = {}
		# iterate over list of bones that pass the size check
		for vmdbone in bones_in_vmd:
			# question: does "vmdbone" match something in "bones_in_model"?
			# BUT, doing comparison in bytes-space to handle escape characters: vmdbone_b vs bones_in_model_b
			vmdbone_b = core.encode_string_with_escape(vmdbone)
			# NOTE: MMD does not try to use "begins-with" matching like I had hoped/assumed, it only looks for exact matches
			# return list of ALL matches, this way i can raise an error if there are multiple matches
			# exact match
			modelbonematch_b = [a for a in bones_in_model_b if a == vmdbone_b]
			
			# copy the key,val in one of the dicts depending on results of matching attempt
			if len(modelbonematch_b) == 0:
				# MISS! key is the VMD bone name since that's the best clue Ive got
				missing_bones[vmdbone] = bonedict[vmdbone]
			elif len(modelbonematch_b) == 1:
				# MATCH! key is the PMX bone name it matched against, since it might be a longer version wtihout escape char
				matching_bones[core.decode_bytes_with_escape(modelbonematch_b[0])] = bonedict[vmdbone]
			else:
				# more than 1 bone was a match!?
				core.MY_PRINT_FUNC(
					"Warning: VMDbone '%s' matched multiple PMXbones, its behavior is uncertain. Assuming it matches against the first." % vmdbone)
				modelbonematch = [core.decode_bytes_with_escape(a) for a in modelbonematch_b]
				core.MY_PRINT_FUNC(modelbonematch)
				matching_bones[modelbonematch[0]] = bonedict[vmdbone]
		
		# display results!
		core.MY_PRINT_FUNC("This model supports {} / {} = {:.1%} of the BONES in '{}'".format(
			len(matching_bones), len(bones_in_vmd), len(matching_bones) / len(bones_in_vmd), input_filename_vmd))
		
		# convert the dicts to lists and sort for printing
		missing_bones_list = list(missing_bones.items())
		missing_bones_list.sort(key=core.get1st)  # sort by name as tiebreaker
		missing_bones_list.sort(key=core.get2nd, reverse=True)  # sort in-place descending by 2nd element as primary
		
		matching_bones_list = list(matching_bones.items())
		matching_bones_list.sort(key=core.get1st)  # sort by name as tiebreaker
		matching_bones_list.sort(key=core.get2nd, reverse=True)  # sort in-place descending by 2nd element as primary
		
		# since only jap names are available, printing to screen won't work. must write to a file.
		# format:
		# "vmd_dance_file", -----
		# "num_bones_missing", #
		# "missing_bone_name", "num_times_used"
		# list
		# "num_bones_matching", #
		# "matching_bone_name", "num_times_used"
		# list
		
		rawlist_out = [
			["vmd_dance_file", "'" + input_filename_vmd + "'"],
			["modelname_jp", "'" + modelname_jp + "'"],
			["modelname_en", "'" + modelname_en + "'"],
			["num_bones_missing", len(missing_bones)]
		]
		if len(missing_bones) != 0:
			rawlist_out.append(["missing_bone_name", "num_times_used"])
			rawlist_out += missing_bones_list
		rawlist_out.append(["num_bones_matching", len(matching_bones)])
		if len(matching_bones) != 0:
			rawlist_out.append(["matching_bone_name", "num_times_used"])
			rawlist_out += matching_bones_list
		
		# write out
		output_filename_bone = "%s_bone_compatability_with_%s.txt" % \
							   (input_filename_vmd[0:-4], core.get_clean_basename(input_filename_pmx))
		output_filename_bone = core.get_unused_file_name(output_filename_bone)
		core.MY_PRINT_FUNC("...writing result to file '%s'..." % (core.get_clean_basename(output_filename_bone) + ".txt"))
		core.write_rawlist_to_txt(output_filename_bone, rawlist_out, use_jis_encoding=False)
		core.MY_PRINT_FUNC("done!")
	return None


if __name__ == '__main__':
	core.MY_PRINT_FUNC("Nuthouse01 - 06/27/2020 - v4.50")
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
			core.MY_PRINT_FUNC(ee.__class__.__name__, ee)
			core.pause_and_quit("ERROR: something truly strange and unexpected has occurred, sorry, good luck figuring out what tho")
