import math
from typing import List, Tuple, Set, Sequence, Callable, Any, Generator
import time

import mmd_scripting.core.nuthouse01_core as core
import mmd_scripting.core.nuthouse01_vmd_parser as vmdlib
import mmd_scripting.core.nuthouse01_vmd_struct as vmdstruct
import mmd_scripting.core.nuthouse01_vmd_utils as vmdutil
from mmd_scripting.vectorpaths_chrisarridge import vectorpaths

import cProfile
import pstats
import logging

_SCRIPT_VERSION = "Script version:  Nuthouse01 - v1.07.05 - 9/7/2021"
# This code is free to use and re-distribute, but I cannot be held responsible for damages that it may or may not cause.
#####################
# https://github.com/chrisarridge/vectorpaths

DEBUG = 1
# debug 1: per-channel results
# debug 2: each match segment
# debug 3: reverse slerp goodness
# debug 4: bez logging always on
DEBUG_PLOTS = False

# if DEBUG >= 4:
# 	# this prints a bunch of useful stuff in the bezier regression, and a bunch of useless stuff from matplotlib
# 	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# if DEBUG_PLOTS:
import matplotlib.pyplot as plt

helptext = '''=================================================
vmd_uninterpolate:
Modify a VMD and remove excess keyframes caused by deliberate over-keying.
This will make the VMD much smaller (filesize) and make it easier to load or tweak for different models.
WARNING: THIS TAKES AN EXTREMELY LONG TIME TO RUN!

Output: dunno
'''

'''
data: how for bone センター in Marionette, how many frames are kept based on position for varying bezier error targets
errors 0.5 - 3.0
total=6212

0.5, keep%=59%
0.6, keep%=54%
0.7, keep%=50%
0.79, keep%=46%
0.89, keep%=42%
0.99, keep%=38%
1.09, keep%=36%
1.2, keep%=34%
1.3, keep%=33%
1.4, keep%=32%
1.5, keep%=30%
1.6, keep%=30%
1.7, keep%=29%
1.8, keep%=28%
1.9, keep%=27%
2.0, keep%=26%
2.1, keep%=25%
2.2, keep%=25%
2.3, keep%=24%
2.4, keep%=23%
2.5, keep%=22%
2.6, keep%=22%
2.7, keep%=21%
2.8, keep%=21%
2.9, keep%=21%
'''

'''
bone='アホ毛１' : rot : keep 18/197
bone='アホ毛１' : RESULT : keep 18/197 : keep%=9.137056%
bone='アホ毛２' : rot : keep 28/6404
bone='アホ毛２' : RESULT : keep 28/6404 : keep%=0.437227%
bone='センター' : pos : chan=0   : keep 1366/6212
bone='センター' : pos : chan=1   : keep 1469/6212
bone='センター' : pos : chan=2   : keep 1384/6212
bone='センター' : pos : chan=ALL : keep 3200/6212
bone='センター' : RESULT : keep 3200/6212 : keep%=51.513200%
bone='上半身' : rot : keep 4203/6034
bone='上半身' : RESULT : keep 4203/6034 : keep%=69.655287%
bone='上半身2' : rot : keep 4060/5660
bone='上半身2' : RESULT : keep 4060/5660 : keep%=71.731449%
bone='下半身' : rot : keep 4387/6237
bone='下半身' : RESULT : keep 4387/6237 : keep%=70.338304%
bone='前髪１' : rot : keep 4/197
bone='前髪１' : RESULT : keep 4/197 : keep%=2.030457%
bone='前髪１_２' : rot : keep 47/6406
bone='前髪１_２' : RESULT : keep 47/6406 : keep%=0.733687%
bone='前髪２' : rot : keep 4/197
bone='前髪２' : RESULT : keep 4/197 : keep%=2.030457%
bone='前髪２_２' : rot : keep 4/197
bone='前髪２_２' : RESULT : keep 4/197 : keep%=2.030457%
bone='前髪３' : rot : keep 4/197
bone='前髪３' : RESULT : keep 4/197 : keep%=2.030457%
bone='前髪３_２' : rot : keep 4/197
bone='前髪３_２' : RESULT : keep 4/197 : keep%=2.030457%
bone='右ひじ' : rot : keep 3982/5448
bone='右ひじ' : RESULT : keep 3982/5448 : keep%=73.091043%
bone='右もみあげ１' : rot : keep 4/197
bone='右もみあげ１' : RESULT : keep 4/197 : keep%=2.030457%
bone='右もみあげ２' : rot : keep 4/197
bone='右もみあげ２' : RESULT : keep 4/197 : keep%=2.030457%
bone='右中指１' : rot : keep 2209/4263
bone='右中指１' : RESULT : keep 2209/4263 : keep%=51.817969%
bone='右中指２' : rot : keep 1585/3963
bone='右中指２' : RESULT : keep 1585/3963 : keep%=39.994953%
bone='右中指３' : rot : keep 1541/4290
bone='右中指３' : RESULT : keep 1541/4290 : keep%=35.920746%
bone='右人指１' : rot : keep 2448/4602
bone='右人指１' : RESULT : keep 2448/4602 : keep%=53.194263%
bone='右人指２' : rot : keep 1644/5017
bone='右人指２' : RESULT : keep 1644/5017 : keep%=32.768587%
bone='右人指３' : rot : keep 1609/4506
bone='右人指３' : RESULT : keep 1609/4506 : keep%=35.707945%
bone='右小指１' : rot : keep 2884/5256
bone='右小指１' : RESULT : keep 2884/5256 : keep%=54.870624%
bone='右小指２' : rot : keep 2246/5570
bone='右小指２' : RESULT : keep 2246/5570 : keep%=40.323160%
bone='右小指３' : rot : keep 1569/4619
bone='右小指３' : RESULT : keep 1569/4619 : keep%=33.968391%
'''

'''
9/22/2021: program is almost totally complete
running on marionette 1person dance:
TOTAL TOTAL RESULT: keep 141052/292580 = 48.21%
TIME FOR ALL BONES: 5067.36 = 84 minutes = 1.5 hr
jesus christ that's so slow, for such a poor result... and this is just the "find the keyframes" part
i still dont have the "assemble into final keyframe list" part yet

10/10/2021: optimizations and bugfixes
marionette-motion-1person-log-2.txt
includes the "assemble into final keyframe list" portion
running on marionette 1persond dance,
TOTAL TOTAL RESULT: keep 143284/292580 = 48.97%
TIME FOR ALL BONES: 3762.887979030609
down to 62 minutes! much faster!
I think most of the time comes from the armtwist/wristtwist bones

log3:
add the "find the entire linear section and operate on all monotonic segments within it" idea
from 62 minutes to 14 minutes :D
there are a sparse handful of places where one method or the other used different numbers of frames
for a section but it's a very minor difference.
'''

# enable/disable switches
SIMPLIFY_BONE_POSITION = True
SIMPLIFY_BONE_ROTATION = True

# this controls how "straight" a line has to be (in 1d morph-space) to get collapsed
# higher values = more likely to collapse = fewer frames in result, but greater deviation from original movements
MORPH_ERROR_THRESHOLD = 0.00001

BEZIER_ERROR_THRESHOLD_BONE_POSITION_RMS = 1.2
BEZIER_ERROR_THRESHOLD_BONE_POSITION_MAX = 1.2

