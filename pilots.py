from pywinauto import *
import os
import sys
import traceback
from PIL import Image, ImageFont, ImageDraw, ImageGrab
import time
sys.path.append('C:\Python27\Lib\site-packages')
sys.path.append('C:\Python27\Lib\site-packages\opencv')
import cv2
import numpy as np
import win32gui, win32ui, win32con, win32api
import logging
import cProfile
import threading
import pyHook
import pythoncom

#define constants
to_pool = (624, 545)
delay = (809, 267)
pilot_heights = map(lambda x: 10*x + 280, range(26))


pilot_cats_add = []
pos = 326
for i in range(18):
	pilot_cats_add.append(pos)
	if i < 1:
		pos += 20
	elif i < 3:
		pos += 35
	elif i < 4:
		pos += 30
	else:
		pos += 25


pilot_cats_release = map(lambda x: 30*x + 326, range(18))



pilot_names = zip([233]*26, pilot_heights)
Fgroup = (277, 256)
prev_group = (252, 593)
pool_box = (607, 537, 660, 552)
pool_switch = (621, 544)

Least = 556
Most = 542
Release1 = 291
Release5 = 372
Release10 = 463
PoolOffset = 158
Done = (832, 556)
AddPilotScreen_Back = (768, 556)
NextRight = (732, 593)
PilotsButtonCoord = (181, 593)
RequestVeteran = (173, 348)
GetNPilots = (263, 335)
GetNewPilot = (173, 335)
Transfer2Active = 515, 459

AlliedPlaneLocations = {
'AllTypes' : 240,
'F' : 276,
'FB' : 302,
'NF' : 323,
'DB' : 343,
'BM' : 359,
'HB' : 383,
'MB' : 405,
'LB' : 422,
'AB' : 443,
'RC' : 458,
'TR' : 483,
'PA' : 496,
'FP' : 522,
'FF' : 542,
'TB' : 563
}

AlliedNationLocations = {
'AllNations' :241,
'USN' : 307,
'USA' : 333,
'USMC' : 368,
'Aus' : 407,
'NZ' : 435,
'Brit' : 469,
'FFr' : 497,
'Dut' : 527,
'Chi' : 559,
'Sov' : 586,
'Ind' : 616,
'CW' : 648,
'Phil' : 679,
'Can' : 709
}

PoolSourceLocation = {
'All' : 243,
'Fighter' : 277,
'Bomber': 339,
'Patrol': 391,
'Transport': 451,
'Recon': 511
}

PoolMapping = {
'F' : 'Fighter',
'FB' : 'Fighter',
'NF' : 'Fighter',
'DB' : 'Bomber',
'BM' : 'Bomber',
'HB' : 'Bomber',
'MB' : 'Bomber',
'LB' : 'Bomber',
'AB' : 'Bomber',
'RC' : 'Recon',
'TR' : 'Transport',
'PA' : 'Patrol',
'FP' : 'Patrol',
'FF' : 'Fighter',
'TB' : 'Bomber'
}


SkillMissionMapping = {
'Air' : 'Escort',
'GrdB' : 'AirfieldAttack',
'NavB' : 'NavalAttack',
'NavT' : 'NavalAttack',
'NavS' : 'NavalSearch',
'Recn' : 'Recon',
'ASW' : 'ASWPatrol',
'Tran' : 'SupplyTranspot',
'LowN' : 'NavalAttack',
'LowG' : 'AirfieldAttack',
'Staf' : 'General',
'Defn' : 'General'
}

MissionSkillMapping = {
'AirfieldAttack' : 'Air',
'ASWPatrol' : 'ASW',
'Escort' : 'Air',
'GroundAttack' : ['LowG', 'GrdB'],
'NavalAttack' : ['LowN', 'NavB'],
'NavalSearch' : 'NavS', 
'PortAttack' : 'GrdB',
'Recon' : 'Recn',
'SupplyTransport' : 'Tran',
'General' : 'Defn',
'Sweep' : 'Air'
}

SkillIndexMapping = {
'Exp' : 3,
'Air' : 4,
'NavB' : 5,
'NavT' : 6,
'NavS' : 7,
'Recn' : 8,
'ASW' : 9,
'Tran' : 10,
'GrdB' : 11,
'LowN' : 12,
'LowG' : 13,
'Staf' : 14,
'Defn' : 15,
'Delay' : 16,
'Retain' : 17,
'Group' : 17
}

CommonPilotSkills = [
'Exp',
'Air',
'NavB',
'NavT',
'NavS',
'Recn',
'ASW',
'Tran',
'GrdB',
'LowN',
'LowG',
'Staf',
'Defn',
]

AddPilotSkills = CommonPilotSkills
ReleasePilotSkills = CommonPilotSkills + ['Delay']


def log_message(text, level=0, override_level=-2):
	should_log = True
	#its off
	if override_level < -1:
		if message_level > 0:
			if level > message_level:
				should_log = False
	#using ovr
	elif override_level > 0:
		if level > override_level:
				should_log = False
		
		
	if should_log:
		text = "\t"*level + text
		print text
		#log text is more complete			
		func_trace = ''
		for line in traceback.extract_stack()[-4:-2]:
			if func_trace:
				func_trace += '_'
			#FIXME: Just get function name
			#func_trace += line[-1]
			func_trace = ''
			
		global screen_count
		global crop_debug_count
		screen_count_local = screen_count
		crop_debug_count_local = crop_debug_count
		log_text = "%(screen_count_local)d_%(crop_debug_count_local)d%(func_trace)s: %(text)s"%vars()
		log_file.write(log_text + '\n')



		
def get_box_size(box, double=False):
	if double:
		size = ((box[2] - box[0]), (box[3] - box[1]))
	else:
		size = (box[2] - box[0]) * (box[3] - box[1])
	return size


def get_skill_by_mission_altitude(mission, altitude, train_torpedoes):
	#if we have M or T for mission/training
	if mission[0] in ["M", "T"]:
		mission = mission[1:]
	skill = MissionSkillMapping[mission]
	if altitude == 100:
		return 'Staf'
	elif (type(skill) == list):
		#special torpedo check
		if mission == "NavalAttack":
			if train_torpedoes:
				return "NavT"
				
		if altitude < 2000:
			return skill[0]
		else:
			return skill[1]
	else:
		return skill
		
def check_in_set(pilot, pilot_list):
	for i_pilot in pilot_list:
		if i_pilot.check_if_duplicate(pilot):
			return True
	return False


class AirGroup(object):
	def __init__(self, group_num):
		self.group_num = group_num
		self.need_more_pilots = True
	
	def get_training_skill(self):
		return get_skill_by_mission_altitude(self.mission, self.altitude, self.train_torpedoes)

	def get_pilots_needed(self):
		total_planes = self.num_ready_aircraft + self.num_grounded_aircraft
		return  total_planes - self.num_pilots_ready
	
	def set_pilot_list(self, pilot_list):
		self.pilot_list = pilot_list
	
	def __str__(self):
		return str(self.group_num)
		
	def mark_as_done(self):
		self.need_more_pilots = False
		
class Pilot(object):
	def __init__(self):
		self.skill_dict = {}
		
	
	def add_skill(self, skill, value):
		self.skill_dict[skill] = value
		
	def __str__(self):
		text = ''
		for skill in CommonPilotSkills:
			if text:
				text += "_"
			value = self.skill_dict[skill]
			text += str(value)
		return text
	
	def __repr__(self):
		return self.skill_dict

	def check_if_duplicate(self, other_pilot):
		for skill in CommonPilotSkills:
			value = self.skill_dict[skill]
			other_value = other_pilot.skill_dict[skill]
			if other_value != value:
				return False
		return True
		


class PilotClass(object):
	def __init__(self, final_skills, basic_skills={}):
		self.basic_skills = basic_skills
		self.final_skills = final_skills
	
	def is_pilot_type(self, pilot):
		for skill_name, skill_value in self.basic_skills.iteritems():
			if pilot.skill_dict[skill_name] < skill_value:
				return False
		return True
		# #check the higher end now
		# for skill_name, skill_value in self.final_skills.iteritems():
			# if pilot.skill_dict[skill_name] < skill_value:
				# return True
		# #if we get here then its fully trained
		# return False
			
		
	def should_train_skill(self, pilot, skill):
		if not skill in self.final_skills:
			return False
		if pilot.skill_dict[skill]  < self.final_skills[skill]:
			return True
		else:
			return False

	def get_relevant_skils(self):
		return self.final_skills.keys()

			
			
