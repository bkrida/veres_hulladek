# 🗑️ Veresegyház Hulladéknaptár

**Home Assistant custom component** a veresegyházi hulladéknaptár kezeléséhez.

> Ez az integráció segít nyomon követni a verschiedens hulladékszállítási naptárakat Veresegyházon, és automatikus értesítéseket küldhet a közelgő szállítási dátumokról.

## 📋 Jellemzők

- **Következő hulladékszállítás követése**: Megjeleníti a legközelebbi szállítási dátumot az összes kategóriára
- **Kategóriánként részletes szenzorok**: 
  - Szelektív gyűjtés
  - Zöldhulladék gyűjtés
  - Kommunális gyűjtés
- **Attribútumok**: 
  - Pontos dátum (`datum`)
  - Hátralévő napok száma (`napok_mulva`)
  - Mai szállítás-e? (`ma_van`)
  - Extra hulladéktípusok (`extra_tipusok`)
- **JSON alapú konfigurálás**: Egyszerű JSON fájlok tárolják az éves szállítási naptárat
- **Helyi feldolgozás**: Nem szükséges internet kapcsolat (iot_class: local_polling)

## 🔧 Telepítés

### 1. Fájlok másolása

A Home Assistant `custom_components` mappájába másold be a komponenst:

```
.homeassistant/
└── custom_components/
    └── veres_hulladek/
        ├── __init__.py
        ├── sensor.py
        ├── manifest.json
        └── config/
            └── 2024.json
            └── 2025.json
            └── 2026.json
```

### 2. Naptár adatok feltöltése

Szükséges egy JSON fájl az aktuális évhez a `config/` mappában. Formátuma:

**config/2024.json** (és további évek):
```json
{
  "szelektiv": [
    "2024-01-11",
    "2024-01-25",
    "2024-02-08"
  ],
  "zoldhulladek": [
    "2024-03-14",
    "2024-04-18"
  ],
  "fenyo": [
    "2024-01-10"
  ],
  "kommunalis": [
    "2024-01-04",
    "2024-01-11"
  ]
}
```

### 3. Home Assistant konfigurációja

Az `configuration.yaml` fájlban add hozzá:

```yaml
sensor:
  - platform: veres_hulladek
```

### 4. Home Assistant újraindítása

```bash
docker restart homeassistant
# vagy
systemctl restart homeassistant
```

## 📊 Elérhető szenzorok

Az integráció automatikusan létrehozza az alábbi szenzorókat:

| Szenzor | Egyedi ID | Leírás |
|---------|-----------|--------|
| Következő Hulladékszállítás | `sensor.veres_hulladek_next` | A legközelebbi szállítás összes kategóriára |
| Szelektív Gyűjtés | `sensor.veres_hulladek_szelektiv` | Szelektív szállítás következő dátuma |
| Zöldhulladék Gyűjtés | `sensor.veres_hulladek_zoldhulladek` | Zöld hulladék szállítás (zöldhulladék + fenyő) |
| Kommunális Gyűjtés | `sensor.veres_hulladek_kommunalis` | Kommunális hulladék szállítás |

## 🎯 Szenzor attribútumok

### `sensor.veres_hulladek_next`

```yaml
- state: "2024-01-11 (Szelektív, Fenyő)"
  attributes:
    datum: "2024-01-11"
    extra_tipusok: ["Szelektív", "Fenyő"]
    napok_mulva: 3
    ma_van: false
```

### Kategória szenzorok (pl. `sensor.veres_hulladek_szelektiv`)

```yaml
- state: "2024-01-11"
  attributes:
    napok_mulva: 3
    ma_van: false
```

## 🏠 Automatizálás példa

Értesítés küldése a nap elején, ha szállítás van:

```yaml
automation:
  - alias: "Hulladékszállítás emlékeztetõ"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      condition: state
      entity_id: sensor.veres_hulladek_next
      state: "true"
      attribute: ma_van
    action:
      - service: notify.notify
        data:
          title: "Hulladékszállítás ma!"
          message: "{{ state_attr('sensor.veres_hulladek_next', 'extra_tipusok') | join(', ') }} szállítás mai napon"
```

## 📁 Projekt szerkezete

```
veres_hulladek/
├── __init__.py              # Integráció inicializálása
├── sensor.py                # Szenzor logika
├── manifest.json            # Metaadatok
├── config/
│   ├── 2024.json           # 2024-es hulladéknaptár
│   ├── 2025.json           # 2025-ös hulladéknaptár
│   └── 2026.json           # 2026-os hulladéknaptár
└── README.md               # Ez a fájl
```

## 🔍 Hibakeresés

### A szenzor "Nincs megadva adat" értéket mutat

- Ellenőrizd, hogy a megfelelő év JSON fájlja létezik-e a `config/` mappában
- Valósítsd meg, hogy a JSON formátuma helyes-e

### A Home Assistant nem találja az integrációt

- Indítsd újra a Home Assistant-ot
- Ellenőrizd a `custom_components` mappa szerkezetét

### Dátumok nincsenek felismerve

- A JSON fájlban a dátumok `YYYY-MM-DD` formátumban kell legyenek
- Ellenőrizd az `homeassistant.log` fájlt a részletekért

## 📝 Verzió

- **Aktuális verzió**: 1.0.0
- **Home Assistant minimális verziója**: 2021.8+
- **Licenc**: MIT

## 👨‍💻 Fejlesztő

- [@bkrida](https://github.com/bkrida)

## 📄 Licenc

Ez a projekt az MIT Licenc alatt áll. Lásd a [LICENSE](LICENSE) fájlt a részletekért.

## 💬 Támogatás

Hibák bejelentéséhez vagy feature kérésekhez nyiss egy [GitHub Issue-t](https://github.com/bkrida/veres_hulladek/issues).

---

**Készült a veresegyházi közösség számára** 🏘️
