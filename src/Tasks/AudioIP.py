# -*- coding: utf-8 -*-
#  Copyleft 2021-2024 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

class AudioIP:

	"""
	AudioIP is a class that handles the AudioIP protocol for streaming audio data.
	It provides methods to connect to an AudioIP server, send audio data, and handle
	incoming messages.
	"""

	def __init__(self):
		"""
		Initializes the AudioIP class.
		"""
		pass
		
	def connect(self, host, port):
		"""
		Connects to the AudioIP server.

		:param host: The hostname or IP address of the AudioIP server.
		:param port: The port number of the AudioIP server.
		"""
		pass

	def send_audio_data(self, data):
		"""
		Sends audio data to the AudioIP server.

		:param data: The audio data to be sent.
		"""

	def receive_message(self):
		"""
		Receives a message from the AudioIP server.
		:return: The received message.
		"""

	def close(self):
		"""
		Closes the connection to the AudioIP server.
		"""