class PilotPoolGroup(object):
	def __init__(self, nation, pool_source):
		self.nation = nation
		self.pool_source = pool_source
		self.pilot_classes = []
		self.air_group_dict = {}
		self.air_group_list = []
		global PilotPoolGroupDict
		if not pool_source in PilotPoolGroupDict:
			PilotPoolGroupDict[pool_source] = {}
		PilotPoolGroupDict[pool_source][nation] = self
		
		self.plane_type_list = []
		for pool_source, plane_type in PoolMapping.iteritems():
			if pool_source == self.pool_source:
				self.plane_type_list.append(plane_type)


	def set_veteran_pool_list(self, pilot_list):
		self.veteran_pilot_list = pilot_list

	def remove_pilots_from_pool(self, number, skill, ascending):
		self.veteran_pilot_list.sort(key = lambda x: x.skill_dict[skill], reverse=ascending)
		for i in range(number):
			pilot = self.veteran_pilot_list.pop(i)
		
		
	
	def add_pilot_class(self, pilot_class):
		self.pilot_classes.append(pilot_class)
	
	def check_continue_training(self, pilot, skill):
		#see if it meets any 
		is_specialized = False
		for pilot_class in self.pilot_classes:
			if pilot_class.is_pilot_type(pilot):
				if pilot_class.should_train_skill(pilot, skill):
					return True
				else:
					is_specialized = True
		if is_specialized:
			return False
		else:
			return True
			
	def get_relevant_skils(self):
		skill_list = []
		for pilot_class in self.pilot_classes:
			for skill in pilot_class.get_relevant_skils():
				if skill not in skill_list:
					skill_list.append(skill)
		return skill_list
		
	
	def get_exclusive_skills(self, skill):
		filtered_class_list = []
		for pilot_class in self.pilot_classes:
			if not pilot_class.is_relevant_skill(skill):
				filtered_class_list.append(pilot_class)
				
		exclusive_list = []
		for pilot_class in filtered_class_list:
			for found_skill in pilot_class.get_relevant_skils():
				if found_skill not in exclusive_list:
					exclusive_list.append(found_skill)
		return exclusive_list
	
	
	def get_plane_type(self):
		#FIX
		return self.plane_type_list[0]


	def add_sorted_skill_list(self, skill, pilot_list, ascending):
		if not 'pilot_skill_dict' in vars(self).keys():
			self.pilot_skill_dict = {}
		self.pilot_skill_dict[self] = (None,None)
		if ascending:
			self.pilot_skill_dict[self][0] = pilot_list
		else:
			self.pilot_skill_dict[self][1] = pilot_list
	
	
	
	def get_retention_ratio(self, training_skill, skill2sort, pilots_needed, reverse=False):
		self.veteran_pilot_list.sort(key = lambda x: x.skill_dict[skill2sort], reverse=reverse)
		
		matching_pilots = 0
		for pilot_obj in self.veteran_pilot_list[:pilots_needed]:
			pilot_string = self.show_relevant_pilot_skills(pilot_obj)
			if self.check_continue_training(pilot_obj, training_skill):
				matching_pilots += 1
				log_message("Can add pilot %(pilot_string)s training skill %(training_skill)s"%vars(), 7)
			else:
				log_message("Don't add pilot %(pilot_string)s training skill %(training_skill)s"%vars(), 7)
				
		
		return matching_pilots * 1.0 / pilots_needed
	
	def show_relevant_pilot_skills(self, pilot_obj):
		skill_list = self.get_relevant_skils()
		text = ''
		for skill in skill_list:
			if text:
				text += ", "
			text += skill + ": " + str(pilot_obj.skill_dict[skill])
		return text
		
	
	def get_best_veteran_retention_group(self):
		best_ratio = 0.0
		best_air_group = None
		best_skill2sort = None
		for air_group in self.air_group_dict.values():
			#skip the ones that are done
			if not air_group.need_more_pilots:
				continue
			pilots_needed = air_group.get_pilots_needed()
			log_message("get_best_veteran_retention_group: Air group %(air_group)s needs %(pilots_needed)d pilots"%vars(), 4)
			if pilots_needed > 0:
				training_skill = air_group.get_training_skill()
				for skill2sort in CommonPilotSkills:
					retention_ratio = self.get_retention_ratio(training_skill, skill2sort, pilots_needed)
					log_message("get_best_veteran_retention_group: Air group %(air_group)s training %(training_skill)s sorting by %(skill2sort)s get a retention ratio of %(retention_ratio)s"%vars(), 5)
					if retention_ratio > best_ratio:
						best_air_group = air_group
						best_ratio = retention_ratio
						best_skill2sort = skill2sort
		if best_air_group:
			log_message("get_best_veteran_retention_group: Group %(best_air_group)s has best ratio %(best_ratio)s sorted by %(skill2sort)s"%vars(), 3)
		else:
			log_message("get_best_veteran_retention_group: No additional pilots needed", 3)
		return best_air_group
	
	
	def get_greatest_pilot_need_group(self):
		max_spots_open = 0
		best_air_group = None
		for air_group in self.air_group_dict.values():
			#skip the ones that are done
			if not air_group.need_more_pilots:
				continue
			pilots_needed = air_group.get_pilots_needed()
			if pilots_needed > max_spots_open:
				max_spots_open = pilots_needed
				best_air_group = air_group
		return best_air_group
	
	
	def get_next_air_group(self):
		best_air_group = self.get_best_veteran_retention_group()
		if best_air_group:
			return best_air_group
		else:
			best_air_group = self.get_greatest_pilot_need_group()
			return best_air_group
	
	
	def get_demand_by_training_skill(self):
		demand_by_skill_dict = {}
		for air_group in self.air_group_dict.values():
			training_skill = air_group.get_training_skill()
			if not training_skill in demand_by_skill_dict:
				demand_by_skill_dict[training_skill] = []
			demand_by_skill_dict[training_skill] += air_group.get_pilots_needed()
		return demand_by_skill_dict

	def get_skill_to_sort(self):
		air_group = self.current_air_group
		pilots_needed = air_group.get_pilots_needed()
		training_skill = air_group.get_training_skill()
		best_ratio = -1.0
		latched_skill = None
		for skill2sort in CommonPilotSkills:
			retention_ratio = self.get_retention_ratio(training_skill, skill2sort, pilots_needed)
			if retention_ratio > best_ratio:
				best_ratio = retention_ratio
				latched_skill = skill2sort
		return latched_skill
	
	def get_best_release_tuple(self):
		best_value = -1
		latched_acsending = False
		latched_pilots2drop = 0
		latched_skill2sort = None
		for ascending in [False, True]:
			for skill2sort in CommonPilotSkills:
				release_value, pilots2drop = self.get_group_release_tuple(skill2sort, ascending)
				if release_value > best_value:
					latched_pilots2drop = pilots2drop
					latched_acsending = ascending
					best_value = release_value
					latched_skill2sort = skill2sort
		return latched_skill2sort, latched_pilots2drop, latched_acsending
	
	
	def get_group_release_tuple(self, skill2sort, ascending):
		air_group = self.current_air_group
		training_skill = air_group.get_training_skill()
		air_group.pilot_list.sort(key = lambda x: x.skill_dict[skill2sort], reverse=ascending)
		
		
		#a hit is if we would release a pilot we should
		#a miss is releasing a pilot we should not
		pilot_hits = 0
		pilot_misses = 0
		
		value_list = []
		for pilot_obj in air_group.pilot_list:
			#want to release pilots so logic is reverssed
			if self.check_continue_training(pilot_obj, training_skill):
				pilot_misses += 1
			else:
				pilot_hits += 1
			value = pilot_hits - pilot_misses
			pilot_obj.append(value)
		
		#get max index
		best_value = 0
		pilots2release = 0
		for i, value in enumerate(value_list):
			if value > best_value:
				best_value = value
				#index 0 is one pilot released
				pilots2release = i + 1
		return best_value, pilots2release
			
		
		
	
	def get_training_skill(self):
		return self.current_air_group.get_training_skill()
		

	def add_new_group(self, air_group, group_num):
		if group_num in self.air_group_dict:
			raise Exception
		self.air_group_dict[group_num] = air_group
		self.air_group_list.append(air_group)
	
	def set_group_from_num(self, group_num):
		self.current_air_group = self.air_group_dict[group_num]
		

	def check_repeat(self, group_num):
		if group_num in self.air_group_dict:
			return True
		else:
			return False

			
#############pilot groups#####################
PilotPoolGroupDict = {}




####Bomber classes
USN_torpedo_bomber = PilotClass(
{'NavT' : 70, 'NavB': 60, 'ASW': 55, 'GrdB': 50, 'Defn':60},
{'NavT' : 45}
)

torpedo_bomber = PilotClass(
{'NavT' : 70, 'NavB': 60, 'Defn':60},
{'NavT' : 45}
)

dive_bomber = PilotClass(
{'NavB' : 70, 'NavS': 60, 'GrdB': 55, 'Defn':60},
{'NavB' : 45}
)

level_bomber = PilotClass(
{'GrdB': 70, 'Defn': 65}
)


low_level_nav_bomber = PilotClass(
{'LowN':65, 'GrdB':60, 'Defn':60},
{'LowN':45}
)


mid_level_nav_bomber = PilotClass(
{'NavB':65, 'GrdB':65, 'Defn':60}, 
{'NavB':45}
)



#######Fighter classes
fighter_pilot = PilotClass(
{'Air' : 70, 'Defn': 65}
)




#######Other
transport_pilot = PilotClass(
{'Tran' : 70, 'Defn' : 55}
)

recon_pilot = PilotClass(
{'Recon' : 70, 'Defn': 55}
)

patrol_pilot = PilotClass(
{'NavS' : 70}
)

USN_patrol_pilot = PilotClass(
{'NavS' : 70, 'NavT': 50}
)


#defaults
default_bomber = PilotPoolGroup('', 'Bomber')
default_bomber.add_pilot_class(level_bomber)

default_fighter = PilotPoolGroup('', 'Fighter')
default_fighter.add_pilot_class(fighter_pilot)

default_transport = PilotPoolGroup('', 'Transport')
default_transport.add_pilot_class(transport_pilot)

default_recon = PilotPoolGroup('', 'Recon')
default_recon.add_pilot_class(recon_pilot)

default_patrol = PilotPoolGroup('', 'Patrol')
default_patrol.add_pilot_class(patrol_pilot)


#overrides
USN_bombers = PilotPoolGroup('USN', 'Bomber')
USMC_bombers = PilotPoolGroup('USMC', 'Bomber')

USN_bombers.add_pilot_class(level_bomber)
for bomber_group in [USN_bombers, USMC_bombers]:
	bomber_group.add_pilot_class(dive_bomber)
	bomber_group.add_pilot_class(USN_torpedo_bomber)


USA_bombers = PilotPoolGroup('USA', 'Bomber')
USA_bombers.add_pilot_class(level_bomber)
USA_bombers.add_pilot_class(low_level_nav_bomber)
USA_bombers.add_pilot_class(mid_level_nav_bomber)


USN_patrols = PilotPoolGroup('USN', 'Patrol')
USN_patrols.add_pilot_class(USN_patrol_pilot)


################################################


class PilotManager(object):
	def __init__(self, time_fact=1, message_level_input=-1):
		self.path = r"C:\\Users\\steph_000\\Dropbox\\Scripts\\"
		app = Application()
		app.connect_(path = "C:\Users\steph_000\Documents\Games\War in the Pacific Admiral's Edition\War in the Pacific Admiral Edition.exe")
		self.dlg = app['War in the Pacific - Admiral Edition (1.7.11.23x6a)']
		rect = self.dlg.Rectangle()

		
		hwin = win32gui.GetDesktopWindow()
		hwindc = win32gui.GetWindowDC(hwin)
		self.srcdc = win32ui.CreateDCFromHandle(hwindc)
		self.memdc = self.srcdc.CreateCompatibleDC()
		self.screen_width = 3200
		self.screen_height = 1800
		
		self.ideal_box = (0, 0, 1042, 815)
		
		self.double = True
		self.screen_box = (rect.left, rect.top, rect.right, rect.bottom)
		self.train_all()
		self.nation_dict = {}
		self.current_screen_state = ''
		
		self.need_refresh = 1
		self.need_debig_refresh = 1
		
		self.left_offset = -18
		self.top_offset = -30
		
		self.left_offset_click = 0
		self.top_offset_click = -10
		
		self.time_fact = time_fact
		
		#globals
		global message_level
		global sample_path
		global screen_count
		global crop_debug_count
		message_level = message_level_input
		sample_path = "test_images"
		screen_count = 0
		crop_debug_count = 0
		
		self.refocus()
		self.sleep(0.2)
		self.group_image_list = []
		self.group_name_knn = cv2.KNearest()
		
		self.set_log_file(file='')
		
		self.group_num_list = []
		
		
		for the_file in os.listdir(sample_path):
			file_path = os.path.join(sample_path, the_file)
			try:
				os.unlink(file_path)
			except:
				pass


#########Miscelaneous Functions start############
	def set_log_file(self, file=''):
		global log_file
		log_file = open("pilot.log", 'wb')
		#logging.getLogger(file)

	def sleep(self, time_val):
		time_val = time_val * self.time_fact
		time.sleep(time_val)

