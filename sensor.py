from datetime import date, datetime
import json
import logging
import os

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "veres_hulladek"


def get_current_year_json_path(hass: HomeAssistant) -> str:
    """Visszaadja az aktuális évnek megfelelő JSON fájl elérési útját."""
    current_year = date.today().year
    return hass.config.path(
        "custom_components", DOMAIN, "config", f"{current_year}.json"
    )


def load_schedule_from_json(json_path: str) -> dict:
    """JSON fájl biztonságos beolvasása a háttérszálon."""
    if not os.path.exists(json_path):
        _LOGGER.warning("A hulladéknaptár JSON fájl nem található: %s", json_path)
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        _LOGGER.error("Hiba a hulladéknaptár JSON beolvasásakor (%s): %s", json_path, err)
        return {}


def parse_dates(date_list: list) -> list:
    """Dátum karakterláncok konvertálása date objektumokká és rendezése."""
    parsed = []
    for d_str in date_list:
        try:
            parsed.append(datetime.strptime(d_str, "%Y-%m-%d").date())
        except ValueError:
            _LOGGER.warning("Érvénytelen dátumformátum a JSON-ban: %s", d_str)
            continue
    return sorted(parsed)


def get_next_date(dates: list, today: date):
    """Visszaadja a legközelebbi jövőbeli vagy mai dátumot."""
    for d in dates:
        if d >= today:
            return d
    return None


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Szenzorok inicializálása."""
    async_add_entities([
        VeresHulladekNextSensor(),
        VeresHulladekCategorySensor("szelektiv", "Következő Szelektív Gyűjtés", "mdi:recycle"),
        VeresHulladekCategorySensor("zoldhulladek", "Következő Zöldhulladék Gyűjtés", "mdi:leaf"),
        VeresHulladekCategorySensor("kommunalis", "Következő Kommunális Gyűjtés", "mdi:trash-can"),
    ])


class VeresHulladekBaseSensor(SensorEntity):
    """Alaposztály az adatok dinamikus beolvasásához az aktuális év JSON fájljából."""

    def __init__(self):
        self._schedule_data = {}

    async def _async_load_data(self):
        """Aszinkron hívás a JSON fájl beolvasására az aktuális év alapján."""
        json_path = get_current_year_json_path(self.hass)
        self._schedule_data = await self.hass.async_add_executor_job(
            load_schedule_from_json, json_path
        )


class VeresHulladekNextSensor(VeresHulladekBaseSensor):
    """Szenzor, ami megadja a legközelebbi gyűjtési napot és az extra hulladék típusát."""

    def __init__(self):
        super().__init__()
        self._attr_name = "Következő Hulladékszállítás"
        self._attr_unique_id = "veres_hulladek_next"
        self._attr_icon = "mdi:truck-cargo-empty"
        self._state = None
        self._attributes = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        await self._async_load_data()
        today = date.today()
        upcoming = []

        cat_names = {
            "szelektiv": "Szelektív",
            "zoldhulladek": "Zöldhulladék",
            "fenyo": "Fenyő",
        }

        for cat, dates_str in self._schedule_data.items():
            dates = parse_dates(dates_str)
            nxt = get_next_date(dates, today)
            if nxt:
                upcoming.append((nxt, cat))

        if upcoming:
            upcoming.sort(key=lambda x: x[0])
            next_date, _ = upcoming[0]

            # Kiválogatjuk az aznapi kategóriákat, de a kommunálist kihagyjuk a megjelenítésből
            same_day_types = [cat for d, cat in upcoming if d == next_date and cat != "kommunalis"]
            
            days_left = (next_date - today).days

            if same_day_types:
                types_formatted = ", ".join([cat_names.get(c, c) for c in same_day_types])
                self._state = f"{next_date.strftime('%Y-%m-%d')} ({types_formatted})"
            else:
                self._state = next_date.strftime("%Y-%m-%d")

            self._attributes = {
                "datum": next_date.strftime("%Y-%m-%d"),
                "extra_tipusok": [cat_names.get(c, c) for c in same_day_types],
                "napok_mulva": days_left,
                "ma_van": days_left == 0,
            }
        else:
            self._state = "Nincs megadva adat"
            self._attributes = {}


class VeresHulladekCategorySensor(VeresHulladekBaseSensor):
    """Szenzor egy adott kategória (szelektív, zöld, kommunális) következő dátumára."""

    def __init__(self, category: str, name: str, icon: str):
        super().__init__()
        self._category = category
        self._attr_name = name
        self._attr_unique_id = f"veres_hulladek_{category}"
        self._attr_icon = icon
        self._state = None
        self._attributes = {}

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        await self._async_load_data()
        today = date.today()

        if self._category == "zoldhulladek":
            dates_str = self._schedule_data.get("zoldhulladek", []) + self._schedule_data.get("fenyo", [])
        else:
            dates_str = self._schedule_data.get(self._category, [])

        dates = parse_dates(dates_str)
        nxt = get_next_date(dates, today)

        if nxt:
            days_left = (nxt - today).days
            self._state = nxt.strftime("%Y-%m-%d")
            self._attributes = {
                "napok_mulva": days_left,
                "ma_van": days_left == 0,
            }
        else:
            self._state = "Nincs adat"
            self._attributes = {}