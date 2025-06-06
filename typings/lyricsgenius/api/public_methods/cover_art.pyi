"""
This type stub file was generated by pyright.
"""

class CoverArtMethods:
    """Cover art methods of the public API."""
    def cover_arts(self, album_id=..., song_id=..., text_format=...):
        """Gets the cover arts of an album or a song.

        You must supply one of :obj:`album_id` or :obj:`song_id`.

        Args:
            album_id (:obj:`int`, optional): Genius album ID
            song_id (:obj:`int`, optional): Genius song ID
            text_format (:obj:`str`, optional): Text format of the results
                ('dom', 'html', 'markdown' or 'plain'). Defines the text
                formatting for the annotation of the cover arts,
                if there are any.

        Returns:
            :obj:`dict`

        """
        ...