# BONE_ROTATION_STRAIGHTNESS_VALUE = 0.15

# this controls how "straight" a line has to be (in rotation-space) to get collapsed
# higher values = more likely to collapse = fewer frames in result, but greater deviation from original movements
REVERSE_SLERP_TOLERANCE = 0.05

CONTROL_POINT_BOX_THRESHOLD = 2

# this reduces quality-of-results slightly (by not stripping out every single theoretically collapsable frame)
# but, it's needed to prevent O(n^2) compute time from getting out of hand :(
BONE_ROTATION_MAX_Z_LOOKAHEAD = 500

BONE_ROTATION_MAX_SAMPLES = 200

# TODO: use looser bezier parameters for rotation section?

# TODO: find some better way to keep the bez error constraints "realistic" for curves at all scales


# TODO: overall cleanup, once everything is acceptably working. variable names, comments, function names, etc.

# TODO: change morph-simplify to use a structure more similar to the bone-simplify structure? i.e. store frame
#  indices in a set and then get the frames back at the very end. it would be less efficient but its just for
#  more consistency between sections.

# TODO: optimize the position section of bone-simplify, add another loop layer so i don't need to keep re-finding z.

# TODO: modify the bezier regression to return the error values? i think it would just be for logging, not sure if its
#  worth changing the structure.
#  it would be useful for, "keep walking backward until you find a curve that's good, and the NEXT curve is worse"...?
#  except that no, if region M can be well fit then any subset of the region can be fit as well or better...

# TODO: even more testing to figure out what good values are for bezier error targets

# TODO: how the fuck can i effectively visualize quaternions? i need to see them plotted on a globe or something
#  so i can have confidence that my "how straight should be considered a straight line" threshold is working right


# TODO investigate 'local breakup' when length = 2(3) but it breaks into 2 segments? are there really so many Vs?

# TODO: ARMTWIST BONES are probably exclusively along one axis, whole thing is slerpable, MASSIVE efficiency loss to
#  recompute that with every pass, really should reuse past results

def get_some_interp_testpoints(start:int, end:int, maxnum:int) ->  Generator[int, None, None]:
	# basically replaces the "range" operator, but lets me cap the number of intermediate points
	# should this return as a list? or as a generator with yield? idk
	# let's set it up as a generator, sure
	R = end-start
	if R <= maxnum:
		for i in range(start,end):
			yield i
	else:
		for i in range(maxnum):
			yield start + round(i * R / maxnum)
	pass

def rotation_close(_a, _b, tol=1e-6) -> bool:
	return all(math.isclose(_aa, _bb, abs_tol=tol) for _aa, _bb in zip(_a, _b))

def find_local_peak_valley(L:List[float]) -> List[int]:
	# return the list of all local minimums or maximums in the input list
	assert len(L) >= 2
	
	if len(L) == 2: return [0,1]
	# i know that the length is 3 or greater
	s = {0, len(L)-1}  # define a set that already contains the endpoints
	# finding discrete peaks is easy... what do i do about plateaus?
	# i guess i only want to add the earliest edge of a plateau?
	# but i also want to ignore plateaus at the start or end...?
	# if i see a plateau, and then i see rising or falling (such that it creates a local minmax), then add the leading edge of the plateau
	# if it starts with a flat, which flat-state doesn't matter because 0 will be added to the set, which is fine
	# if it ends with a flat, it will never see the state stop being flat and will never add it to the set
	flat_start_idx = 0
	last_state = 3  # rising=1, falling=2, flat-last-rising=3, flat-last-falling=4
	for i in range(0, len(L)-1):
		a = L[i]    # this
		b = L[i+1]  # next
		# first, determine state of this-to-next
		if a > b:
			state = 2  # falling
		elif a < b:
			state = 1  # rising
		elif last_state == 2:
			state = 4  # flat-last-falling
			flat_start_idx = i  # if it was falling, and now flat, then save idx of beginning of flat
		elif last_state == 1:
			state = 3  # flat-last-rising
			flat_start_idx = i  # if it was rising, and now flat, then save idx of beginning of flat
		else:
			# if currently flat and was flat, then retain state
			state = last_state
		
		# second, compare with state of prev-to-this
		# in most cases, state will not change
		if last_state == state:
			pass
		# if was rising, now falling OR was falling, now rising
		elif (last_state == 1 and state == 2) or (last_state == 2 and state == 1):
			# then store idx of THIS
			s.add(i)
		# if was flat-last-rising, now falling, then store the flat-start-idx
		# if was flat-last-falling, now rising, then store the flat-start-idx
		elif (last_state == 3 and state == 2) or (last_state == 4 and state == 1):
			s.add(flat_start_idx)
		
		# third, move state to last-state
		last_state = state
		
	return sorted(list(s))

def sign(U):
	# return -1/0/+1 if input is negative/zero/positive
	if U == 0:  return 0
	elif U > 0: return 1
	else:       return -1

def scale_list(L:List[float], R: float) -> List[float]:
	"""
	Take a list of floats, shift/scale it so it starts at 0 and ends at R.
	:param L: list of floats
	:param R: range endpoint
	:return: list of floats, same length
	"""
	assert len(L) >= 2
	# one mult and one shift
	ra = L[-1] - L[0]  # current range of list
	if math.isclose(ra, 0, abs_tol=1e-6):
		# if the range is basically 0, then add 0 to the first, add R to the last, and interpolate in between
		offset = [R * s / (len(L)-1) for s in range(len(L))]
		L = [v + o for v,o in zip(L,offset)]
	else:
		# if the range is "real",
		L = [v * R / ra for v in L]  # scale the list to be the desired range
	L = [v - L[0] for v in L]  # shift it so the 0th item equals 0
	return L

def scale_two_lists(x:List[float], y:List[float], R: float) -> Tuple[List[float], List[float]]:
	"""
	Take a list of floats, shift/scale it so it starts at 0 and ends at R.
	:param x: list of floats for x
	:param y: list of floats for y
	:param R: range endpoint
	:return: list of floats, same length
	"""
	assert len(x) == len(y)
	assert len(x) >= 2
	# one mult and one shift
	# first do x
	xR = x[-1] - x[0]  # current range of list
	assert not math.isclose(xR, 0, abs_tol=1e-6)  # x must have real-valued range
	x = [v * R / xR for v in x]  # scale the list to be the desired range
	x = [v - x[0] for v in x]  # shift it so the 0th item equals 0
	# now, do y
	yR = y[-1] - y[0]
	
	if math.isclose(yR, 0, abs_tol=1e-6):
		# if the range is basically 0, then add 0 to the first, add R to the last, and interpolate in between
		# offset = [R * s / (len(x) - 1) for s in range(len(x))]  # wrong
		# offset = [core.linear_map(0, 0, x[-1], R, xx) for xx in x]  # inefficient
		offset = [R*xx/x[-1] for xx in x]
		y = [v + o for v, o in zip(y, offset)]
	else:
		# if the range is "real",
		y = [v * R / yR for v in y]  # scale the list to be the desired range
	y = [v - y[0] for v in y]  # shift it so the 0th item equals 0
	return x, y

