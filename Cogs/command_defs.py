import aiohttp

class CmdDefs:
    @staticmethod
    async def fetch_image(session, url, timeout=20):
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            if resp.status != 200:
                return None, resp.status
            data = await resp.read()
            return data, None

    @staticmethod
    def get_file_extension(url):
        ext = url.split(".")[-1].split("?")[0].lower()
        return ext if ext in ("png", "jpg", "jpeg", "gif", "webp") else "png"

cmd_def = CmdDefs()