#########Miscelaneous Functions End############

		
#########Interface Functions start############
		
		
	def refocus(self):
		self.dlg.Minimize()
		self.dlg.Maximize()
		self.dlg.SetFocus()
		self.need_refresh = 1
		self.need_debug_refresh = 1
		
	def ClickInput(self, coords, right=False):
		x = coords[0] + self.left_offset_click
		y = coords[1] + self.top_offset_click
		if right:
			button = 'right'
		else:
			button = 'left'
		self.dlg.ClickInput(coords=(x, y), button=button)
		self.need_refresh = 1
		self.need_debug_refresh = 1
	
	def PressMouseInput(self, coords):
		x = coords[0] + self.left_offset_click
		y = coords[1] + self.top_offset_click
		self.dlg.PressMouseInput(coords=(x, y))
		self.need_refresh = 1
		self.need_debug_refresh = 1
	
	def ReleaseMouseInput(self, coords):
		x = coords[0] + self.left_offset_click
		y = coords[1] + self.top_offset_click
		self.dlg.ReleaseMouseInput(coords=(x, y))
		self.need_refresh = 1
		self.need_debug_refresh = 1
		
	def TypeKeys(self, key):
		self.dlg.TypeKeys(key)
		self.need_refresh = 1
		self.need_debug_refresh = 1
	
	def click_away(self):
		self.ClickInput(coords=(100,100))
		self.ClickInput(coords=(70,70))
		
		

	def scroll_to_top(self, debug=False):
		left = 856
		top = 283
		right = 870
		bottom = 296
		box = (left, top, right, bottom)
		self.PressMouseInput(coords=(865, 515))
		self.ReleaseMouseInput(coords=(865, 281))
		self.sleep(0.2)
		status = self.check_train(self.scroll_knn, box, debug=debug)
		if status == 1:
			return True
		elif status == 2:
			return True
	
	def scroll_down_tiny(self):
		x = 865
		y = 534
		coords = (x, y)
		self.ClickInput(coords)
		
	
	
	#normalized height is 0 to 1
	def click_to_scroll_pos(self, normalized_height, debug=False):
		min_height = 285
		max_height = 524
		x = 865
		y = int(round(min_height + normalized_height * (max_height - min_height)))
		coords = (x, y)
		self.ClickInput(coords)
		#check a single line
#		while not self.is_pilot_pool_aligned(debug=debug):'
#			coords = (x, max_height + 5)
#			self.ClickInput(coords)
#			self.sleep(0.2)
		return

	def scroll_to_bottom(self):
		self.ClickInput(coords=(865, 522))



#########Interface Functions End############



#########Managing Multiple Groups Start############

		
	def switch_group(self):
		self.ClickInput(coords=NextRight)
		self.sleep(0.5)


	#start: Main Unit Screen
	#action: Sweep through all the air groups of a given type exactly once
	#return: Successs
	def first_sweep(self, debug=False):
		i = 0
		while True:
			group_num = self.get_group_num()
			log_message("first_sweep: Found group num %(group_num)d"%vars(), 1)
			if group_num > 0:
				if self.pilot_pool_group.check_repeat(group_num):
					log_message("first_sweep: Repeat with group %(group_num)d"%vars(), 1)
					return True
				else:
					self.create_air_group(group_num)
					self.release_pilots_by_skill(debug=debug)
					self.switch_group()
					i += 1
			else:
				print "unexpected pilot num"
				return False



	#start: Main Unit Screen
	#action: Sweep through all the groups of a given type
	#return: Successs
	def train_pilots(self, debug=False):
		self.first_sweep(debug=debug)
		
		
		success = False
		#need to find a group we can use to look at the pool with
		for air_group in self.air_group_list:
			#jump to add pilot screen
			if self.check_can_add_reserve_pilots(debug=debug):
				self.ClickInput(coords=RequestVeteran)
				#add reserve pilot
				self.sleep(0.2)
				success = True
				break
			else:
				self.switch_group()
		
		#can't add any pilots i guess
		if not success:
			return
		
		#read the pilot pool
		pilot_list = self.read_pilot_pool(debug=debug)
		self.pilot_pool_group.set_veteran_pool_list(pilot_list)
		
		self.ClickInput(coords=AddPilotScreen_Back)
		self.sleep(0.1)
		
		
		#now the adding sweep
		i = 0
		while True:
			next_group = self.pilot_pool_group.get_next_air_group()
			if next_group:
				next_group_num = next_group.group_num
				self.switch_to_group_num(next_group_num, debug)
				self.add_pilots_by_skill(debug=debug)
				i += 1
			else:
				log_message("train_pilots: No more groups to train on iteration %(i)d"%vars(), 1)
				return
	
	
	
	#start: Main Unit Screen
	#action: Switch to a group specified by group number
	#return: Successs
	def switch_to_group_num(self, next_group_num, debug=False):
		i = 0
		while i < len(self.air_group_list):
			group_num = self.get_group_num()
			if group_num == next_group_num:
				log_message("switch_to_group_num: Found target group %(next_group_num)d"%vars(), 2)
				self.pilot_pool_group.set_group_from_num(group_num)
				return
			else:
				log_message("switch_to_group_num: Looking %(next_group_num)d and found %(group_num)s at iteration %(i)d"%vars(), 3)
				self.switch_group()
			i += 1
		raise Exception


		
		
	'''
	def get_group_name(self):
		left = 176
		top = 235
		right = 273
		bottom = 244
		box = (left, top, right, bottom)
	'''



#########Managing Multiple Groups End############





