# Multiplayerová Hra - Redis a Mongo, FastAPI + Flask?

## Instalace

1. **Verze Pythonu**: 3.11. (testovano na 3.11.2)
   
2. **Virtuální prostředí**:
   - virtuální prostředí a nainstaluj potřebné závislosti:
     ```bash
     pip install -r requirements.txt
     ```

3. **Nastavení Redis**:
   - konfiguračního soubor `redis.conf`

## Co už máme hotové

- **Herní server**: Plně funkční server pro multiplayerovou hru, který zvládá všechny základní operace.
- **Arcade klient**: Herní klient, který se dokáže připojit k serveru.
- **Správa relací (sessions)**: Každá herní relace je ověřována pomocí Redis databáze.
  - Redis ukládá relace ve formátu: `"user_session_id": "player_id"`, což zajišťuje rychlou a efektivní správu připojení hráčů.

## Co je ještě potřeba udělat

- **Integrace MongoDB**:
  - Ukládat data hráčů do MongoDB ve formátu: `"player_id": player_data`.
  - Při připojení hráče automaticky načíst jeho data z MongoDB.
  - Implementovat periodické zálohování dat z paměti do MongoDB, aby nedocházelo ke ztrátě dat.

- **Uživatelský klient**:
  - Vytvořit samostatný klient, který by umožnil hráčům spravovat své účty mimo hru. Plánujeme, že tento klient umožní:
    - Autorizace jmeno:heslo.  
    - Kupovat upgrady.
    - Spravovat seznam přátel.
    - Marketplace??
    - atd atd idk 
