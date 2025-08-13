# Implementation Plan

- [x] 1. Nastavenie projektu a základnej štruktúry



  - Vytvorenie pyproject.toml s potrebnými závislosťami (Flask, SQLAlchemy, Flask-Login, requests)
  - Vytvorenie základnej štruktúry adresárov (templates, static, instance)
  - Inicializácia Flask aplikácie s základnou konfiguráciou
  - Pridanie databázy a instance/ adresára do .gitignore
  - Vytvorenie README.md s inštrukciami pre uv
  - _Requirements: 7.1, 7.3_

- [-] 2. Implementácia databázových modelov

- [-] 2.1 Vytvorenie základných databázových modelov


  - Implementácia User, Chat, Message a UserSettings modelov pomocou SQLAlchemy
  - Definovanie vzťahov medzi modelmi (foreign keys, relationships)
  - Vytvorenie databázovej inicializácie a migračných skriptov
  - _Requirements: 6.1, 6.2, 6.4, 6.5_


- [x] 2.2 Implementácia databázových operácií


  - Vytvorenie CRUD operácií pre všetky modely
  - Implementácia metód pre načítanie používateľských dát s izolovaním
  - Napísanie unit testov pre databázové operácie
  - _Requirements: 6.3, 1.4_

- [ ] 3. Implementácia autentifikačného systému
- [ ] 3.1 Vytvorenie registračných a prihlasovacích formulárov
  - Implementácia WTForms pre registráciu a prihlásenie
  - Pridanie validácie emailu a hesla
  - Vytvorenie Jinja2 templates pre login a register stránky
  - _Requirements: 1.1, 1.2, 1.5_

- [ ] 3.2 Implementácia autentifikačnej logiky
  - Integrácia Flask-Login pre session management
  - Implementácia password hashing pomocou Werkzeug
  - Vytvorenie login/logout routes s bezpečnostnými kontrolami
  - Napísanie testov pre autentifikačný flow
  - _Requirements: 1.1, 1.3, 1.4_

- [ ] 4. Vytvorenie OLLAMA API klienta
- [ ] 4.1 Implementácia OllamaClient triedy
  - Vytvorenie triedy pre komunikáciu s OLLAMA API
  - Implementácia metód get_models() a chat() pomocou requests library
  - Pridanie error handling pre connection timeouts a invalid responses
  - _Requirements: 3.1, 3.4, 5.4_

- [ ] 4.2 Testovanie OLLAMA integrácie
  - Napísanie unit testov s mock OLLAMA responses
  - Implementácia test_connection() metódy
  - Vytvorenie integration testov pre API komunikáciu
  - _Requirements: 3.1, 3.4_

- [ ] 5. Implementácia používateľských nastavení
- [ ] 5.1 Vytvorenie settings management
  - Implementácia UserSettings modelu s OLLAMA host konfiguráciou
  - Vytvorenie settings formulára a template
  - Implementácia routes pre načítanie a uloženie nastavení
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [ ] 5.2 Integrácia nastavení s OLLAMA klientom
  - Prepojenie používateľských nastavení s OllamaClient
  - Implementácia dynamického načítavania modelov pri zmene servera
  - Pridanie validácie server adresy a portu
  - Napísanie testov pre settings funkcionalitu
  - _Requirements: 2.3, 2.4, 3.4_

- [ ] 6. Implementácia chat management systému
- [ ] 6.1 Vytvorenie chat CRUD operácií
  - Implementácia API endpoints pre vytvorenie, načítanie a mazanie chatov
  - Vytvorenie metód pre načítanie používateľských chatov
  - Implementácia automatického generovania chat titulkov
  - _Requirements: 4.1, 4.2, 4.4, 6.4_

- [ ] 6.2 Implementácia správy správ
  - Vytvorenie API endpoint pre posielanie správ
  - Implementácia ukladania user a AI správ do databázy
  - Vytvorenie metód pre načítanie chat histórie
  - Napísanie testov pre chat a message operácie
  - _Requirements: 5.5, 6.1, 6.2_

- [ ] 7. Vytvorenie hlavného chat rozhrania
- [ ] 7.1 Implementácia chat UI template
  - Vytvorenie base.html template s responzívnym layoutom
  - Implementácia chat.html template s bočným panelom pre chaty
  - Pridanie minimálneho CSS pre základné štýlovanie
  - _Requirements: 7.1, 7.2, 7.5_

- [ ] 7.2 Implementácia JavaScript funkcionalite
  - Vytvorenie vanilla JavaScript pre posielanie správ
  - Implementácia real-time aktualizácie chat rozhrania
  - Pridanie loading indikátorov a error handling
  - _Requirements: 5.1, 5.3, 7.3, 7.4_

- [ ] 8. Implementácia model selection funkcionalite
- [ ] 8.1 Vytvorenie model picker UI
  - Pridanie dropdown menu pre výber modelov do chat template
  - Implementácia API endpoint pre načítanie dostupných modelov
  - Vytvorenie JavaScript logiky pre prepínanie modelov
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 8.2 Integrácia model selection s chat systémom
  - Prepojenie vybraného modelu s posielaním správ
  - Implementácia ukladania použitého modelu do message záznamu
  - Pridanie automatického refresh modelov pri zmene nastavení
  - Napísanie testov pre model selection funkcionalitu
  - _Requirements: 3.3, 3.4, 5.5_

- [ ] 9. Implementácia kompletného chat flow
- [ ] 9.1 Prepojenie všetkých komponentov
  - Integrácia autentifikácie s chat rozhraním
  - Prepojenie OLLAMA klienta s chat API endpoints
  - Implementácia kompletného flow od prihlásenia po chat komunikáciu
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [ ] 9.2 Finálne testovanie a optimalizácia
  - Vytvorenie end-to-end testov pre celý používateľský flow
  - Optimalizácia databázových queries s indexami
  - Testovanie responzívnosti na rôznych zariadeniach
  - Implementácia error handling pre všetky edge cases
  - _Requirements: 4.3, 7.2, 7.4_

- [ ] 10. Deployment príprava
  - Vytvorenie production konfigurácie s environment variables
  - Implementácia database initialization scriptu
  - Vytvorenie dokumentácie pre spustenie aplikácie
  - Pridanie základných security headers a CSRF protection
  - _Requirements: 1.4, 6.5_