def get_difference_quat(quatA: Tuple[float, float, float, float],
						quatB: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
	# get the "difference quaternion" that represents how to get from A to B...
	# or is this how to get from B to A?
	# as long as I'm consistent I don't think it matters?
	deltaquat_AB = core.hamilton_product(core.my_quat_conjugate(quatA), quatB)
	return deltaquat_AB

def get_quat_angular_distance(quatA: Tuple[float, float, float, float],
							  quatB: Tuple[float, float, float, float]) -> float:
	"""
	Calculate the "angular distance" between two quaternions, in radians. Opposite direction = pi.
	:param quatA: WXYZ quaternion A
	:param quatB: WXYZ quaternion B
	:return: float [0-1]
	"""
	# https://math.stackexchange.com/questions/90081/quaternion-distance
	# theta = arccos{2 * dot(qA, qB)^2 - 1}
	# unlike previous "get_corner_sharpness_factor", this doesn't discard the W component
	# so i have a bit more confidence in this approach, i think?
	quatA = core.normalize_distance(quatA)
	quatB = core.normalize_distance(quatB)
	
	a = core.my_dot(quatA, quatB)
	b = (2 * (a ** 2)) - 1
	c = core.clamp(b, -1.0, 1.0)  # this may not be necessary? better to be safe tho
	d = math.acos(c)
	# d: radians, 0 = same, pi = opposite
	# return d / math.pi
	return d

def get_corner_sharpness_factor(deltaquat_AB: Tuple[float, float, float, float],
								deltaquat_BC: Tuple[float, float, float, float],) -> float:
	"""
	Calculate a [0.0-1.0] factor indicating how "sharp" the corner is at B.
	By "corner" I mean the directional change when A->B stops and B->C begins.
	If they are going the same angular "direction", then return 1.0. If they
	are going perfectly opposite directions, return 0.0. Otherwise return something
	in between.

	:param deltaquat_AB: "delta quaterinon" WXYZ from frame A to B
	:param deltaquat_BC: "delta quaternion" WXYZ from frame B to C
	:return: float [0.0-1.0]
	"""
	
	# "how sharp a corner is" = the "angular distance" between AtoB delta and BtoC delta
	
	# first, find the deltas between the quaternions
	# deltaquat_AB = core.hamilton_product(core.my_quat_conjugate(quatA), quatB)
	# deltaquat_BC = core.hamilton_product(core.my_quat_conjugate(quatB), quatC)
	# to get sensible results below, ignore the "W" component and only use the XYZ components, treat as 3d vector
	deltavect_AB = deltaquat_AB[1:4]
	deltavect_BC = deltaquat_BC[1:4]
	# second, find the angle between these two deltas
	# use the plain old "find the angle between two vectors" formula
	len1 = core.my_euclidian_distance(deltavect_AB)
	len2 = core.my_euclidian_distance(deltavect_BC)
	if (len1 == 0) and (len2 == 0):
		# zero equals zero, so return 1!
		return 1.0
	t = len1 * len2
	if t == 0:
		# if exactly one vector has a length of 0 (but not both, otherwise it would be caught above) then they are DIFFERENT
		return 0.0
	# technically the clamp shouldn't be necessary but floating point inaccuracy caused it to do math.acos(1.000000002) which crashed lol
	shut_up = core.my_dot(deltavect_AB, deltavect_BC) / t
	shut_up = core.clamp(shut_up, -1.0, 1.0)
	ang_d = math.acos(shut_up)
	# print(math.degrees(ang_d))
	# if ang = 0, perfectly colinear, factor = 1
	# if ang = 180, perfeclty opposite, factor = 0
	factor = 1 - (ang_d / math.pi)
	return factor

def reverse_slerp(q, q0, q1) -> Tuple[float,float]:
	# https://math.stackexchange.com/questions/2346982/slerp-inverse-given-3-quaternions-find-t
	# t = log(q0not * q) / log(q0not * q1)
	# elementwise division, except skip the w component
	
	if not rotation_close(q0, q1, tol=1e-6):
		# check for and correct quaternion "handedness" to fix slerp going along wrong path
		# todo problem: the slerp is doing something strange at certain points... how is it possible for what1, what2, what3
		#  to be printed? it's a triangle, there should not be only one inequalty here????
		dot01 = core.my_dot(q0,q1)
		dot0q = core.my_dot(q0, q)
		dotq1 = core.my_dot(q, q1)
		if dot01 < 0:
			if dot0q < 0:
				# if 0!=1 and 0!=q then 0 is bad
				q0 = [-z for z in q0]
			elif dotq1 < 0:
				# if 0!=1 and q!=1 then 1 is bad
				q1 = [-z for z in q1]
			# else:
			# 	print("what1")
		elif dot0q < 0 and dotq1 < 0:
			# if 0!=q and q!=1 then q is bad
			q = [-z for z in q]
		# elif dot0q < 0:
		# 	print("what2")
		# elif dotq1 < 0:
		# 	print("what3")
		q0not = core.my_quat_conjugate(q0)
		num = core.quat_ln(core.hamilton_product(q0not, q))
		dom = core.quat_ln(core.hamilton_product(q0not, q1))
		
		# compute the result for each channel that doesn't div-by-zero-error
		# if they all get zero (should never happen i hope?) then fall thru and do the ang dist thing
		channel_results = []
		for a,b in zip(num[1:4],dom[1:4]):
			if b == 0: continue
			channel_results.append(a/b)
			
		if len(channel_results) != 0:
			# compute the average t-value
			avg = sum(channel_results) / len(channel_results)
			# compute the deviation between the channels
			channel_results.sort()  # sort the channels to be ascending
			diff = channel_results[-1] - channel_results[0]  # the diff is the biggest minus smallest
			return avg, diff
		else:
			print("ERR OH COME ON")

	
	# fall thru case
	# this also happens if b is ALL zeros
	# this happens when q0 EXACTLY EQUALS q1... so, if interpolating between Z and Z, you're not moving at all, right?
	# actually, what if something starts at A, goes to B, then returns to A? it's all perfectly linear with
	# start/end exactly the same! but it's definitely 2 segments. so I cant just return a static value.
	# i'll return the angular distance between q and q0 instead, its on a different scale but w/e, it gets
	# normalized to 127 anyways
	x = 100 * get_quat_angular_distance(q0, q)
	return x, 0
	
	


def simplify_morphframes(allmorphlist: List[vmdstruct.VmdMorphFrame]) -> List[vmdstruct.VmdMorphFrame]:
	"""
	morphs have only one dimension to worry about, and cannot have interpolation "curves"
	everything is perfectly linear!
	i'm not entirely sure that the facials are over-keyed like the bones are... but it's a good warmup
	turns out that there are a few spots with excessive keys, but it's mostly sparse like i expected

	:param allmorphlist:
	:return:
	"""
	output = []  # this is the list of frames to preserve, the startpoints and endpoints
	
	# verify there is no overlapping frames, just in case
	allmorphlist = vmdutil.assert_no_overlapping_frames(allmorphlist)
	# sort into dict form to process each morph independently
	morphdict = vmdutil.dictify_framelist(allmorphlist)
	
	print("number of morphs %d" % len(morphdict))
	# analyze each morph one at a time
	for morphname, morphlist in morphdict.items():
		print("MORPH '%s' LEN %d" % (morphname, len(morphlist)))
		# make a list of the deltas, for simplicity
		thisoutput = []
		# the first frame is always kept. and the last frame is also always kept.
		# if there is only one frame, or two, then don't even bother walking i guess?
		if len(morphlist) <= 2:
			output.extend(morphlist)
			continue
		
		# the first frame is always kept.
		thisoutput.append(morphlist[0])
		i = 0
		while i < (len(morphlist)-1):
			# start walking down this list
			# assume that i is the start point of a potentially over-keyed section
			m_this = morphlist[i]
			m_next = morphlist[i+1]
			delta_rate = (m_next.val - m_this.val) / (m_next.f - m_this.f)
			# now, walk forward from here until i "return" a frame that has a different delta
			z = 0  # to make pycharm shut up
			for z in range(i+1, len(morphlist)):
				# if i reach the end of the morphlist, then "return" the final valid index
				if z == len(morphlist)-1:
					break
				z_this = morphlist[z]
				z_next = morphlist[z + 1]
				delta_z = (z_next.val - z_this.val) / (z_next.f - z_this.f)
				if math.isclose(delta_z, delta_rate, abs_tol=MORPH_ERROR_THRESHOLD):
				# if (delta_rate - MORPH_ERROR_THRESHOLD) < delta_z < (delta_rate + MORPH_ERROR_THRESHOLD):
					# if this is within the tolerance, then this is continuing the slide and should be skipped over
					pass
				else:
					# if this delta is not within some %tolerance of matching, then this is a break!
					break
			# now, z is the index for the end of the sequence
			# it starts at i and ends at z
			# i know that i have found a segment endpoint and i can discard everything in between!
			# no need to preserve 'i', it has already been added
			thisoutput.append(morphlist[z])
			# now skip ahead and start walking from z
			i = z
		if DEBUG:
			# when i am done with this morph, how many have i lost?
			if len(thisoutput) != len(morphlist):
				print("'%s' : RESULT : keep %d/%d = %.2f%%" % (morphname, len(thisoutput), len(morphlist), 100 * len(thisoutput) / len(morphlist)))
		
		output.extend(thisoutput)
	# FIN
	print("MORPH TOTAL: keep %d/%d = %.2f%%" % (len(output), len(allmorphlist), 100 * len(output) / len(allmorphlist)))
	
	return output

def _simplify_boneframes_scalar(bonename: str,
								bonelist: List[vmdstruct.VmdBoneFrame],
								chan: str,
								getter: Callable[[vmdstruct.VmdBoneFrame], float],
								) -> Set[int]:
	"""
	Wrapper function for the sake of organization.
	
	:param bonename: str name of the bone being analyzed, for debug print
	:param bonelist: list of all boneframes that correspond to this bone
	:param chan: str label for channel being analyzed, for debug print
	:param getter: lambda func for accessing the scalar channel being analyzed
	:return: set of ints, referring to indices within bonelist that are "important frames"
	"""
	keepset = set()
	i = 0
	while i < (len(bonelist) - 1):
		# start walking down this list
		# assume that i is the start point of a potentially over-keyed section
		i_sign = getter(bonelist[i+1]) > getter(bonelist[i])
		
		# +++++++++++++++++++++++++++++++++++++
		# zero-change shortcut
		z = i+1  # to make pycharm shut up
		# while (z < len(bonelist)) and math.isclose(bonelist[i].pos[C], bonelist[z].pos[C], abs_tol=1e-4):
		while (z < len(bonelist)) and getter(bonelist[i]) == getter(bonelist[z]):
			z += 1
		if z != i+1:  # if the while-loop went thru at least 1 loop,
			z -= 1  # back off one value, since z is the value that no longer matches,
			if DEBUG >= 2:
				print(f"MATCH! bone='{bonename}' {chan} : i-z= {i}-{z} : pts={z-i+1} (ZERO CHANGE)")
			keepset.add(z)  # add this endpoint
			i = z  # and move the startpoint to here and keep walking from here
			continue
		
		# +++++++++++++++++++++++++++++++++++++
		# now, walk forward from here until i "return" the frame "z" that has a different delta
		# "z" is the farthest plausible endpoint of the section (the real endpoint might be between i and z, tho)
		# "different" means only different state, i.e. rising/falling/zero
		
		for z in range(i + 1, len(bonelist)):
			# if i reach the end of the bonelist, then "return" the final valid index
			if z == len(bonelist) - 1:
				break
			z_this = bonelist[z]
			z_next = bonelist[z + 1]
			z_sign = getter(z_next) > getter(z_this)
			# TODO: also break if the delta is way significantly different than the previous delta?
			#  pretty sure this concept is needed for the camera jumpcuts to be guaranteed detected?
			if z_sign == i_sign:
				pass  # if this is potentially part of the same sequence, keep iterating
			else:
				break  # if this is definitely no longer part of the sequence, THEN i can break
		# anything past z is DEFINITELY NOT the endpoint for this sequence
		# everything from i to z is monotonic: always increasing OR always decreasing
		
		# +++++++++++++++++++++++++++++++++++++
		# generate all the x-values and y-values (will scale to [0-127] later)
		x_points_all, y_points_all = make_xy_from_segment_scalar(bonelist, i, z, getter, noscale=True)
		assert len(x_points_all) == len(y_points_all)
		
		# +++++++++++++++++++++++++++++++++++++
		# use this function to break this monotonic data into as many bezier segments as necessary
		k = make_beziers_from_datarange(x_points_all, y_points_all, i, i, bonename, chan)
		i = max(k)
		keepset.update(k)
		pass  # end "while i < len(bonelist)"
	
	# now i have found every frame# that is important for this axis
	if DEBUG and len(keepset) > 1:
		# ignore everything that found only 1, cuz that would mean just startpoint and endpoint
		# add 1 to the length cuz frame 0 is implicitly important to all axes
		print(f"'{bonename}' {chan} : keep {len(keepset)+1}/{len(bonelist)}")
	return keepset


def _simplify_boneframes_rotation(bonename: str, bonelist: List[vmdstruct.VmdBoneFrame]) -> Set[int]:
	"""
	Wrapper function for the sake of organization.
	:param bonename: str name of the bone being operated on
	:param bonelist: list of all boneframes that correspond to this bone
	:return: set of ints, referring to indices within bonelist that are "important frames"
	"""
	chan = "R"
	
	keepset = set()
	i = 0
	while i < (len(bonelist) - 1):
		# start walking down this list
		# assume that i is the start point of a potentially over-keyed section
		i_this = bonelist[i]
		i_this_quat = core.euler_to_quaternion(i_this.rot)
		
		# todo problem: how do i distinguish between when it is most efficient to group a bunch of frames as zeros, vs
		#  when it's really just a veeeeery slow lead-in to a bezier-matchable curve?
		# +++++++++++++++++++++++++++++++++++++
		# zero-rotation shortcut
		z = i+1  # to make pycharm shut up
		# while (z < len(bonelist)) and rotation_close(bonelist[i].rot, bonelist[z].rot):
		while (z < len(bonelist)) and bonelist[i].rot == bonelist[z].rot:
			z += 1
		if z != i + 1:  # if the while-loop went thru at least 1 loop,
			z -= 1  # back off one value, since that's the value that no longer matches
			if DEBUG >= 2:
				print(f"MATCH! bone='{bonename}' {chan} : i-z= {i}-{z} : pts={z-i+1} (ZERO CHANGE)")
			keepset.add(z)  # add this endpoint
			i = z
			continue
			
		# +++++++++++++++++++++++++++++++++++++
		# now, walk FORWARD from here until i identify a frame z that might be an 'endpoint' of an over-key section
		for z in range(i + 1, len(bonelist)):
			z_this_quat = core.euler_to_quaternion(bonelist[z].rot)
			# walk forward from here, testing frames as i go
			# if i can succesfully reverse-slerp everything from i to z, then z is a valid endpoint!
			# success means all reverse-slerp dimensions are close to equal
			endpoint_good = True
			temp_reverse_slerp_diffs = []
			# NEW IDEA: put a ceiling on the number of points that i test! even if i=7 and z=1007, only test 200 points
			#  evenly spaced between those two ends. it's still really slow, but it's not O(n^2) any more ;)
			for q in get_some_interp_testpoints(i + 1, z, maxnum=BONE_ROTATION_MAX_SAMPLES):
				q_this_quat = core.euler_to_quaternion(bonelist[q].rot)
				# calculate reverse-slerp for this start/end/intermediate
				# note: if start==end, then divergence=0 and avg=distance in radians
				avg, divergence = reverse_slerp(q_this_quat, i_this_quat, z_this_quat)
				# "avg" = average of independent results from all 3 x/y/z channels
				# "divergence" = greatest difference between these 3 results
				temp_reverse_slerp_diffs.append(divergence)
				# if any of the frames between i and z cannot be reverse-slerped, then break
				if divergence >= REVERSE_SLERP_TOLERANCE:
					endpoint_good = False
					break
			# if (DEBUG >= 3) and temp_reverse_slerp_diffs:
			# 	divergence = max(temp_reverse_slerp_diffs)
			# 	print("rev-slerp-quality : i-z= %d-%d, diff=%.8f" % (i, z, divergence))
			if not endpoint_good:
				# when i find something that is a BAD endpoint, i know (assume?) that the one before was GOOD.
				# so, "return" z-1
				z -= 1
				if DEBUG >= 2:
					if temp_reverse_slerp_diffs:
						print(f"rev-slerp-segment : i-z= {i}-{z} : pts={z-i+1}" + (" : nextdiff=%.5f" % max(temp_reverse_slerp_diffs)))
					else:
						print(f"rev-slerp-segment : i-z= {i}-{z} : pts={z-i+1}")
				break
			else:
				# if i got thru all the points between i and z, and they all passed, then this z is the last known good endpoint
				pass
		
		# if i == 1190:
		# 	DEBUG_PLOTS = True
		
		# now i have z, and anything past z is DEFINITELY NOT the endpoint for this sequence
		# everything from i to z is "slerpable", meaning it is all falling on a linear arc
		# BUT, that doesn't mean it's all on one bezier! it might be several beziers in a row...

		# next, properly calculate the x and y datapoints that will be used for bezier fitting
		x_points_all, y_points_all = make_xy_from_segment_rotation(bonelist, i, z, noscale=True)

		# now i have x_points_all and y_points_all, same length, both in range [0-1], including endpoints
		# because of slerp oddities it is possible that the y-points in the middle are outside [0-1] but thats okay i think
		assert len(x_points_all) == len(y_points_all)
		
		# +++++++++++++++++++++++++++++++++++++
		# the y-datapoints should be STRICTLY MONOTONIC (increasing or decreasing), so break the current y-values
		#  apart until that's the case!
		if z-i >= BONE_ROTATION_MAX_SAMPLES:
			print(f"LONG SEGMENT : i-z= {i}-{z} : pts={z-i+1}")
		local_minmax = find_local_peak_valley(y_points_all)
		if (DEBUG >= 2) and (len(local_minmax) != 2):
			# if breakup is needed (not often) then print a message
			print(f"breakup : i-z= {i}-{z} : pts={z-i+1} : numseg={len(local_minmax)} : list=" + str([i+v for v in local_minmax]))
			# plt.plot(x_points_all, y_points_all, 'r+')
			# plt.show(block=True)
		if DEBUG_PLOTS:
			if len(x_points_all) > 2:
				print("reverse-slerp: bone='%s' : i-z= %d-%d" % (bonename, i, z))
				plt.plot(x_points_all, y_points_all, 'r+')
				plt.show(block=True)
		
		# +++++++++++++++++++++++++++++++++++++
		# if breakup was not needed, then i can safely make beziers from the one region that was found
		# if breakup was needed, then i should make beziers from all monotonic segments except the last?? half?? all??
		# lets start with all
		initial_i = i
		for mm in range(len(local_minmax)-1):
			local_start = local_minmax[mm]
			local_end = local_minmax[mm+1]
			x_points = x_points_all[local_start:local_end+1]
			y_points = y_points_all[local_start:local_end+1]
		
			k = make_beziers_from_datarange(x_points, y_points, local_start + initial_i, local_end + initial_i, bonename, chan)
			i = max(k)
			keepset.update(k)
		
		pass  # end "while i < len(bonelist)"
	# now i have found every frame# that is important due to position changes
	if DEBUG and len(keepset) > 1:
		# if it found only 1, ignore it, cuz that would mean just startpoint and endpoint
		# add 1 to the length cuz frame 0 is implicitly important to all axes (added to set in outer level)
		# print("'%s' : rot : keep %d/%d" % (bonename, len(keepset) + 1, len(bonelist)))
		print(f"'{bonename}' {chan} : keep {len(keepset) + 1}/{len(bonelist)}")
	return keepset

def make_beziers_from_datarange(x_points_all: List[float], y_points_all: List[float], i: int, z: int, bonename: str, chan: str):
	"""
	This function accepts a series of XY datapoints that define a strictly monotonic range.
	Then it uses a "greedy" algorithm to define that range with the fewest possible number of bezier curves.
	Its output is the INDICES of the frames that can define endpoints for reasonable bezier curves.

	I still need to figure out how to fix the bezier-fitting-error problems tho...
	Maybe it will be solved if I do the scaling outside this function, in some special way?

	:param x_points_all: list of float x-vals for xy pairs of data
	:param y_points_all: list of float y-vals for xy pairs of data
	:param i: int idx within bonelist where the datarange starts
	:param z: int idx within bonelist where the datarange ends (inclusive)
	:param bonename: str name of bone, for debug printing
	:param chan: str name of channel, for debug printing
	:return: set of ints in i/z scope
	"""
	# i know that the list of points I am given is STRICTLY MONOTONIC
	# so, attempt to fit some number of beziers to this section
	keepset = set()
	
	# OPTIMIZE: if i find z, then walk backward a bit and find a good bezier, i can reuse the same z!
	# no need to re-walk forward cuz i'll just find the same z-point.
	
	num_all_points = len(x_points_all)
	found_beziers = []  # list of all beziers i find
	segment_count = 0  # which segment i am finding/have found
	
	v = 0  # v is the start of "this segment", w is the end of "this segment" (inclusive)
	# both v and w are always valid indices within the lists, will never equal the length
	
	# keep finding bezier segments until a segment ends on the final frame
	while v != (num_all_points-1):
		# w is the relative index within this i-to-z stretch
		# w is always a valid index within the lists
		# it starts at z, and counts down to i (should never actually hit i tho, should always pass when it's 2 points)
		for w in reversed(range(v, num_all_points)):
			# take a subset of the range of points, and scale them to [0-127] range
			x_points, y_points = scale_two_lists(x_points_all[v:w + 1], y_points_all[v:w + 1], 127)
			
			# then run regression to find a reasonable interpolation curve for this stretch
			# this innately measures both the RMS error and the max error, and i can specify thresholds
			# if it cannot satisfy those thresholds it will split and try again
			bezier_list = vectorpaths.fit_cubic_bezier(x_points, y_points,
													   rms_err_tol=BEZIER_ERROR_THRESHOLD_BONE_POSITION_RMS,
													   max_err_tol=BEZIER_ERROR_THRESHOLD_BONE_POSITION_MAX)
			
			# if it has split, then it's not good for my purposes
			# note: i modified the code so that if it would split, it returns an empty list instead
			# TODO: it would be WAY more efficient if i could trust/use the splitting in the algorithm, but it changes
			#  the location of the endpoints without scaling the error metrics so each split makes it easier to be
			#  accepted, even without actually fitting any better
			if len(bezier_list) != 1:
				continue
			# if any control points are not within the box, it's no good
			# (well, if its only slightly outside the box thats okay, i can clamp it)
			bez, rms_error, max_error = bezier_list[0]
			cpp = (bez.p[1][0], bez.p[1][1], bez.p[2][0], bez.p[2][1])
			if not all((0 - CONTROL_POINT_BOX_THRESHOLD < p < 127 + CONTROL_POINT_BOX_THRESHOLD) for p in cpp):
				continue
			
			# once i find a good interp curve match (if a match is found),
			found_beziers.append(bez)
			segment_count += 1
			keepset.add(i + w)  # then save this proposed endpoint as a valid endpoint,
			if DEBUG >= 2 or DEBUG_PLOTS:
				# i thru z is the full monotonic stretch
				# v thru w is one bezier curve on the stretch
				if (w == num_all_points-1) and (segment_count == 1):
					# if one stretch of input data can be matched to one bezier curve, then don't print the segcnt
					print(f"MATCH! bone='{bonename}' {chan} : i-z= {i}-{z} : v-w= {i+v}-{i+w} : pts={w-v+1}")
					# print("MATCH! bone='%s' : i-z= %d-%d : v-w= %d-%d : pts=%d" %
					# 	  (bonename, i, z, i+v, i+w, w-v+1))
				else:
					# if there are more than 1 segment, then each also prints its index
					print(f"MATCH! bone='{bonename}' {chan} : i-z= {i}-{z} : v-w= {i+v}-{i+w} : pts={w-v+1} : #={segment_count}")
					# print("MATCH! bone='%s' : i-z= %d-%d : v-w= %d-%d : pts=%d : seg=%d%s" %
					# 	  (bonename, i, z, i+v, i+w, w-v+1, segment_count, "*" if (w == num_all_points-1) else ""))
				# only show the graph if it is more than a simple two-point line segment
				if (w-v+1 > 2) and DEBUG_PLOTS:
					bez.plotcontrol()
					bez.plot()
					plt.plot(x_points, y_points, 'r+')
					plt.show(block=True)
					
			v = w  # where this segment ends is where the next segment will begin
			break
			# if i let it iterate all the way down to 2 points then it is guaranteed to find a match (cuz linear)
			# actually it's probably also guaranteed to pass at 3 points. do i want that? hm... probably not?
			pass  # end walking backwards from z to i
	return keepset

def simplify_boneframes(allbonelist: List[vmdstruct.VmdBoneFrame]) -> List[vmdstruct.VmdBoneFrame]:
	"""
	dont yet care about phys on/off... but, eventually i should.
	only care about x/y/z/rotation
	
	:param allbonelist:
	:return:
	"""
	
	# verify there is no overlapping frames, just in case
	allbonelist = vmdutil.assert_no_overlapping_frames(allbonelist)
	# sort into dict form to process each morph independently
	bonedict = vmdutil.dictify_framelist(allbonelist)
	
	# for progress printouts
	totalbonelen = len(allbonelist)
	sofarbonelen = 0
	
	# the final list of all boneframes that i am keeping
	allbonelist_out = []
	
	print("number of bones %d" % len(bonedict))
	# analyze each morph one at a time
	for bonename, bonelist in bonedict.items():
		# if bonename != "センター":
		# 	continue
		# if bonename != "上半身":
		# 	continue
		# if bonename != "右足ＩＫ" and bonename != "左足ＩＫ" and bonename != "上半身" and bonename != "センター":
		# 	continue
		# if bonename != "右足ＩＫ":
		# 	continue
		# if bonename != "上半身2":
		# 	continue
		print("BONE '%s' LEN %d" % (bonename, len(bonelist)))
		sofarbonelen += len(bonelist)
		core.print_progress_oneline(sofarbonelen/totalbonelen)
		
		if len(bonelist) <= 2:
			allbonelist_out.extend(bonelist)
			continue
		
		# since i need to analyze what's "important" along 4 different channels,
		# i think it's best to store a set of the indices of the frames that i think are important?
		keepset = set()
		
		# the first frame is always kept.
		keepset.add(0)
		
		#######################################################################################
		if SIMPLIFY_BONE_POSITION:
			k = _simplify_boneframes_scalar(bonename, bonelist, "posX", lambda x: x.pos[0])
			keepset.update(k)
			k = _simplify_boneframes_scalar(bonename, bonelist, "posY", lambda x: x.pos[1])
			keepset.update(k)
			k = _simplify_boneframes_scalar(bonename, bonelist, "posZ", lambda x: x.pos[2])
			keepset.update(k)
			# now i have found every frame# that is important due to position changes
			if DEBUG and len(keepset) > 2:
				# if it found only 2, ignore it, cuz that would mean just startpoint and endpoint
				print(f"'{bonename}' posALL : keep {len(keepset)}/{len(bonelist)}")
		
		#######################################################################################
		# now, i walk along the frames analyzing the ROTATION channel. this is the hard part.
		if SIMPLIFY_BONE_ROTATION:
			k = _simplify_boneframes_rotation(bonename, bonelist)
			keepset.update(k)
			
		#######################################################################################
		# now done searching for the "important" points, filled "keepset"
		if DEBUG and len(keepset) > 2:
			# if it found only 2, dont print cuz that would mean just startpoint and endpoint
			print("'%s' : RESULT : keep %d/%d = %.2f%%"% (
				bonename, len(keepset), len(bonelist), 100*len(keepset)/len(bonelist)))
			
		# recap: i have found the minimal set of frames needed to define the motion of this bone,
		# i.e. the endpoints where a bezier can define the motion between them.
		# when i unify the sets from each source, i am makign those segments shorter.
		# if a bezier curve can be fit onto points A thru Z, then it's guaranteed that a bezier curve can
		# be fit onto points A thru M and separately onto points M thru Z.
		# i know it's possible, so, thats what i'm doing now.
		
		r = _finally_put_it_all_together(bonelist, keepset)
		allbonelist_out.extend(r)
		pass  # end "for each bonename, bonelist"
	print("TOTAL TOTAL RESULT: keep %d/%d = %.2f%%" % (len(allbonelist_out), len(allbonelist), 100 * len(allbonelist_out) / len(allbonelist)))
	return allbonelist_out

def _finally_put_it_all_together(bonelist: List[vmdstruct.VmdBoneFrame], keepset: Set[int]) -> List[vmdstruct.VmdBoneFrame]:
	"""
	I have found the minimal set of frames needed to define the motion of this bone with respect to each separate
	channel... when I unify the sets from each source, I am inserting new points into the middle of most segments.
	If a bezier curve can be fit onto points A thru Z, then it's guaranteed that a bezier curve can be fit onto
	points A thru M and separately onto points M thru Z.
	So now I am re-generating the beziers and this time I actually change the interp parameters.
	
	:param bonelist: list of all boneframes that correspond to this bone
	:param keepset: set of ints, referring to indices within bonelist that are "important frames"
	:return: list of the boneframes that 'keepset' refers to, with the interpolation parameters modified
	"""
	
	# if DEBUG >= 2:
	# 	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
		
	# turn the set into sorted list for walking
	keepframe_indices = sorted(list(keepset))
	
	# frame 0 always gets in, so just add it now
	# don't even need to modify it's interp curves, since it's the first frame its curves dont matter
	output = [bonelist[keepframe_indices[0]]]
	
	# for each of them, re-calculate the best interpolation curve for each channel based on the frames between the keepframes
	for a in range(len(keepset) - 1):
		# for each start/end pair,
		idx_this = keepframe_indices[a]
		idx_next = keepframe_indices[a + 1]
		# for each channel (x/y/z/rot),
		# look at all the points in between (including endpoints) and scale to [0-127],
		allxally = [make_xy_from_segment_scalar(bonelist, idx_this, idx_next, lambda x: x.pos[0]), # x pos
					make_xy_from_segment_scalar(bonelist, idx_this, idx_next, lambda x: x.pos[1]), # y pos
					make_xy_from_segment_scalar(bonelist, idx_this, idx_next, lambda x: x.pos[2]), # z pos
					make_xy_from_segment_rotation(bonelist, idx_this, idx_next),                   # rotation
					]
		all_interp_params = []
		# for each channel (x/y/z/rot),
		# generate the proper bezier interp curve,
		for d,(x_points,y_points) in enumerate(allxally):
			bezier_list = vectorpaths.fit_cubic_bezier(x_points, y_points,
													   rms_err_tol=BEZIER_ERROR_THRESHOLD_BONE_POSITION_RMS,
													   max_err_tol=BEZIER_ERROR_THRESHOLD_BONE_POSITION_MAX,
													   max_reparam_iter=50,
													   return_best_onelevel=True)
			# TODO: this assertion failed! why!? damnit i dont want to explore this more right now...
			#  basically, the previous steps find endpoints that allow for 'close enogh' fits, not perfect fits.
			#  so at this stage, any sub-segments are also going to be only 'close enough'. BUT, because they are
			#  shorter segments being scaled up to full 0-127 size, the error threshold is relatively tighter...
			#  and in some cases, it's too difficult to attain.
			# TODO to fix this i need to allow this part of the algorithm to return its "best effort fit", even if it
			#  doesn't get below the error threshold. that's simple enough!
			# TODO other idea: use the recursion and return list of results like originally designed
			#  (need switch to toggle between these two behaviors)
			
			# 168,179 on channel0(x) isn't able to refine well enough
			# best = RMSerr=0.8171 and MAXerr=1.3291
			# but 165,179 was able to get below the error threshold!
			# needs 52 iterations to get below 1.2, but it gets there
			
			# another problem, a later one fails with RMSerr=1.6185 and MAXerr=2.8596 after 100 iterations
			# i,z=223,230, chan=1
			# that can't be fixed by just letting it run longer...
			# max-err bottoms at 2.8406 at iter 10, and increases from there
			a = bezier_list[0]
			bez, rms_error, max_error = a
			
			# if rms_error > BEZIER_ERROR_THRESHOLD_BONE_POSITION_RMS or max_error > BEZIER_ERROR_THRESHOLD_BONE_POSITION_MAX:
			if max_error > 10:
				print("bad fit : i,z=%d,%d, chan=%d : rmserr %f maxerr %f" % (idx_this, idx_next, d, rms_error, max_error))
				print(bez.p)
				# bez.plotcontrol()
				# bez.plot()
				# plt.plot(x_points, y_points, 'r+')
				# plt.show(block=True)

			# clamp all the control points to valid [0-127] range, and also make them be integers
			cpp = (bez.p[1][0], bez.p[1][1], bez.p[2][0], bez.p[2][1])
			params = [round(core.clamp(v, 0, 127)) for v in cpp]
			all_interp_params.append(params)
			
		# for each channel (x/y/z/rot),
		# store the params into the proper field of frame_next,
		frame_next = bonelist[idx_next]
		frame_next.interp_x = all_interp_params[0]
		frame_next.interp_y = all_interp_params[1]
		frame_next.interp_z = all_interp_params[2]
		frame_next.interp_r = all_interp_params[3]
		
		# and finally store the modified frame in the ultimate output list.
		output.append(frame_next)
	# verify that i stored one frame for each value in keepset
	assert len(output) == len(keepset)
	return output


def make_xy_from_segment_rotation(bonelist: List[vmdstruct.VmdBoneFrame],
								  idx_this:int,
								  idx_next:int,
								  noscale=False) -> Tuple[List[float], List[float]]:
	# for each channel (x/y/z/rot),
	# look at all the points in between (including endpoints),
	frame_this = bonelist[idx_this]
	y_points = []
	x_points = []
	quat_start = core.euler_to_quaternion(frame_this.rot)
	quat_end = core.euler_to_quaternion(bonelist[idx_next].rot)
	for i in range(idx_this, idx_next + 1):
		point = bonelist[i]
		x_pos = point.f - frame_this.f
		x_points.append(x_pos)
		q = core.euler_to_quaternion(point.rot)
		avg,diff = reverse_slerp(q, quat_start, quat_end)
		y_points.append(avg)
	if noscale: return x_points, y_points
	else:       return scale_two_lists(x_points, y_points, 127)

def make_xy_from_segment_scalar(bonelist: List[vmdstruct.VmdBoneFrame],
								idx_this:int,
								idx_next:int,
								getter: Callable[[vmdstruct.VmdBoneFrame], float],
								noscale=False) -> Tuple[List[float], List[float]]:
	# look at all the points in between (including endpoints),
	x_points = [bonelist[i].f for i in range(idx_this, idx_next + 1)]
	y_points = [getter(bonelist[i]) for i in range(idx_this, idx_next + 1)]
	# y_points = []
	# x_points = []
	# for i in range(idx_this, idx_next + 1):
	# 	point = bonelist[i]
	# 	x_pos = point.f - bonelist[idx_this].f
	# 	x_points.append(x_pos)
	# 	y_pos = getter(point) - getter(bonelist[idx_this])
	# 	y_points.append(y_pos)
	if noscale: return x_points, y_points
	else:       return scale_two_lists(x_points, y_points, 127)



def main(moreinfo=True):
	###################################################################################
	# prompt for inputs
	# vmdname = core.MY_FILEPROMPT_FUNC("VMD file", ".vmd")
	# vmdname = "../../../Apple Pie_Cam-interpolated.vmd"
	vmdname = "../../../marionette motion 1person.vmd"
	# vmdname = "../../../IA_Conqueror_full_key_version.vmd"
	vmd = vmdlib.read_vmd(vmdname)
	
	anychange = False
	
	if vmd.morphframes:
		start = time.time()
		newmorphs = simplify_morphframes(vmd.morphframes)
		morphend = time.time()
		print("TIME FOR ALL MORPHS:", morphend - start)
		if newmorphs != vmd.morphframes:
			print('morphs changed')
			anychange = True
			vmd.morphframes = newmorphs
			
	if vmd.boneframes:
		start = time.time()
		newbones = simplify_boneframes(vmd.boneframes)
		boneend = time.time()
		print("TIME FOR ALL BONES:", boneend - start)
		if newbones != vmd.boneframes:
			print('bones changed')
			anychange = True
			vmd.boneframes = newbones
			
			
	if vmd.camframes:
		# framenums = [cam.f for cam in vmd.camframes]
		# rotx = [cam.rot[0] for cam in vmd.camframes]
		# roty = [cam.rot[1] for cam in vmd.camframes]
		# rotz = [cam.rot[2] for cam in vmd.camframes]
		# plt.plot(framenums, rotx, label="x")
		# plt.plot(framenums, roty, label="y")
		# plt.plot(framenums, rotz, label="z")
		# plt.legend()
		# plt.show()
		
		for i in range(len(vmd.camframes) - 1):
			cam = vmd.camframes[i]
			nextcam = vmd.camframes[i+1]
			rot_delta = [f - i for f,i in zip(nextcam.rot, cam.rot)]
			framedelta = nextcam.f - cam.f
			rot_delta = [r/framedelta for r in rot_delta]
			# print(cam.rot)
			try:
				r1 = rot_delta[0] / rot_delta[1]
			except ZeroDivisionError:
				r1 = 0
			try:
				r2 = rot_delta[1] / rot_delta[2]
			except ZeroDivisionError:
				r2 = 0
			try:
				r3 = rot_delta[0] / rot_delta[2]
			except ZeroDivisionError:
				r3 = 0
			if cam.f in (460, 2100, 2149):
				print('hi')
			print(cam.f, round(r1, 3), round(r2, 3), round(r3, 3))
	
	core.MY_PRINT_FUNC("")
	###################################################################################
	# write outputs

	if not anychange:
		core.MY_PRINT_FUNC("nothing changed, nothing to write")
		return None
	else:
		output_filename_vmd = core.filepath_insert_suffix(vmdname, "_simplified")
		output_filename_vmd = core.filepath_get_unused_name(output_filename_vmd)
		vmdlib.write_vmd(output_filename_vmd, vmd, moreinfo=moreinfo)
	
	core.MY_PRINT_FUNC("Done!")
	return None

if __name__ == '__main__':
	core.MY_PRINT_FUNC(_SCRIPT_VERSION)
	core.MY_PRINT_FUNC(helptext)
	core.RUN_WITH_TRACEBACK(main)
	
	# cProfile.run('main()', 'uninterpolate_stats')
	# ppp = pstats.Stats('uninterpolate_stats')
	# ppp.sort_stats(pstats.SortKey.CUMULATIVE)
	# ppp.print_stats()
	
	# x = [0] + [50]*50 + [100]
	# y = [0] + [50]*50 + [100]
	# print(vectorpaths.fit_cubic_bezier(x, y, rms_err_tol=1.0))
	
	# e1 = [0, 0, 0]
	# e2 = [0, 10, 0]
	# e3 = [0, 20, 0]
	# e4 = [43, 25, -4]
	# e5 = [43, 35, -4]
	# q1 = core.euler_to_quaternion(e1)
	# q2 = core.euler_to_quaternion(e2)
	# q3 = core.euler_to_quaternion(e3)
	# q4 = core.euler_to_quaternion(e4)
	# q5 = core.euler_to_quaternion(e5)
	#
	# d12 = get_difference_quat(q1, q2)
	# d23 = get_difference_quat(q2, q3)
	# d45 = get_difference_quat(q4, q5)
	#
	# print(d12)
	# print(d23)
	# print(d45)
	#
	# dist1 = get_quat_angular_distance(q1, q2)
	# dist2 = get_quat_angular_distance(q1, q3)
	# print(dist1)
	# print(dist2)
	# dist1 = get_quat_angular_distance(q1, q4)
	# dist2 = get_quat_angular_distance(q1, q5)
	# print(dist1)
	# print(dist2)
	# print(get_quat_angular_distance(q1, core.euler_to_quaternion((180, 0, 0))))
	# print(get_quat_angular_distance(q1, core.euler_to_quaternion((0, 180, 0))))
	# print(get_quat_angular_distance(q1, core.euler_to_quaternion((0, 0, 180))))
	# pass
	
	# data = [[-34.18498160983529, 162.36696123640758, -47.77082064976655],
	# 		[-33.254664043042155, 166.45073669252278, -51.87984353641723],
	# 		[-32.0425151793791, 171.39295902289882, -56.85758479140585],
	# 		[-30.312845492276253, 176.89607074752024, -62.42481334883806],
	# 		[-27.887332931654115, -177.3761874021451, -68.26338866456251],
	# 		[-24.670456884890783, -171.76023745536244, -74.05532823555019],
	# 		[-20.65589689213871, -166.54581281354416, -79.53089393235882],
	# 		[-15.913903709063252, -161.94521858255777, -84.50036877773108],
	# 		]
	#
	# # code block to validate the SLERP code via 3d plotting
	# original_point = [1, 0, 0]
	# t_list = [i/20 for i in range(20)]
	#
	# # quat1 = core.euler_to_quaternion(euler1)
	# # quat2 = core.euler_to_quaternion(euler2)
	# point_list = []
	# # point_list_new = []
	# for rot in data:
	# 	qrot = core.euler_to_quaternion(rot)
	# 	newpoint = core.rotate3d((0,0,0), qrot, original_point)
	# 	point_list.append(newpoint)
	# 	# rot = core.new_slerp(quat1, quat2, t) # new slerp
	# 	# newpoint = core.rotate3d((0, 0, 0), rot, original_point)
	# 	# point_list_new.append(newpoint)
	# # now graph them
	# fig = plt.figure()
	# ax = fig.add_subplot(111, projection='3d')
	# x,y,z = zip(*point_list)
	# ax.scatter(x,y,z, label="old")
	# # x,y,z = zip(*point_list_new)
	# # ax.scatter(x,y,z, label="new")
	# ax.scatter(0,0,0, label="origin")  # plot the origin too
	# ax.set_xlim(-1, 1)
	# ax.set_ylim(-1, 1)
	# ax.set_zlim(-1, 1)
	# # STARTPOINT = core.rotate3d((0,0,0), quat1, original_point)
	# # ENDPOINT = core.rotate3d((0,0,0), quat2, original_point)
	# # ax.scatter(*STARTPOINT, marker='x', label='START')
	# # ax.scatter(*ENDPOINT, marker='x', label='END')
	# ax.legend()
	# plt.show(block=True)
	#
