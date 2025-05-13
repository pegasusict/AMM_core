# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
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

"""This Module communicates with the server of MusicBrainz.
It uses the musicbrainzngs library to communicate with the MusicBrainz API.
It is used to retrieve information about artists, albums, and tracks.
It is also used to retrieve the cover art for albums and artists.
It is used to retrieve the MusicBrainz ID for albums, artists and tracks.
"""

import musicbrainzngs

from src.Singletons.config import Config
from src.Singletons.logger import Logger

class MusicBrainzClient:
	"""This Class communicates with the server of MusicBrainz."""

	def __init__(self, config:Config) -> None:
		"""Initializes the ArtGetter class."""
		self.logger = Logger(config)
		self.config = config
		self.musicbrainz = musicbrainzngs
		self.musicbrainz.set_useragent("Audiophiles Music Manager", "0.1", "pegasus.ict@gmail.com")
		self.musicbrainz.set_rate_limit(True)

	def get_album_art(self, mbid:str) -> str|None:
		"""
		Retrieves album art from online archives.

		Args:
			mbid: The MusicBrainz ID of the album.

		Returns:
			The URL of the album art.
		"""
		try:
			result = self.musicbrainz.get_image_list(mbid)
			if result['images']:
				return result['images'][0]['thumbnails']['large']
			else:
				return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving album art: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving album art: {e}")
			return None

	def get_artist_art(self, mbid:str) -> str|None:
		"""
		Retrieves artist art from online archives.

		Args:
			mbid: The MusicBrainz ID of the artist.

		Returns:
			The URL of the artist art.
		"""
		try:
			result = self.musicbrainz.get_image_list(mbid)
			if result['images']:
				return result['images'][0]['thumbnails']['large']
			return None
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving artist art: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving artist art: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving artist art: {e}")
			return None

	def get_release_group_by_id(self, mbid:str) -> str|None:
		"""
		Retrieves release group information by MusicBrainz ID.

		Args:
			mbid: The MusicBrainz ID of the release group.

		Returns:
			The release group information.
		"""
		try:
			result = self.musicbrainz.get_release_group_by_id(mbid)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release group: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release group: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release group: {e}")
			return None

	def get_artist_by_id(self, mbid:str) -> str|None:
		"""
		Retrieves artist information by MusicBrainz ID.

		Args:
			mbid: The MusicBrainz ID of the artist.

		Returns:
			The artist information.
		"""
		try:
			result = self.musicbrainz.get_artist_by_id(mbid)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving artist: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving artist: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving artist: {e}")
			return None

	def get_release_by_id(self, mbid:str) -> str|None:
		"""
		Retrieves release information by MusicBrainz ID.

		Args:
			mbid: The MusicBrainz ID of the release.

		Returns:
			The release information.
		"""
		try:
			result = self.musicbrainz.get_release_by_id(mbid)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_recording_by_id(self, mbid:str) -> str|None:
		"""
		Retrieves recording information by MusicBrainz ID.

		Args:
			mbid: The MusicBrainz ID of the recording.

		Returns:
			The recording information.
		"""
		try:
			result = self.musicbrainz.get_recording_by_id(mbid)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_track_by_id(self, mbid:str) -> str|None:
		"""
		Retrieves track information by MusicBrainz ID.

		Args:
			mbid: The MusicBrainz ID of the track.

		Returns:
			The track information.
		"""
		try:
			result = self.musicbrainz.get_recording_by_id(mbid)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_album_by_id(self, mbid:str) -> str|None:
		"""
		Retrieves album information by MusicBrainz ID.

		Args:
			mbid: The MusicBrainz ID of the album.

		Returns:
			The album information.
		"""
		try:
			result = self.musicbrainz.get_release_by_id(mbid)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_artist_by_name(self, name:str) -> str|None:
		"""
		Retrieves artist information by name.

		Args:
			name: The name of the artist.

		Returns:
			The artist information.
		"""
		try:
			result = self.musicbrainz.search_artists(name=name)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_album_by_name(self, name:str) -> str|None:
		"""
		Retrieves album information by name.

		Args:
			name: The name of the album.

		Returns:
			The album information.
		"""
		try:
			result = self.musicbrainz.search_releases(name=name)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_track_by_name(self, name:str) -> str|None:
		"""
		Retrieves track information by name.

		Args:
			name: The name of the track.

		Returns:
			The track information.
		"""
		try:
			result = self.musicbrainz.search_recordings(name=name)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_release_group_by_name(self, name:str) -> str|None:
		"""
		Retrieves release group information by name.

		Args:
			name: The name of the release group.

		Returns:
			The release group information.
		"""
		try:
			result = self.musicbrainz.search_release_groups(name=name)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_recording_by_name(self, name:str) -> str|None:
		"""
		Retrieves recording information by name.

		Args:
			name: The name of the recording.

		Returns:
			The recording information.
		"""
		try:
			result = self.musicbrainz.search_recordings(name=name)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_release_by_name(self, name:str) -> str|None:
		"""
		Retrieves release information by name.

		Args:
			name: The name of the release.

		Returns:
			The release information.
		"""
		try:
			result = self.musicbrainz.search_releases(name=name)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_track_by_audio_fingerprint(self, fingerprint:str) -> str|None:
		"""
		Retrieves track information by audio fingerprint.

		Args:
			fingerprint: The audio fingerprint of the track.

		Returns:
			The track information.
		"""
		try:
			result = self.musicbrainz.search_recordings(fingerprint=fingerprint)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_release_by_audio_fingerprint(self, fingerprint:str) -> str|None:
		"""
		Retrieves release information by audio fingerprint.

		Args:
			fingerprint: The audio fingerprint of the release.

		Returns:
			The release information.
		"""
		try:
			result = self.musicbrainz.search_releases(fingerprint=fingerprint)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None

	def get_recording_by_audio_fingerprint(self, fingerprint:str) -> str|None:
		"""
		Retrieves recording information by audio fingerprint.

		Args:
			fingerprint: The audio fingerprint of the recording.

		Returns:
			The recording information.
		"""
		try:
			result = self.musicbrainz.search_recordings(fingerprint=fingerprint)
			return result
		except musicbrainzngs.ResponseError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
		except musicbrainzngs.NetworkError as e:
			self.logger.error(f"Network error retrieving release: {e}")
			return None
		except musicbrainzngs.WebServiceError as e:
			self.logger.error(f"Error retrieving release: {e}")
			return None
