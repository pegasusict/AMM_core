# audioutils/dedupe.py

from ..core.decorators import register_audioutil
from ..core.enums import CodecPriority


@register_audioutil
async def dedupe_files(files: list) -> dict:
    """
    Given a list of file objects, returns:
        {
            "keep": file,
            "delete": [file, file, ...]
        }

    Sorts by codec priority & bitrate.
    """

    if len(files) <= 1:
        return {"keep": files[0] if files else None, "delete": []}

    # Highest quality first
    sorted_files = sorted(
        files,
        key=lambda f: (CodecPriority[f.codec], f.bitrate),
        reverse=True,
    )

    return {
        "keep": sorted_files[0],
        "delete": sorted_files[1:],
    }
