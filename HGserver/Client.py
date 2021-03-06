import struct, time
from Sockets import HelbreathSocket
from Helpers import strip_zeros
import NetMessages
import Packets

class ClientSocket(HelbreathSocket):
	'''
		Gate server protocol class
	'''
	dir = 0
	type = 0
	status = 0
	ping = 0
		
	def __init__(self, instance):
		'''
			No need for address and port
		'''
		super(ClientSocket, self).__init__(
			address = None,
			port = None,
			instance = instance
		)
		self.setblocking(False)
	
	def pop_packet(self):
		packet = super(ClientSocket, self).pop_packet()
		
		if not packet:
			return False
		
		if len(packet) < 6:
			return False
		
		MsgID, MsgType = struct.unpack('<IH', packet[:6])
		packet = packet[6:]
		
		if MsgID == NetMessages.MSGID_REQUEST_INITPLAYER:
			fmt = '<10s' # char_name
			fmt += '10s' # account_name
			fmt += '10s' # account password
			fmt += '?' # is observer mode ?
			packet_len = struct.calcsize(fmt)
			
			(char_name, account_name, account_password, is_observer_mode, ) = \
				map(strip_zeros, struct.unpack(fmt, packet[:packet_len]))
				
			self.on_request_initplayer(
				char_name = char_name,
				account_name = account_name,
				account_password = account_password,
				is_observer_mode = is_observer_mode,
				client = self						
			)
		elif MsgID == NetMessages.MSGID_REQUEST_INITDATA:
			fmt = '<10s' # char_name
			fmt += '10s' # account_name
			fmt += '10s' # account password
			packet_len = struct.calcsize(fmt)
			
			(char_name, account_name, account_password, ) = \
				map(strip_zeros, struct.unpack(fmt, packet[:packet_len]))
			
			self.on_request_initdata(
				char_name = char_name,
				account_name = account_name,
				account_password = account_password,
				client = self
			)
		
		elif MsgID == NetMessages.MSGID_REQUEST_NOTICEMENT:
			fmt = '<I'
			packet_len = struct.calcsize(fmt)
			client_size, = struct.unpack(fmt, packet[:packet_len])
			print 'Request noticement: %dbytes' % client_size
			self.on_request_noticement(
				client = self,
				file_size = client_size
			)
		
			self.send_msg(struct.pack('<IH',
				NetMessages.MSGID_RESPONSE_NOTICEMENT,
				NetMessages.DEF_MSGTYPE_CONFIRM
			))
			
		elif MsgID == NetMessages.MSGID_REQUEST_FULLOBJECTDATA:
			self.on_request_fullobjectdata(
				client = self,
				object_id = MsgType				
			)
		elif MsgID == NetMessages.MSGID_COMMAND_CHECKCONNECTION:
			self.on_command_checkconnection()
		else:
			print 'Client packet. MsgID: 0x%08X MsgType: 0x%04X' % (MsgID, MsgType)
		
		return True
	'''
		Client functions
	'''
	
	def do_response_initplayer(self, success):
		# Fun fact:
		# If you call do_response_initplayer(success = False)
		# Original client will show message 'World Server Full'
		# 'Try other World server'
		
		data = struct.pack('<IH',
			NetMessages.MSGID_RESPONSE_INITPLAYER,
			NetMessages.DEF_MSGTYPE_CONFIRM if success else NetMessages.DEF_MSGTYPE_REJECT
		)
		self.send_msg(data)
		
	def do_playercharactercontents(self):
		stats = self.player_data.str + \
			self.player_data.vit + \
			self.player_data.dex + \
			self.player_data.int + \
			self.player_data.mag + \
			self.player_data.chr
			
		self.lu_pool = stats - self.player_data.level * 3
		
		self.send_packet(
			Packets.PLAYERCHARACTERCONTENTS,
			hp = self.player_data.hp,
			mp = self.player_data.mp,
			sp = self.player_data.sp,
			defense_ratio = 0, # TODO: Calculate defense ratio
			hit_ratio = 0, # TODO: Calculate hit ratio
			level = self.player_data.level,
			str = self.player_data.str,
			int = self.player_data.int,
			vit = self.player_data.vit,
			dex = self.player_data.dex,
			mag = self.player_data.mag,
			chr = self.player_data.chr,
			lu_pool = self.lu_pool,
			exp = self.player_data.exp,
			ek_count = self.player_data.ek_count,
			pk_count = self.player_data.pk_count,
			reward_gold = self.player_data.reward_gold,
			location = self.player_data.location,
			guild_name = self.player_data.guild_name,
			guild_rank = self.player_data.guild_rank,
			leftsac = self.player_data.leftsac,
			fightzone_number = -1 # TODO: Fightzone number	
		)
		
		self.do_playeritemlistcontents()

	def do_playeritemlistcontents(self):
		print 'do playeritemlistcontents'
		
		# TODO: decode item list contents
		
		magic_mastery = ''.join(
			map(lambda spell: {'1': chr(1), '0': chr(0)}[spell], self.player_data.magic_mastery)
		)
		
		self.send_packet(Packets.PLAYERITEMLISTCONTENT,
			item_count = 0,
			items = [],
			bankitem_count = 0,
			bankitems = [],
			magicmastery = magic_mastery,
			skills = self.player_data.skill_mastery,
		)
		
	def get_type(self):
		if self.player_data.admin_user_level >= 10:
			return self.player_data.admin_user_level
		
		t = 0
		if self.player_data.sex == 1:
			t = 1
		elif self.player_data.sex == 2:
			t = 4
			
		t += self.player_data.skin - 1

		return t
				
	def do_response_initdata(self):
		print 'do response initdata'
		fmt = '<IH'
		fmt += 'H' # Client ID
		fmt += 'hh' # X, Y
		fmt += 'h' # Type
		fmt += '4h' # Appr1 Appr2 Appr3 Appr4
		fmt += 'i' # Appr color
		fmt += 'i' # Status (auras etc)
		fmt += '10s' # Map name
		fmt += '10s' # Location
		fmt += 'B' # Day or night (Sprite alpha degree?)
		fmt += 'B' # Weather status
		fmt += 'I' # Contribution
		fmt += 'B' # Is observer mode?
		fmt += 'i' # Rating
		fmt += 'I' # HP
		fmt += 'x' # "Discount" -> % cost
		data = struct.pack(fmt,
			NetMessages.MSGID_RESPONSE_INITDATA,
			NetMessages.DEF_MSGTYPE_CONFIRM,
			self.id,
			self.player_data.x - 14 - 5,
			self.player_data.y - 12 - 5,
			self.get_type(),
			(self.player_data.hair_style << 8) | (self.player_data.hair_color << 4) | (self.player_data.underwear),
			0, 0, 0, # TODO: Appr 2 - 4
			0, # TODO: Appr color
			0, # Status
			self.player_data.map_name,
			self.player_data.location,
			2, # Its always night :) (1 = Day 2 = Night)
			0, # Weather. 3 = Rainy 4 = Snowy ...
			self.player_data.contribution,
			0, # Ofcourse, player is not in observer mode
			self.player_data.rating,
			self.player_data.hp,
		)
		
		# Composed map data
		
		data += struct.pack('<H', 0) # Total tiles
		
		print 'initdata len', len(data)
		self.send_msg(data)
		
	def do_event_motion(self, action, object):
		print 'do event motion', action
		
		actions = {
			'stop': NetMessages.DEF_OBJECTSTOP
		}
		
		header = struct.pack('<IH', NetMessages.MSGID_EVENT_MOTION, actions[action])
		
		if object.id < 10000:
			# Human
			fmt = '<H' # Object ID
			fmt += 'hh' # X, Y
			fmt += 'h' # Type
			fmt += 'h' # Dir
			fmt += '10s' # Char name
			fmt += '4h' # Appr 1 - 4
			fmt += 'i' # Appr color
			fmt += 'I' # Status
			fmt += '?' # Is killed ?
			header += struct.pack(fmt,
				object.id,
				object.player_data.x, object.player_data.y,
				0, # Type
				object.dir, # Direction
				object.player_data.char_name,
				0, 0, 0, 0, # TODO: Appr 1 - 4
				object.status,
				object.player_data.hp <= 0
			)
		else:
			# NPC
			print 'Unimplemented: NPC event motion'
			return
		
		self.send_msg(header)
	
	def send_noticement(self, data):
		print 'send_noticement', data
		if not data:
			self.send_msg(struct.pack('<IH', NetMessages.MSGID_RESPONSE_NOTICEMENT, NetMessages.DEF_MSGTYPE_CONFIRM))
			return
		
		self.send_msg(struct.pack('<IH', NetMessages.MSGID_RESPONSE_NOTICEMENT, NetMessages.DEF_MSGTYPE_REJECT) + \
			data
		)
		
	def on_request_initplayer(self, char_name, account_name, account_password, is_observer_mode, client):
		pass
	
	def on_request_initdata(self, char_name, account_name, account_password, client):
		pass
	
	def on_request_noticement(self, client, file_size):
		pass
	
	def on_request_fullobjectdata(self, client, object_id):
		pass
	
	def on_command_checkconnection(self):
		'''
			We dont need to handle this message in main Server module
		'''
		if self.ping:
			print '(!) Player:%s Ping:%.4fms' % (
				self.player_data.char_name,
				time.time() - self.ping
			)
			self.ping = time.time()
			return
		
		self.ping = time.time()