#########Managing Single Air Group Start#############

	#Start: Main pilot screen
	#End: Main pilot screen
	def release_unqualified_pilots(self, debug=False):
		self.save_main_screen_info(debug=debug)
	
		self.ClickInput(coords=PilotsButtonCoord)
		self.sleep(0.2)
		
		while True:
			pilot_list = self.read_pilot_pool(release=True, debug=debug)
			self.current_air_group.set_pilot_list(pilot_list)
			skill2sort, pilots2drop, ascending = self.pilot_pool_group.get_best_release_tuple()
			self.release_n_pilots(skill2sort, pilots2drop, ascending, debug=debug)


	#Start: Main pilot screen
	#End: Main pilot screen
	def release_n_pilots(self, skill2sort, pilots2drop, ascending, debug=False):
		
		self.save_main_screen_info(debug=debug)
	
		self.ClickInput(coords=PilotsButtonCoord)
		self.sleep(0.2)
		
			
		self.sort_skill(skill2train, ascending=ascending, release=True, debug=debug)
		
		#iterate through the skill in descending order
		#when we find the first pilot that should continue training we stop and move on
		
		
		log_message("release_n_pilots: Releasing pilots sorted by %(skill2sort)s"%vars(), 3)
		
		pilots_left2release = pilots2drop
		pilots_released = 0
		max_pilots2release = 10
		success = True
		while success:
			success = False
			for i in [10, 5, 1]:
				if i <= max_pilots2release and i <= pilots_left2release:
					if self.Release_Pilot_To_Pool("Reserve"):
						pass
					else:
						log_message("release_n_pilots: Can't set pool to reserve", 2)
						break
						
					
				if self.press_release(least=ascending, num = i):
					self.scroll_to_top()
					max_pilots2_release = i
					pilots_left2release += -1 * i
					pilots_released += i
					success = True
					break
		log_message("release_n_pilots: Released up to %(pilots_released)d pilots"%vars(), 3)	
		
		

	#Start: Main pilot screen
	#Action: Go to release pilot screen
	#		Release pilots at or above a certain skill level
	#End: Main pilot screen
	def release_pilots_by_skill(self, skill2sort=None, ascending=False, debug=False):
	
		self.save_main_screen_info(debug=debug)
	
		self.ClickInput(coords=PilotsButtonCoord)
		self.sleep(0.2)
		
		skill2train = self.pilot_pool_group.get_training_skill()
		#by default use the skill we are triaining
		if not skill2sort:
			skill2sort = skill2train
		
			
		self.sort_skill(skill2train, ascending=ascending, release=True, debug=debug)
		
		#iterate through the skill in descending order
		#when we find the first pilot that should continue training we stop and move on
		
		
		log_message("release_pilots_by_skill: Releasing pilots training %(skill2train)s sorted by %(skill2sort)s"%vars(), 2)
		should_release_pilots = False
		
		max_pilots2release = 10
		num_pilots2skip = 0
		while True:
			success = False
			for i in [10, 5, 1]:
				if i <= max_pilots2release:
					last_in_line = i - 1 + num_pilots2skip
					
					pilot_obj = self.create_pilot_object(last_in_line, release=True, debug=debug)
					if pilot_obj:
						if not self.pilot_pool_group.check_continue_training(pilot_obj, skill2train):
						
							#now check how many pilots would actually be released
							pilots2release, new_pilots2skip = self.set_pilots2release(skill2train, num_pilots2skip, i, debug=debug)
							#we can release this many
							if pilots2release >= i:
								release_num = i
							elif pilots2release >= 5:
								release_num = 5
							elif pilots2release >= 1:
								release_num = 1
							else:
								break
								
							if not should_release_pilots:
								if self.Release_Pilot_To_Pool("Reserve"):
									should_release_pilots = True
								else:
									log_message("release_pilots_by_skill: Can't set pool to reserve", 2)
									break
									
								
							if self.press_release(least=ascending, num = release_num):
								log_message("release_pilots_by_skill: Released %(release_num)d pilots"%vars(), 3)
								self.scroll_to_top()
								max_pilots2_release = i
								num_pilots2skip += new_pilots2skip
								success = True
								break
		
			if not success:
				break
		log_message("release_pilots_by_skill: Done releasing pilots"%vars(), 2)
		self.ClickInput(coords=Done)
		self.sleep(0.2)
		self.save_main_screen_info(debug=debug)
		return success


	#Start: Main pilot screen
	#Action: Set pool to pick reserve pilots
	#Click "request verteran
	#Add as many pilots as possible
	#End: Main pilot screen
	def overload_reserve_pilots(self, debug=False):
		
		self.save_main_screen_info(debug=debug)
	
		#add set the draw pool
		self.set_pool_draw('Reserve')
		#jump to add pilot screen
		self.ClickInput(coords=RequestVeteran)
		#add reserve pilot
		self.sleep(0.2)
		
		
		self.handle_bar('pilot_pool_source_bar')
		
		if self.set_pool_draw('Reserve', main_screen=False):
			skill2sort = self.pilot_pool_group.get_skill_to_sort()
			skill2train = self.pilot_pool_group.get_training_skill()
			
			self.sort_skill(skill2sort, ascending=True, release=False, debug=debug)
			
			pilots_added = 0
			round_num = 0
			added_any = True
			
			while added_any:
				added_any = False
				for k in [10, 5, 1]:
					if self.press_release(least=True, num = k):
						added_any = True
						pilots_added += k
				round_num += 1
				
			if pilots_added > 0:
				log_message("overload_reserve_pilots: Added %(pilots_added)s pilots"%vars(), 2)
				self.pilot_pool_group.remove_pilots_from_pool(pilots_added, skill2sort, ascending=True)
	
		self.ClickInput(coords=AddPilotScreen_Back)
		self.sleep(0.1)
		self.save_main_screen_info(debug=debug)
		
	#Start: Main pilot screen
	#Action: Set pool to pick reserve pilots
	#Click "request verteran
	#Add pilots below a certain skill level	
	#Return: number of pilots we need to add
	#End: Main pilot screen
	def add_qualified_reserve_pilots(self, pilots2add, debug=False, level=10):
		
		self.save_main_screen_info(debug=debug)
		
		pilot_num = 0
		pilots_added = 0
		success = False
		round_num = 0
		#see if we can even click the request veteran button
		if not self.check_can_add_reserve_pilots(debug=debug):
			return pilots2add, pilots_added
	
		#add set the draw pool
		self.set_pool_draw('Reserve')
		#jump to add pilot screen
		self.ClickInput(coords=RequestVeteran)
		#add reserve pilot
		self.sleep(0.2)
		
		
		self.handle_bar('pilot_pool_source_bar')
		
		if self.set_pool_draw('Reserve', main_screen=False):
			skill2sort = self.pilot_pool_group.get_skill_to_sort()
			skill2train = self.pilot_pool_group.get_training_skill()
			log_message("add_qualified_reserve_pilots: Sorting skill %(skill2sort)s for adding pilots"%vars(), 3)
			
			self.sort_skill(skill2sort, ascending=True, release=False, debug=debug)
			while pilots_added < pilots2add:
				success = False
				skip2release = False
				log_message("add_qualified_reserve_pilots: On iteration %(round_num)d we have added %(pilots_added)d out of %(pilots2add)d"%vars(), 3)
				for k in [10, 5, 1]:
					next_pilot_num = pilot_num + k
					#can't go past 26
					if next_pilot_num > 26:
						next_pilot_num = 26
					last_in_line = next_pilot_num - 1
					release = False
					if skip2release:
						release = True
					else:
						pilot_obj = self.create_pilot_object(last_in_line, release=False, debug=debug, level=level)
						if pilot_obj:
							if self.pilot_pool_group.check_continue_training(pilot_obj, skill2train):
								release = True
					
					if release:
						if self.press_release(least=True, num = k):
							success = True
							pilot_num = next_pilot_num
							pilots_added += k
							break
						#if we can't release but we meet the right value we can release without checking next time
						else:
							skip2release = True
				if not success:
					break
				round_num += 1
			#get some totals
			num_pilots_left = pilots2add - pilots_added
			self.pilot_pool_group.remove_pilots_from_pool(pilots_added, skill2sort, ascending=True)
		else:
			num_pilots_left = pilots2add
		#go back
		self.ClickInput(coords=AddPilotScreen_Back)
		self.sleep(0.1)
		self.save_main_screen_info(debug=debug)
		return num_pilots_left, pilots_added
	
			
	#Start: Main pilot screen
	#Action: Set pool to pick reserve pilots
	#		 Click "request verteran
	#		Add pilots below a certain skill level	
	#Return: number of pilots we need to add
	#End: Main pilot screen	
	def add_reserve_pilots_old(self, pilots2add, debug=False):
	
		#add set the draw pool
		self.set_pool_draw('Reserve')
		#jump to add pilot screen
		self.ClickInput(coords=RequestVeteran)
		#add reserve pilot
		self.sleep(0.2)
		
		skill = self.pilot_group.get_skill2train()
		column_index = SkillIndexMapping[skill]
		target_val = self.pilot_group.get_target_val()
		log_message('add_reserve_pilots: Adding pilots with %(skill)s worse than %(target_val)d'%vars(), 1)
		self.handle_bar('pilot_pool_source_bar')
		pilot_num = 0
		pilots_added = 0
		success = False
		round_num = 0
		if self.set_pool_draw ('Reserve', main_screen=False):
			self.sort_cat(column_index, ascending=True, release=False, debug=debug)
			while pilots_added < pilots2add:
				success = False
				skip2release = False
				log_message("add_reserve_pilots: On iteration %(round_num)d we have added %(pilots_added)d out of %(pilots2add)d"%vars(), 2)
				for k in [10, 5, 1]:
					next_pilot_num = pilot_num + k
					#can't go past 26
					if next_pilot_num > 26:
						next_pilot_num = 26
					last_in_line = next_pilot_num - 1
					release = False
					if skip2release:
						release = True
					else:
						value = self.get_pilot_val(column_index, last_in_line, release=False, debug=True)
						log_message('add_reserve_pilots: Pilot in column %(column_index)d position of %(last_in_line)d has %(value)d skill for %(skill)s'%vars(), 2)
						if value  < target_val:
							release = True
					
					if release:
						if self.press_release(least=True, num = k):
							success = True
							pilot_num = next_pilot_num
							pilots_added += k
							break
						#if we can't release but we meet the right value we can release without checking next time
						else:
							skip2release = True
				if not success:
					break
				round_num += 1
		#go back
		self.ClickInput(coords=AddPilotScreen_Back)
		self.sleep(0.1)
		num_pilots_left = pilots2add - pilots_added
		return num_pilots_left
			
		

	def release_group(self):
		if self.Release_Pilot_To_Pool("Reserve"):
			self.scroll_to_top()
			self.sleep(0.3)
			for i in range(20):
				if self.check_set_retain():
					if self.press_release(num = 10):
						pass
					elif self.press_release(num = 5):
						pass
					elif self.press_release(num = 1):
						pass
					else:
						return True
				else:
					return True
		return False
		
	#start: Main Pilot Screen
	#action: See how many pilots we have in reserve
	#		Click to the release pilot screen
	#		Set "To pool" to active
	#		Release pilots based off how many reserves we had
	#		Call the manual set to active to fix any remaining ones
	#return: If success he number of pilots that cannot be dropped 
	#		 Else -1
	def set_pilots2active(self, debug=False):
		pilots_ready, pilots_in_resrerve = self.get_num_ready_pilots(debug=debug)
		#go to the release pilot screen
		self.ClickInput(coords=PilotsButtonCoord)
		self.sleep(0.2)
		pilots_released = 0
		if self.Release_Pilot_To_Pool("Active"):
			self.sleep(0.2)
			while pilots_released < pilots_in_resrerve:
				if self.press_release(num = 10):
					pilots_released += 10
				elif self.press_release(num = 5):
					pilots_released += 5
				elif self.press_release(num = 1):
					pilots_released += 1
				else:
					return
				self.sleep(0.4)
				log_message("set_pilots2active: Released %(pilots_released)d to active so far"%vars(), 4)
			self.set_pilots2active_manual(debug=debug)
	
	#start:  Release pilot screen OR Main Pilot Screen
	#action: Click to the release pilot screen
	#		Sort the delay col
	#		 Release pilots until the top pilot is not there or has delay
	#		Go back to main pilot screen
	#return: If success he number of pilots that cannot be dropped 
	#		 Else -1
	def set_pilots2active_manual(self, main_pilot_screen=False, max_pilot_pos=26, debug=False):
	
		if main_pilot_screen:
			#go to the release pilot screen
			self.ClickInput(coords=PilotsButtonCoord)
			self.sleep(0.2)
	
		#sort
		success = False
		delay_col = SkillIndexMapping['Delay']
		if	self.sort_cat(delay_col, ascending=False):
			#see how many we need to skip over
			pilotnum2set = 0
			can_set2active = False
			for pilot_num in range(max_pilot_pos+1):
				#check the pilot values
				delay_val = self.get_pilot_val(delay_col, pilot_num)
				if delay_val > 1:
					pilotnum2set += 1
				#ok we can set at least one to active now
				elif delay_val == 1:
					can_set2active = True
					log_message("set_pilots2active_manual: Setting pilots at position %(pilotnum2set)d to active"%vars(), 3)
					break
				#no need to do anything more
				else:
					success = True
					break
			#set the remaining pilots to active
			pilots_set = 0
			first = True
			while not success:
				#no need to check delay val on the first since we did above
				if first:
					first = False
				else:
					delay_val = self.get_pilot_val(delay_col, pilotnum2set)
					if delay_val < 1:
						log_message("set_pilots2active_manual: Set %(pilots_set)d pilots"%vars(), 3)
						success = True
						break
						
				coords = pilot_names[pilotnum2set]
				self.ClickInput(coords=coords, right=True)
				self.sleep(0.1)
				self.TypeKeys("y")
				self.sleep(0.1)
				pilots_set +=  1
				self.scroll_to_top()
		else:
			log_message("set_pilots2active_manual: Couldn't sort the delay column")
			success = False
		
		#go back
		self.ClickInput(coords=Done)
		self.sleep(0.2)
		return success
	
	
		
	
	#start: Release Pilot Screen
	#return the number of pilots that can be released under a certain criteria and how many have been skipped
	def set_pilots2release(self, skill2train, offset, target2release, debug=False):
		num2skip = 0
		pilots_checked = 0
		while pilots_checked < target2release + num2skip and pilots_checked < 26:
			pilot2check = offset + pilots_checked
			#assume for now that pilots up to the target have been checked
			if pilots_checked >= target2release:
			
				pilot_obj = self.create_pilot_object(pilot2check, release=True, debug=debug)
				if pilot_obj:
					#are we actually worried about a skill 
					if skill2train:
						#can release everything up to but NOT including this pilot
						if self.pilot_pool_group.check_continue_training(pilot_obj, skill2train):
							num2release = pilots_checked - num2skip - 1
							log_message("set_pilots2release: Pilot detected at position %(pilot2check)d should be retained."%vars(), 4)
							log_message("set_pilots2release: OK to release %(num2release)d with %(num2skip)d to skip"%vars(), 4)
							return num2release, num2skip
				
				#no pilot on this position so can release everything
				else:
					log_message("set_pilots2release: No pilot detected at position %(pilot2check)s, OK to release %(target2release)d"%vars(), 4)
					return target2release, num2skip
			status = self.set_one_retain(pilot2check, release=True, debug=debug)
			if status == 1:
				num2skip += 1
			elif status == 0:
				pass
			else:
				#no pilot on this position so can release everything
				log_message("set_pilots2release: No pilot detected at position %(pilot2check)s, OK to release %(target2release)d"%vars(), 4)
				return target2release, num2skip
			pilots_checked += 1
		num2release = pilots_checked - num2skip
		log_message("set_pilots2release: OK to release %(target2release)d with %(num2skip)d to skip"%vars(), 4)
		return pilots_checked - num2skip, num2skip


#########Managing Single Air Group En#############



