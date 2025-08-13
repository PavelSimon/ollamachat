# Requirements Document

## Introduction

Vývoj jednoduchej webovej aplikácie pre komunikáciu s lokálnym OLLAMA modelom. Aplikácia bude poskytovať chat rozhranie podobné Claude.ai s možnosťou správy používateľov, chatov a komunikácie s rôznymi AI modelmi cez OLLAMA API.

## Requirements

### Requirement 1

**User Story:** Ako používateľ chcem sa prihlásiť do aplikácie pomocou emailu a hesla, aby som mal prístup k svojmu vlastnému dátovému priestoru.

#### Acceptance Criteria

1. WHEN používateľ zadá platný email a heslo THEN systém SHALL umožniť prihlásenie a presmerovať na hlavnú stránku
2. WHEN používateľ zadá neplatné prihlasovacie údaje THEN systém SHALL zobraziť chybovú správu
3. WHEN používateľ nie je prihlásený THEN systém SHALL presmerovať na prihlasovaciu stránku
4. WHEN používateľ sa úspešne prihlási THEN systém SHALL vytvoriť bezpečnú session
5. IF používateľ nemá účet THEN systém SHALL umožniť registráciu s emailom a heslom

### Requirement 2

**User Story:** Ako prihlásený používateľ chcem mať možnosť konfigurovať OLLAMA server adresu a port, aby som sa mohol pripojiť k rôznym OLLAMA inštanciám.

#### Acceptance Criteria

1. WHEN používateľ otvorí nastavenia THEN systém SHALL zobraziť aktuálnu OLLAMA server adresu a port
2. WHEN používateľ zmení server adresu alebo port THEN systém SHALL uložiť nové nastavenia
3. WHEN systém sa pokúša pripojiť k OLLAMA serveru THEN systém SHALL použiť nakonfigurovanú adresu a port
4. IF pripojenie k OLLAMA serveru zlyhá THEN systém SHALL zobraziť chybovú správu
5. WHEN aplikácia štartuje THEN systém SHALL použiť predvolenú adresu http://192.168.1.23:11434

### Requirement 3

**User Story:** Ako používateľ chcem vidieť zoznam dostupných OLLAMA modelov a mať možnosť ich meniť, aby som mohol komunikovať s rôznymi AI modelmi.

#### Acceptance Criteria

1. WHEN aplikácia štartuje THEN systém SHALL načítať zoznam dostupných modelov z OLLAMA servera
2. WHEN používateľ otvorí výber modelu THEN systém SHALL zobraziť aktuálne dostupné modely
3. WHEN používateľ vyberie iný model THEN systém SHALL prepnúť na vybraný model pre ďalšiu komunikáciu
4. WHEN sa pripojenie k OLLAMA serveru zmení THEN systém SHALL aktualizovať zoznam dostupných modelov
5. IF žiadne modely nie sú dostupné THEN systém SHALL zobraziť informačnú správu

### Requirement 4

**User Story:** Ako používateľ chcem mať možnosť začať nový chat a vidieť históriu svojich chatov, aby som mohol organizovať svoje konverzácie.

#### Acceptance Criteria

1. WHEN používateľ klikne na "Nový chat" THEN systém SHALL vytvoriť nový prázdny chat
2. WHEN používateľ má aktívne chaty THEN systém SHALL zobraziť zoznam chatov v bočnom paneli
3. WHEN používateľ klikne na existujúci chat THEN systém SHALL načítať a zobraziť históriu konverzácie
4. WHEN používateľ vytvorí nový chat THEN systém SHALL automaticky prepnúť na tento chat
5. WHEN používateľ má viacero chatov THEN systém SHALL označiť aktuálne aktívny chat

### Requirement 5

**User Story:** Ako používateľ chcem posielať správy AI modelu a dostávať odpovede v reálnom čase, aby som mohol viesť prirodzenú konverzáciu.

#### Acceptance Criteria

1. WHEN používateľ napíše správu a stlačí Enter alebo klikne odoslať THEN systém SHALL odoslať správu k OLLAMA modelu
2. WHEN systém dostane odpoveď od modelu THEN systém SHALL zobraziť odpoveď v chat okne
3. WHEN prebieha komunikácia s modelom THEN systém SHALL zobraziť indikátor načítavania
4. WHEN komunikácia s modelom zlyhá THEN systém SHALL zobraziť chybovú správu
5. WHEN používateľ pošle správu THEN systém SHALL uložiť správu aj odpoveď do databázy

### Requirement 6

**User Story:** Ako používateľ chcem aby sa všetky moje chaty a správy ukladali do databázy, aby som mal trvalý prístup k histórii konverzácií.

#### Acceptance Criteria

1. WHEN používateľ pošle správu THEN systém SHALL uložiť správu do SQLite databázy
2. WHEN systém dostane odpoveď od AI modelu THEN systém SHALL uložiť odpoveď do databázy
3. WHEN používateľ sa prihlási THEN systém SHALL načítať iba jeho vlastné chaty a správy
4. WHEN používateľ vytvorí nový chat THEN systém SHALL vytvoriť nový záznam v databáze
5. IF databáza neexistuje THEN systém SHALL vytvoriť potrebné tabuľky pri prvom spustení

### Requirement 7

**User Story:** Ako používateľ chcem mať jednoduché a responzívne používateľské rozhanie s minimálnym CSS a JavaScript, aby aplikácia bola rýchla a ľahko použiteľná.

#### Acceptance Criteria

1. WHEN používateľ otvorí aplikáciu THEN systém SHALL zobraziť čisté a jednoduché rozhranie
2. WHEN používateľ používa aplikáciu na mobile zariadení THEN rozhranie SHALL byť responzívne
3. WHEN sa stránka načítava THEN systém SHALL minimalizovať použitie JavaScript knižníc
4. WHEN používateľ interaguje s rozhraním THEN odpovede SHALL byť rýchle bez zbytočných animácií
5. WHEN aplikácia beží THEN systém SHALL používať minimálne CSS štýly pre základnú funkčnosť