
import ee
import xmltodict
import aiohttp
from app.config import env, logger
async def check_gee() -> str:
    try:
        # Teste com um asset real e existente
        test_collection = (
            ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1")
            .filterDate("2020-01-01", "2020-12-31")
            .limit(1)
        )
        test_collection.size().getInfo()  # força avaliação
        return "connected"
    except Exception as e:
        logger.warning("Erro ao conectar ao GEE: %s", e, exc_info=True)
        return "error"

def check_valkey(valkey_client) -> str:
    try:
        pong = valkey_client.ping()

        return "connected" if pong else "error"
    except Exception as e:
        logger.warning(f"Erro ao conectar ao Valkey: {e}", e)
        return "error"

async def check_planet() -> str:
    try:
        planet_url = env.get("PLANET_WMS_URL")
        planet_auth = env.get("PLANET_AUTH_TOKEN")
        url = f"{planet_url}?SERVICE=WMS&REQUEST=GetCapabilities"
        headers = {
            "Authorization": f"Basic {planet_auth}",
            "User-Agent": "Mozilla/5.0 QGIS/33415/Linux",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logger.error(f"Planet GetCapabilities falhou ({response.status})")
                    return f"error ({response.status})"

                xml_text = await response.text()
                xmltodict.parse(xml_text)  # validando o XML
                return "connected"
    except Exception as e:
        logger.warning("Erro ao verificar Planet WMS: %s", e)
        return "error"