##########Pilot Pool Fuction Start#################


	
	def read_pilot_info(self, y_offset=0, release=False, num_pilots=26, debug=False, level=10):
		pilot_list = []
		for i in range(num_pilots):
			pilot_obj = self.create_pilot_object(i, y_offset=y_offset, release=release, debug=debug, level=level)
			if not pilot_obj:
				return pilot_list
			pilot_list.append(pilot_obj)
		return pilot_list
	
	
	#Start: Either pilot screen
	#Return: A list of pilot objects
	def read_pilot_pool(self, release=False, debug=False, level=10):
		
		
		#FIXME
		if release:
			raise Exception
		else:
			log_message("read_pilot_pool: Reading from pool %s"%(self.pool_source), 4, level)
			offset = 0
			ordered_pool_list = ["Fighter", "Bomber", "Patrol", "Transport", "Recon"]
			
			for pool_source in ordered_pool_list:
		
				#get the number of pilots in the pool
				y = 255
				if pool_source == "Fighter":
					x = 303 + offset
				elif pool_source == "Bomber":
					x = 360 + offset
				elif pool_source == "Patrol":
					x = 416 + offset
				elif pool_source == "Transport":
					x = 483 + offset
				elif pool_source == "Recon":
					x = 534 + offset
				else:
					raise Exception
				
				coords = (x, y)
				pilots_in_pool_group = self.get_num(coords, size=4, debug=debug, level=level)
				log_message("read_pilot_pool: Found %(pilots_in_pool_group)d in group of source %(pool_source)s"%vars(), 5, level)
				
				#increasing offset
				if pilots_in_pool_group >= 100:
					offset += 5
				
				if self.pool_source == pool_source:
					log_message("read_pilot_pool: Found %(pilots_in_pool_group)d in main group of source %(pool_source)s"%vars(), 4, level)
					break
				
			self.handle_bar('pilot_pool_source_bar')
		self.scroll_to_top()
		if pilots_in_pool_group > 26:
		
			scroll_increment =  26.0 / pilots_in_pool_group  * 0.75
			
			pilot_list = []
			scroll_value = 0
			
			while scroll_value < 1:
				self.click_to_scroll_pos(scroll_value, debug=debug)
				self.sleep(0.2)
				
				y_offset = self.get_pilot_y_offset(debug=debug, level=level)
				new_pilots = self.read_pilot_info(release=release, y_offset=y_offset, debug=debug, level=level)
				unique_pilots = []
				for pilot in new_pilots:
					if check_in_set(pilot, pilot_list):
						log_message("read_pilot_pool: Found duplicate pilot %(pilot)s"%vars(), 5, level)
					else:
						log_message("read_pilot_pool: Found new pilot %(pilot)s"%vars(), 5, level)
						pilot_list.append(pilot)
						unique_pilots.append(pilot)
				scroll_value += scroll_increment
		else:
			pilot_list = self.read_pilot_info(release=release, debug=debug, level=level)
		log_message("read_pilot_pool: found %d pilots"%(len(pilot_list)), 4)
		return pilot_list



	
	def is_pilot_pool_aligned(self, release=True, debug=False):
		for i in range(18):
			val = self.get_pilot_val(i, 0, release=release, debug=debug)
			if val < 0:
				return False
		return True
		

##########Pilot Pool Fuction End#################






########Individual Pilot Function Start################


	def get_pilot_val(self, col, row, y_offset=0, release=True, debug=False, level=10):
		if release:
			x = pilot_cats_release[col]
		else:
			x = pilot_cats_add[col]
		y = pilot_heights[row] + y_offset
		coords = (x, y)
		log_message("get_pilot_val: getting pilot value for row %(row)d col %(col)d" %vars(), 6)
		num = self.get_num(coords, debug=debug, level=level)
		return num


	def get_num(self, coords, size=3, debug=False, level=10):
		top = coords[1] - 6
		bottom = top + 10
		far_left = coords[0] - 5
		num = 0
		valid = False
		for i in range(size):
			left = far_left + i * 5
			right = left + 5
			box = (left, top, right, bottom)
			result = self.check_train(self.digit_knn, box, debug=debug, level=level)
			log_message("\t\t\t\tget_num: Found digit %(result)d at position %(i)d"%vars(), 7)
			#3 per digit
			if result < 30:
				digit = result % 10
				num = num * 10 + digit
				valid = True
		if valid:
			log_message("get_num: detected number %(num)d"%vars(), 6)
			return num
		else:
			return -1




	def create_pilot_object(self, pilot_position, y_offset=0, release=True, debug=True, level=10):
		
		pilot_obj = Pilot()
		if release:
			relevant_skills = ReleasePilotSkills
		else:
			relevant_skills = AddPilotSkills
		for skill in relevant_skills:
			col = SkillIndexMapping[skill]
			row = pilot_position
			num = self.get_pilot_val(col, row, y_offset=y_offset, release=release, debug=debug, level=level)
			#only happens when we don't have a pilot there
			if num < 0:
				log_message("create_pilot_object:Could not create pilot at position %(pilot_position)d"%vars(), 5, level)
				return None
			pilot_obj.add_skill(skill, num)
		log_message("create_pilot_object: At position %(pilot_position)d created pilot %(pilot_obj)s"%vars(), 6, level)
		return pilot_obj



	def press_release(self, least=True, num=10):
		if num == 10:
			x = Release10
		elif num == 5:
			x = Release5
		elif num == 1:
			x = Release1
		else:
			raise Exception
		if least:
			y = Least
			adj = "least"
		else:
			y = Most
			adj = "most"
		left = x - 9
		right = x + 3
		top = y - 5
		bottom = y + 7
		box = (left, top, right, bottom)
		status = self.check_train(self.release_knn, box, debug=True)
		if status:
			verb = "Can"
		else:
			verb = "Unable to"
		log_message("press_release: %(verb)s release %(num)d %(adj)s pilots"%vars(), 5) 
		if status == 1:
			coords = (x, y)
			self.ClickInput(coords=coords)
			self.sleep(0.2)
			return True
		else:
			return False




########Individual Pilot Function End################

		
	
			
			
			
	#start: Release Pilot Screen
	#action: Check if the to pool text reads the desired destination
	#return: If the button reads desired destination return True
	#		 Else False
	#return False if cannot set because less than 1 pilot
	def Release_Pilot_To_Pool(self, target_dest, debug=False):
	
		#if we fail in 3 then we're fucked
		state = self.get_pool_loc(debug=debug)
		
		if state == 0:
			x = Release10 + 158
			num2release = 10
		elif state == 1:
			x = Release5 + 153
			num2release = 5
		elif state == 2:
			x = Release1 + 143
			num2release = 1
		else:
			num2release = 0
		
		log_message("Release_Pilot_To_Pool:  Can release %(num2release)d pilots at a time"%vars(), 4)
		if num2release == 0:
			return False
		
		coords = (x, Most)
		if x > -1:
			#give it some extra tries
			for i in range(3):
				reserve = self.check_to_pool_text(target_dest, x)
				if reserve:
					return True
				else:
					self.ClickInput(coords=coords)
					self.click_away()
					self.sleep(0.4)
		return False
			


########Reading Images Start#########

	#start: Release Pilot Screen
	#action: Check if the to pool text reads Reserve (status 0) 
	#return: IIf the button reads the target  return True
	#		 Else False
	def check_to_pool_text(self, target_dest, x, debug=False):
		left = x - 14
		top = Most - 5
		right = left + 53
		bottom = top + 15
		box = (left, top, right, bottom)
		status = self.check_train(self.Release_Pilot_To_Pool_Text_knn, box, debug=debug)
		
		#original labels
		train_labels = ["Reserve", "Active", "Group", "pool_null"]
		
		if status == train_labels.index(target_dest):
			return True
		else:
			return False
			

		
		
	def check_train(self, train, box, debug=False, level=10):
		cropped_image = self.get_screen_box(box, debug=debug, level=level)
		cv_image = np.array(cropped_image)
		gray = cv2.cvtColor(cv_image,cv2.COLOR_BGR2GRAY).reshape(1, -1).astype(np.float32)
		ret,result,neighbours,dist = train.find_nearest(gray, k=1)
		return int(result[0][0])
		
	def check_bool_train(self, train, box, tolerence=100, debug=False, level=10):
		grayscale_image = self.get_grayscale_image(box, debug=debug, level=level)
		ret,result,neighbours,dist = train.find_nearest(grayscale_image, k=1)
		size = get_box_size(box)
		error = dist[0][0]/size
		if error <=  tolerence:
			return True
		else:
			return False

	def get_grayscale_image(self, box, debug=False, level=10):
		cropped_image = self.get_screen_box(box, debug=debug, level=level)
		cv_image = np.array(cropped_image)
		grayscale_image = cv2.cvtColor(cv_image,cv2.COLOR_BGR2GRAY).reshape(1, -1).astype(np.float32)
		return grayscale_image









########Reading Images End#########

		
		
		
	#Start: Release pilot screen
	#Action: return the index of what pilots we can release
	def get_pool_loc(self, debug=False):
		y = Most
		x_list = [Release10, Release5, Release1]
		self.sleep(0.3)
		self.ClickInput(coords=(400, 240))
		self.sleep(0.3)
		for i, x in enumerate(x_list):
			left = x - 9
			right = x + 3
			top = y - 5
			bottom = y + 7
			box = (left, top, right, bottom)
			log_message("get_pool_loc: checking location %(i)d"%vars(), 5)
			status = self.check_train(self.release_knn, box, debug=True)
			if status == 1:
				return i
		return -1
			
	def set_pool_nation(self, pool_source, nation, debug=False):
		global PilotPoolGroupDict
		PilotSourceGroupDict = PilotPoolGroupDict[pool_source]
		if nation not in PilotSourceGroupDict:
			self.pilot_pool_group = PilotSourceGroupDict['']
		else:
			self.pilot_pool_group = PilotSourceGroupDict[nation]
		self.nation = nation
		self.pool_source = pool_source
		self.air_group_dict = self.pilot_pool_group.air_group_dict 
		self.air_group_list =  self.pilot_pool_group.air_group_list

	#start at air unit list screen 
	def sweep_pool_nation_group(self, pool_source, nation, debug=False):
		self.set_pool_nation(pool_source, nation, debug=debug)
		plane_type = self.pilot_pool_group.get_plane_type()
		self.set_pool_nation(plane_type, nation, debug=debug)
		self.sleep(0.2)
		#first group
		coords = (207, 304)
		self.ClickInput(coords=coords)
		self.sleep(0.2)
		self.train_pilots(debug=debug)
		
	
	#Start: Main unit screen
	#Action: Add pilots for training 
	#End: Main unit screen
	def overload_pilots_by_skill(self, debug=False):
		
		#we have to do this in multiple rounds 
		#use pilots ready as the marker
		need_replacements = False
		added_pilots = False
		#100 is way more than we need
		for i in range(100):
			#if we can add any pilots lets do it
			if self.check_can_add_reserve_pilots(debug=debug):
				self.overload_reserve_pilots(debug=debug)
				#now release the extras
				
		

	
	#Start: Main unit screen
	#Action: Add pilots for training 
	#End: Main unit screen
	def add_pilots_by_skill(self, debug=False, level=10):
		
		#we have to do this in multiple rounds 
		#use pilots ready as the marker
		need_replacements = False
		added_pilots = False
		#100 is way more than we need
		for i in range(100):
			pilots2add = self.get_num_pilots2add(count_reserve_pilots=True, level=level)
			log_message("add_pilots_by_skill: Need to add %(pilots2add)d pilots on iteration %(i)d"%vars(), 1)
			if pilots2add <= 0:
				break
				
			if not need_replacements:
				
				#next check if we can even add pilots
				if not self.check_can_add_reserve_pilots(debug=debug):
					log_message("add_pilots_by_skill: Cannot click 'Request Veteran' button on iteration %(i)d"%vars(), 1)
					self.mark_group_as_done()
					break
				
				open_spots, num_pilots_added = self.add_qualified_reserve_pilots(pilots2add, debug=debug, level=level)
				added_pilots = True
				if open_spots > 0:
					need_replacements = True
			if need_replacements:
				self.add_replacement_pilots(debug = debug, level=level)
				added_pilots = True
		if added_pilots:
			#after adding pilots set them to be ready
			self.set_pilots2active()
		self.save_main_screen_info()
		return 1

	#Start: Main unit screen
	#Action: Add replacement pilots
	#End: Main unit screen
	def add_replacement_pilots(self, debug=False, level=10):
		#special training groups are different
		special = False
		can_add = False
		if self.check_if_special_training_group():
			special = True
			can_add = True
		#check button for non-special
		elif self.set_pool_draw('Replacement', debug=debug):
			can_add = True
		
		if can_add:
			#sometimes may not reach full total
			for i in range(5):
				#check how many pilots we need
				pilots2add = self.get_num_pilots2add(count_reserve_pilots=True, level=level)
				#break if done
				if pilots2add <= 0:
					return True
				coords = (297, 337)
				pilots2grab = self.get_num(coords, size=2, debug=debug, level=level)
				#for special groups just add the 10
				if special:
					self.ClickInput(coords=GetNPilots)
				else:
					if pilots2add >= pilots2grab:
						self.ClickInput(coords=GetNPilots)
					else:
						self.ClickInput(coords=GetNewPilot)
		else:
			return False
				
			
	
	
	
	#Start: Main unit screen
	#Action: find number of pilots, planes then return true if we need more pilots to fill out unit
	def check_need_more_pilots(self, count_reserve_pilots=True, debug=False, level=10):
		aircraft_ready, aircraft_not_ready = self.get_num_aircraft(debug=debug, level=level)
		total_aircraft = aircraft_ready + aircraft_not_ready
		pilots_ready, pilots_in_resrerve = self.get_num_ready_pilots(debug=debug, level=level)
		log_message("check_need_more_pilots: total aircraft: %(total_aircraft)d, pilots ready: %(pilots_ready)d, pilots in reserve %(pilots_in_resrerve)d"%vars(), 3)
		if count_reserve_pilots:
			pilot_count = pilots_ready + pilots_in_resrerve
		else:
			pilot_count = pilots_ready
		if pilot_count < total_aircraft:
			return True
		else:
			return False

	#Start: Main unit screen
	#Action: find number of pilots, planes then return the number of pilots we need to add
	def get_num_pilots2add(self, count_reserve_pilots=True, debug=False, level=10):
		aircraft_ready, aircraft_not_ready = self.get_num_aircraft(debug=debug, level=level)
		total_aircraft = aircraft_ready + aircraft_not_ready
		pilots_ready, pilots_in_resrerve = self.get_num_ready_pilots(debug=debug, level=level)
		log_message("get_num_pilots2add: total aircraft: %(total_aircraft)d, pilots ready: %(pilots_ready)d, pilots in reserve %(pilots_in_resrerve)d"%vars(), 3)
		if count_reserve_pilots:
			pilot_count = pilots_ready + pilots_in_resrerve
		else:
			pilot_count = pilots_ready
		return total_aircraft - pilot_count
	

	
		
		
	#start: Release Pilot Screen
	#action: Check the status a pilot and try to set it to OFF
	#return: 1 if pilot retain is set to ON or delay > 1, 0 if OFF
	#		 If no pilot there -1
	def set_one_retain(self, pilot_num, release=True, debug=False):
		status = self.check_retain(pilot_num, release=release, debug=debug)
		#There isn't a pilot at that position
		if status == -1:
			log_message("set_one_retain: No pilot at position %(pilot_num)d"%vars(), 5)
			return -1
		#pilot is delayed and cannot be released
		elif status == 0:
			log_message("set_one_retain:  Pilot %(pilot_num)d is delayed more than 1 day"%vars(), 5)
			return 1
		#pilot can be released but delayed 1 day
		elif status == 1:
			log_message("set_one_retain: Pilot at position %(pilot_num)d ready to be released"%vars(), 5)
			return 0
		#pilot can be immediately released
		elif status == 2:
			log_message("set_one_retain: Pilot at position %(pilot_num)d ready to be released"%vars(), 5)
			return 0
		#pilot can be released if retain becomes "ON"
		elif status == 3:
			if release:
				left =  pilot_cats_release[SkillIndexMapping['Retain']]
			else:
				left = 	pilot_cats_add[SkillIndexMapping['Retain']]
			SetRetainCoords = (left, pilot_heights[pilot_num])
			self.ClickInput(coords=SetRetainCoords)
			self.sleep(0.2)
			restatus = self.check_retain(pilot_num, release=release, debug=debug)
			#check if it got reversed to "ON"
			if restatus == 3:
				log_message("set_one_retain: Unable to flip retain of pilot %(pilot_num)d from ON to OFF"%vars(), 5)
				return 1
			else:
				log_message("set_one_retain: Flipped retain of pilot %(pilot_num)d from ON to OFF"%vars(), 5)
				return 0
					
				
		#we can add scrolling if we think we need to but that seems unnecessary
		log_message("set_one_retain: Something went wrong..."%vars(), 4)
		return -1
		


#return -1 for null, 0 for delayed more than 1 day, 1 for delayed one day, 2 for off, 3 for on
	def check_retain(self, pilot_num, release=True, debug=False):
		skill_map = SkillIndexMapping['Retain']
		if release:
			left = pilot_cats_release[skill_map] - 5
		else:
			left = pilot_cats_add[skill_map]- 5
		right = left + 20
		top = pilot_heights[pilot_num] -6
		bottom = top + 10
		box = (left, top, right, bottom)
		status = self.check_train(self.retain_knn, box, debug=debug)
		
		return_val = 0
		if status == 0:
			return_val = -1
		#pilot has retain value of "OFF"
		elif status == 1:
			delay_val = self.get_pilot_val(SkillIndexMapping['Delay'], pilot_num, release=True, debug=debug)
			if delay_val == 0:
				return_val = 2
				
			elif delay_val == 1:
				return_val = 1
				
			else:
				return_val = 0
		elif status == 2:
			return_val = 3
	
		if return_val == 0:
			log_message("check_retain: Pilot %(pilot_num)d is delayed at least 2 days"%vars(), 5)
		elif return_val == 1:
			log_message("check_retain: Pilot %(pilot_num)d is delayed 1 day"%vars(), 5)
		elif return_val == 2:
			log_message("check_retain: Pilot %(pilot_num)d can be released"%vars(), 5)
		elif return_val == 3:
			log_message("check_retain: Pilot %(pilot_num)d WILL be retained"%vars(), 5)
		else:
			log_message("check_retain: Pilot %(pilot_num)d is null"%vars(), 5)
		
		return return_val
		
		
		
			
		
	
	def train_all(self):
		#train for pool
		train_labels = ["Reserve", "Active", "Group", "pool_null"]
		self.Release_Pilot_To_Pool_Text_knn = self.train_knn(train_labels)
		
		train_labels = ["release_null", "release"]
		self.release_knn = self.train_knn(train_labels)
		
		train_labels = ["retain_null", "off", "on"]
		self.retain_knn = self.train_knn(train_labels)
		
		train_labels = []
		for c in ['W', 'R', 'G']:
			for i in range(10):
				train_labels.append("%d%s"%(i, c))
		train_labels.append('digit_null')
		#lower a an s needed when we check number of pilots in a group which is preceded by "has"
		train_labels.append('lower_s')
		train_labels.append('lower_a')
		train_labels.append('Lpar')
		train_labels.append('Rpar')
		train_labels.append('RparY')
		train_labels.append('RparG')
		train_labels.append('Rslash')
		train_labels.append('halfP')
		self.digit_knn = self.train_knn(train_labels)
		
		self.mission_types = ["MAirfieldAttack", "MASWPatrol", "MEscort", "MGroundAttack",
		"MNavalAttack", "MNavalSearch", "MPortAttack", "MRecon", "MStoodDown",
		"MSupplyTransport", "MSweep", "MTroopTransport", "TAirfieldAttack", "TASWPatrol", 
		"TEscort", "TGeneral", "TGroundAttack", "TNavalAttack", "TNavalSearch",
		"TPortAttack", "TRecon", "TSupplyTransport", "TSweep"]
		self.mission_knn = self.train_knn(self.mission_types)
		
		train_labels = ["Any", "GroupAllGroups", "ReservePool", "TRACOM"]
		self.pool_source_knn = self.train_knn(train_labels)
		
		train_labels = []
		for c in ['G', 'Y', 'R', 'W']:
			for pool in ['Reserve', 'Replace', 'TRACOM', 'Any']:
				train_labels.append("%sD%s"%(pool, c))
		self.pool_draw_knn = self.train_knn(train_labels)
		
		train_labels = ['pilots']
		self.pilot_bool_knn = self.train_knn(train_labels)
		
		train_labels = ['pilots_comma']
		self.pilot_release_bool_knn = self.train_knn(train_labels)
		
		train_labels = ['scroll_null', 'scroll_top', 'scroll_missing']
		self.scroll_knn = self.train_knn(train_labels)
		
		train_labels = ["Current"]
		self.current_text_knn = self.train_knn(train_labels)
		
		train_labels = ["CantAddPilot", "GetNewPilot", "GetInstructor"]
		self.get_new_pilot_knn = self.train_knn(train_labels)
		
		train_labels = ["UsingBombsY", "UsingTorpedoesY", "UsingTorpedoesR"]
		self.using_torpedoes_knn = self.train_knn(train_labels)
		
		
	def check_group_train(self, image_cropped):
		cv_image = np.array(image_cropped)
		gray = cv2.cvtColor(cv_image,cv2.COLOR_BGR2GRAY)
		flat = np.array(gray).reshape(1, -1).astype(np.float32)
		if len(self.group_image_list) > 0:
			ret,result,neighbours,dist = self.group_name_knn.find_nearest(flat, k=1)
			dist = dist[0][0]
			result = int(result[0][0])
			if dist < 1000.0:
				#log_message('check_group_train: %d matches %d with value %f'%(self.pic_num - 1, result, dist), 5)
				return True
			else:
				pass
				#log_message('check_group_train: New number %d with value %f'%(self.pic_num - 1, dist), 5)
			
		self.group_image_list.append(flat)
		responses = np.arange(len(self.group_image_list))
		trainData = np.array(self.group_image_list).reshape(len(self.group_image_list), -1).astype(np.float32)
		self.group_name_knn.train(trainData,responses)
		return False
		
	
	def create_air_group(self, air_group_number):
		air_group = AirGroup(air_group_number)
		self.pilot_pool_group.add_new_group(air_group, air_group_number)
		return air_group
	
	def get_group_num(self, level=10):
		num = self.get_num((171, 165), size=4, level=level)
		return num

		
	def get_pool_source(self):
		return self.pool_source
		
	def get_plane_type(self):
		return self.plane_type
		
	def get_nation(self):
		return self.nation

	def train_knn(self, train_labels):
		train = []
		base_path = self.path + "images"
		for i, dest in enumerate(train_labels):
			path = base_path + "\\\%s.jpeg"%dest
			try:
				dest_image = cv2.imread(path)
			except:
				log_message("train_knn: Error fail to load %(path)s"%vars(), 0)
				os._exit(1)
			else:
				gray = cv2.cvtColor(dest_image,cv2.COLOR_BGR2GRAY)
				train.append(gray)
		dest_image = cv2.imread(path)
		trainData = np.array(train).reshape(len(train), -1).astype(np.float32)
		responses = np.arange(len(train_labels))
		knn = cv2.KNearest()
		knn.train(trainData,responses)
		return knn
	
	def select_nation_plane(self, nation, plane_type, debug=False):
		nation_y = 268
		plane_y = 255
		nation_x = AlliedNationLocations[nation]
		plane_x = AlliedPlaneLocations[plane_type]
		
		self.ClickInput(coords=(nation_x, nation_y), right=True)
		self.sleep(0.2)
		self.ClickInput(coords=(plane_x, plane_y), right=True)
		self.sleep(0.2)
		
	def handle_bar(self, bar_type, debug=False, level=10):
		if bar_type == 'nation_select_bar':
			nation = self.get_nation()
			x1 = AlliedNationLocations['AllNations']
			x2 = AlliedNationLocations[nation]
			y = 268
		elif bar_type == 'plane_select_bar':
			plane_type = self.get_plane_type()
			x1 = AlliedPlaneLocations['AllTypes']
			x2 = AlliedPlaneLocations[plane_type]
			y = 255
		elif bar_type == 'pilot_pool_source_bar':
			pool_source = self.get_pool_source()
			x1 = PoolSourceLocation['All']
			x2 = PoolSourceLocation[pool_source]
			y = 255
		else:
			log_message("handle_bar: could not recognize Bar Type %(bar_type)"%vars(), 0)
			raise Exception
		coords = (x1, y)
		
		self.click_away()
		self.sleep(0.2)
		
		set_green = False
		#see if we already set All
		for i in range(6):
			green_status = self.check_text_green(x1, y, debug=debug, level=level)
			if green_status == 1:
				set_green = True
				
			elif green_status == -1:
				print "error"
				break
			else:
				if set_green:
					self.sleep(0.1)
					break
					
			self.ClickInput(coords=coords)
			self.click_away()
			self.sleep(0.2)
		
		#flip it again
		coords = (x2, y)
		self.ClickInput(coords=coords)
		
		
	def check_text_green(self, mid_x, mid_y, debug=False, level=10):
		left = mid_x - 5
		right = mid_x + 5
		top = mid_y - 5
		bottom = mid_y + 5
		box = (left, top, right, bottom)
		cropped_image = self.get_screen_box(box, debug=debug, level=level)
		return self.check_green_status(cropped_image, debug=debug)
	
	
	#no support for the weird training squadrons yet
	#Screen: Main pilot screen
	def get_altitude(self, start_index=0, end_index=14, debug=False, level=10):
		top = 323
		left = 655
		width = 35
		right = left + width
		height = 13
		spacing = 12
		for i in range(start_index, end_index):
			local_top = top + spacing * i
			bottom = local_top + height
			box = (left, local_top, right, bottom)
			if self.check_bool_train(self.current_text_knn, box, tolerence=300, debug=debug, level=1):
				coords = (left + 77, local_top+8)
				num = self.get_num(coords, size=5, debug=debug, level=level)
				return num
		return -1
			
			
		
	#Start: Main unit screen
	#Action: Go to release pilot screen
	#		Get mission
	#End: Main unit screen
	def get_mission_type(self, debug=False):
		#go to release pilot screen
		self.ClickInput(coords=PilotsButtonCoord)
		self.sleep(0.2)
		
		left = 259
		top = 246
		right = 382
		bottom = 257
		box = (left, top, right, bottom)
		mindex = self.check_train(self.mission_knn, box, debug=debug)
		mtype = self.mission_types[mindex]
		
		self.ClickInput(coords=Done)
		self.sleep(0.2)
		return mtype
		
	def set_pool_dest(self):
		left = 668
		top = 234
		right = 757
		bottom = 245
		box = (left, top, right, bottom)
		coords = (683, 240)
		for i in range(6):
			status = self.check_train(self.pool_source_knn, box)
			if status == 2:
				return True
			else:
				self.ClickInput(coords=coords)
				self.sleep(0.5)
		return False
		
	def add_new_pilots(self):
		left = 257
		top = 330
		right = 269
		bottom = 342
		box = (left, top, right, bottom)
		while True:
			status = self.check_train(self.release_knn, box, debug=True)
			if status:
				self.ClickInput(coords=(263, 336))
				self.sleep(0.2)
			else:
				break
	#start: Any
	#action: Check if a standard right arrow button can be pressed
	def check_button_status(self, coords, debug=False, level=10):
		x_center, y_center = coords
		
		left = x_center - 6
		right = x_center + 6
		
		top = y_center - 6
		bottom = y_center + 6
		
		
		box = (left, top, right, bottom)
		status = self.check_train(self.release_knn, box, debug=debug, level=level)
		if status:
			return True
		else:
			return False
	
	def check_can_add_reserve_pilots(self, debug=False):
		coords = RequestVeteran
		return self.check_button_status(coords, debug=debug)
	

	def set_pool_draw(self, pool, main_screen=True, debug=False):
		if main_screen:
			left = 335
			top = 331
		else:
			left = 670
			top = 234
		right = left + 34
		bottom = top + 10
		box = (left, top, right, bottom)
		coords = (left+10, top+5)
		if pool == 'Reserve':
			dest_num = 0
		elif pool == 'Replacement':
			dest_num = 1
		elif pool == 'TRACOM':
			dest_num = 2
		elif pool == 'Any':
			dest_num = 3
		else:
			raise Exception
		
		#8 rounds for good measure
		for i in range(8):
			status = self.check_train(self.pool_draw_knn, box, debug)
			pool_dest = status % 4
			if pool_dest == dest_num:
				return True
			else:
				self.ClickInput(coords=coords)
				self.sleep(0.3)
		return False
			
	
	def sort_skill(self, skill, ascending=True, release=True, debug=True):
		log_message('sort_skill: Sorting skill %(skill)s'%vars(), 5)
		col = SkillIndexMapping[skill]
		if release:
			x = pilot_cats_release[col]
		else:
			x = pilot_cats_add[col]
		coords = (x, 270)
		self.ClickInput(coords=coords)
		self.sleep(0.2)
		self.scroll_to_top(debug=debug)
		self.sleep(0.2)
		is_ascending = self.check_ascending(col, release=release, debug=debug)
		if is_ascending == ascending:
			return True
		else:
			self.ClickInput(coords=coords)
			self.sleep(0.2)
			self.scroll_to_top()
			return True
			
		
		
		
	def sort_cat(self, col, ascending=True, release=True, debug=False):
		log_message('sort_cat: Sorting column %(col)d'%vars(), 5)
		if release:
			x = pilot_cats_release[col]
		else:
			x = pilot_cats_add[col]
		coords = (x, 270)
		self.ClickInput(coords=coords)
		self.sleep(0.2)
		self.scroll_to_top(debug=debug)
		self.sleep(0.2)
		is_ascending = self.check_ascending(col, release=release, debug=debug)
		if is_ascending == ascending:
			return True
		else:
			self.ClickInput(coords=coords)
			self.sleep(0.2)
			self.scroll_to_top()
			return True
			
		
			
	#start: Release or Add Pilot Screen already scrolled to the top
	#action: Check to see if a given column is ascending
	#		 Start at pilot 8 and do a search
	#return: Return true if ascending, no pilots, or all equal
	#		 Else -1	
	def check_ascending(self, col, release=True, debug=False):
		first_pilot_val = self.get_pilot_val(col, 0, release=release, debug=debug)
		if first_pilot_val< 0:
			log_message("check_ascending: no pilots", 4)
			return True
		if release:
			num_pilots = self.check_num_pilots_in_group(debug=debug)
		else:
			#go to the bottom
			num_pilots, _ = self.check_pilot_number_info()
		log_message("check_ascending: %(num_pilots)d pilots in list"%vars(), 4)
		scroll_back = False
		if num_pilots > 25:
			last_pilot = 25
			self.scroll_to_bottom()
			self.sleep(0.1)
			scroll_back = True
		else:
			last_pilot = num_pilots
		last_pilot_val = self.get_pilot_val(col, last_pilot, release=release, debug=debug)
		if scroll_back:
			self.scroll_to_top()
		if last_pilot_val < first_pilot_val:
			return False
		else:
			return True
		
	def take_pic(self):
		box = self.screen_box
		if self.double:
			real_width = 2 * (box[2] - box[0])
			real_height = 2 * (box[3] - box[1])
			bmp = win32ui.CreateBitmap()
			bmp.CreateCompatibleBitmap(self.srcdc, real_width, real_height)
			self.memdc.SelectObject(bmp)
			self.memdc.BitBlt((0, 0), (real_width, real_height), self.srcdc, (0, 0), win32con.SRCCOPY)
			bmpstr = bmp.GetBitmapBits(True)
			im = Image.frombuffer('RGB', (real_width, real_height), bmpstr, 'raw', 'BGRX', 0, 1)
		else:
			im = ImageGrab.grab(box)
		return im
	
	def save_screenshot(self):
		im = self.take_pic()
		if self.double:
			size = (self.ideal_box[2], self.ideal_box[3])
			im = im.resize(size)
		outfile = "full_screen.jpeg"
		im.save(outfile)
	
	def get_screen_box(self, box, debug=False, level=10, override_level=-2):
		global sample_path
		global screen_count
		global crop_debug_count
		if self.need_refresh:
			image = self.take_pic()
			self.current_screen = image
			self.need_refresh = 0
			crop_debug_count = 0
			self.need_debug_refresh = 0
			screen_count += 1
			outfile = "%s/%d.jpeg"%(sample_path, screen_count)
			self.current_screen.save(outfile)
			

			
		image_cropped = self.crop_current_screen(box, debug=debug, level=level)
		return image_cropped

		
	def crop_current_screen(self, box, debug=False, level=10, override_level=-2):
		image = self.current_screen
		
		if self.double:
			size = (box[2] - box[0], box[3] - box[1])
			left = box[0] * 2 + self.left_offset
			top = box[1] * 2 + self.top_offset
			right = box[2] * 2 + self.left_offset
			bottom = box[3] * 2 + self.top_offset
			new_box = (left, top, right, bottom)
			cropped_image = image.crop(new_box)
			cropped_image = cropped_image.resize(size)
		else:
			cropped_image = image.crop(box)
		
		#ovr off
		save_image = False
		global message_level
		if override_level < -1:
			if level <= message_level:
				save_image = True
		else:
			if level <= override_level:
				save_image = True
				
		if save_image:
			x = box[0]
			y = box[1]
			width = box[2] - box[0]
			height = box[3] - box[1]
			box_str = "%(x)d_%(y)d_%(width)d_%(height)d"%vars()
			global screen_count
			global crop_debug_count
			crop_debug_count += 1
			outfile = "%s/%d_%d_%s.jpeg"%(sample_path, screen_count, crop_debug_count, box_str)
			cropped_image.save(outfile)
				
		return cropped_image



	def get_pilot_y_offset(self, release=True, debug=False, level=10):
		x = 184
		y_start = 275
		
		for offset in range(10):
			y = y_start + offset
			box = (x, y, x+10, y+1)
			cropped_image = self.get_screen_box(box, debug=debug, level=level)
			cv_image = np.array(cropped_image)
			flat = cv_image.reshape(-1, 1).astype(np.float32)
			for num in flat:
				if num > 200:
					return offset
		raise Exception
		
		
		
	def check_green_status(self, cropped_image, debug=False):
		cv_image = np.array(cropped_image)
		flat = cv_image.reshape(-1, 3).astype(np.float32)
		yellow_count = 0
		green_count = 0
		for blue, green, red in flat:
			if green > 200:
				if blue > 200:
					yellow_count += 1
				elif blue < 20:
					green_count += 20
		diff = green_count - yellow_count
		if diff > 5:
			return 1
		elif diff < -5:
			return 0
		else:
			return -1
	
	def save_main_screen_info(self, debug=False, level=10):
		num_pilots_ready, num_pilots_in_reserve = self.get_num_ready_pilots(debug=debug, level=level)
		num_ready_aircraft, num_grounded_aircraft = self.get_num_aircraft(debug=debug, level=level)
		
		air_group_num = self.get_group_num()
		self.pilot_pool_group.set_group_from_num(air_group_num)
		
		current_air_group = self.pilot_pool_group.current_air_group
		self.current_air_group = current_air_group
		
		current_air_group.num_pilots_ready = num_pilots_ready
		current_air_group.num_pilots_in_reserve = num_pilots_in_reserve
		current_air_group.num_ready_aircraft = num_ready_aircraft
		current_air_group.num_grounded_aircraft = num_grounded_aircraft
		
		mission = self.get_mission_type()
		log_message('save_main_screen_info: Got mission %(mission)s'%vars(), 5)
		
		
		altitude = self.get_altitude()
		
		'''
		attempt_number = 0
		while altitude  < 100:
			log_message('save_main_screen_info: Got altitude %(altitude)d on attempt %(attempt_number)d'%vars(), 5)
			attempt_number +=1
			self.sleep(0.2)
			altitude = self.get_altitude(debug=debug, level=level)
		'''
		
		current_air_group.mission = mission
		current_air_group.altitude = altitude
		
		#check the torpedo
		current_air_group.train_torpedoes = False
		if mission == "TNavalAttack":
			if self.check_torpedoes(debug=debug, level=level):
				current_air_group.train_torpedoes = True
		
	
	def mark_group_as_done(self):
		current_air_group = self.pilot_pool_group.current_air_group
		current_air_group.mark_as_done()
	
	def set_pilot_source(self, source_type):
		pass
		
	
	#start: Release or Add Pilot Screen
	#action: move through header line and match the word pilot
	#		 When the location of "pilot" is known we can get numbers
	#return: Return the tuple containing the number in the list and the number needed
	def check_pilot_number_info(self, debug=False, level=10):
		left = 339
		top = 235
		width = 24
		height = 10
		
		num_in_list = -1
		#i = 0 means single digit, i = 1 means double digit, etc
		for i in range(4):
			box = (left, top, left+width, top+height)
			log_message('check_pilot_number_info: Attempting to match pilots in list number location at attempt %(i)d'%vars(), 4)
			if self.check_bool_train(self.pilot_bool_knn, box, level=10):
				coords = (left - 6, top + 5)
				num_in_list = self.get_num(coords, size=(i+1), debug=True, level=level)
				log_message('check_pilot_number_info: Success finding pilots in list at attempt %(i)d'%vars(), 4)
			left += 5
		#76 is min offset between the two numbers
		left += 76
		
		num_needed = -1
		for i in range(2):
			box = (left, top, left+width, top+height)
			log_message('check_pilot_number_info: Attempting to match pilot needed number location at attempt %(i)d'%vars(), 4)
			if self.check_bool_train(self.pilot_bool_knn, box, level=level):
				coords = (left - 6, top + 5)
				num_needed = self.get_num(coords, size=(i+1), debug=debug, level=level)
				log_message('check_pilot_number_info: Success finding pilots needed at attempt %(i)d'%vars(), 4)
			left += 5
		return num_in_list, num_needed
	
	
	def check_num_pilots2add(self, debug=False, level=10):
		left = 300
		top = 235
		width = 24
		height = 10
		for i in range(10):
			box = (left, top, left+width, top+height)
			log_message('check_num_pilots2add: Attempting to match pilot number location at attempt %(i)d'%vars(), 3)
			if self.check_bool_train(self.pilot_bool_knn, box, level=level):
				coords = (left - 6, top + 5)
				num = self.get_num(coords, size=2, debug=debug, level=level)
				log_message('check_num_pilots2add: Success at attempt %(i)d'%vars(), 3)
				return num
			left += 5
			if left > 350:
				break
		log_message('check_num_pilots2add: Failed to get the number of pilots needed to add!', 3)
	
	#start: release pilot screen
	def check_num_pilots_in_group(self, dig_size=3, debug=False, level=10):
		left = 290
		top = 235
		width = 24
		height = 10
		for i in range(400):
			box = (left, top, left+width, top+height)
			if self.check_bool_train(self.pilot_release_bool_knn, box, tolerence=500, debug=debug, level=level):
				coords = (left - (5*dig_size-4), top + 5)
				num = self.get_num(coords, size=dig_size, debug=debug, level=level)
				log_message('check_num_pilots_in_group: Success at attempt %(i)d'%vars(), 3)
				return num
			left += 1
		log_message('check_num_pilots_in_group: Failed to get the number of pilots needed to add!', 3)
		return -1
	
	#start: Main unit screen
	#return True if special training group, False if normal group
	def check_if_special_training_group(self, debug=False):
		left = 167
		top = 329
		width = 81
		height = 14
		box = (left, top, left+width, top+height)
		status = self.check_train(self.get_new_pilot_knn, box, debug=debug)
		log_message("check_if_special_training_group: Status %(status)d"%vars(), 3)
		if status == 2:
			return True
		else:
			return False
			
	#start: Main unit screen
	#return a tuple of the number of ready planes and damaged/maintained 
	def get_num_aircraft(self, debug=True, level=10):
		left = 266
		top = 227
		bottom = top + 10
		#no more than 3 digits
		num_ready_aircraft = 0
		for i in range(3):
			right = left + 5
			box = (left, top, right, bottom)
			result = self.check_train(self.digit_knn, box, debug=debug, level=level)
			#check to see if this is a number of a parentheses
			if result >= 30:
				break 
			else:
				digit = result % 10
				num_ready_aircraft = num_ready_aircraft * 10 + digit
				left += 5
		#now look at the maintained planes
		left = 266
		top = 238
		bottom = top + 10
		num_maintained_aircraft = 0
		for i in range(2):
			right = left + 5
			box = (left, top, right, bottom)
			result = self.check_train(self.digit_knn, box, debug=debug)
			#check to see if this is a number of a parentheses
			if result >= 30:
				break 
			else:
				digit = result % 10
				num_maintained_aircraft = num_maintained_aircraft * 10 + digit
				left += 5
		#now get damaged planes
		left += 7
		num_damaged_aircraft = 0
		for i in range(2):
			right = left + 5
			box = (left, top, right, bottom)
			result = self.check_train(self.digit_knn, box, debug=debug)
			#check to see if this is a number of a parentheses
			if result >= 30:
				break 
			else:
				digit = result % 10
				num_damaged_aircraft = num_damaged_aircraft * 10 + digit
				left += 5
		num_grounded_aircraft = num_maintained_aircraft + num_damaged_aircraft
		return num_ready_aircraft, num_grounded_aircraft
		
	
	
	#start: Main unit screen
	#return a tuple of the number of ready pilots and pilots in reserve
	def get_num_ready_pilots(self, debug=True, level=10):
		far_left = 266
		top = 274
		bottom = top + 10
		#no more than 3 digits
		num_pilots_ready = 0
		left = far_left
		for i in range(3):
			right = left + 5
			box = (left, top, right, bottom)
			result = self.check_train(self.digit_knn, box, debug=debug, level=10)
			#check to see if this is a number of a parentheses
			if result >= 30:
				break 
			else:
				digit = result % 10
				num_pilots_ready = num_pilots_ready * 10 + digit
				left += 5
		#now get the pilots in reserve
		num_pilots_in_reserve = 0
		left += 5
		for i in range(3):
			right = left + 5
			box = (left, top, right, bottom)
			result = self.check_train(self.digit_knn, box, debug=debug)
			#check to see if this is a number of a parentheses
			if result >= 30:
				break 
			else:
				digit = result % 10
				num_pilots_in_reserve = num_pilots_in_reserve * 10 + digit
				left += 5
		return num_pilots_ready, num_pilots_in_reserve


	def check_torpedoes(self, debug=False, level=10):
		
		#check to see if button is there
		#if no button then we may carry torpedoes
		coords = (433, 390)
		if self.check_button_status(coords, debug=debug, level=level):
			return False
		
		
		box = (444, 385, 535, 397)
		status = self.check_train(self.using_torpedoes_knn, box, debug=debug, level=level)
		#even if no torpedoes available we still train it
		if status > 0:
			return True
		else:
			return False

		

		
end_program = False
def wait_for_key():
	hm = pyHook.HookManager()
	hm.KeyDown = OnKeyboardEvent
	hm.HookKeyboard()
	global end_program
	while not end_program:
		pythoncom.PumpWaitingMessages()

def OnKeyboardEvent(event):
	key = chr(event.Ascii)
	if key == "=":
		os._exit(1)

		
#Bug list
#1. Occasionally we read the wrong altitude and mission


#TODO:
#1. Check if we are using torpedoes


def run():
	pilot = PilotManager(time_fact=1, message_level_input=5)
	pilot.set_pool_nation("Fighter", "USN")
	pilot.train_pilots(debug=False)
	#pilot.read_pilot_pool(debug=True)
	#pilot.sweep_plane_nation_group("F", "USMC", debug=True)
	#pilot.Release_Pilot_To_Pool("Reserve")
	#pilot.add_pilots_by_skill(debug=True)
	#pilot.save_screenshot()
	print 'done'
	os._exit(1)



if __name__ == "__main__":
	global Thread2
	Thread1 = threading.Thread(target=run)
	Thread2 = threading.Thread(target=wait_for_key)
	Thread2.start()
	Thread1.start()
	Thread2.join()
	Thread1.join()
	print "done"


