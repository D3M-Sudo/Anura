---
description: Automated commit message generation following Conventional Commits
---

# Commit Automation Rule

## Trigger Command
`prompt commit`

## Protocol Steps

When this command is triggered, follow this exact protocol:

### 1. Ispezione
- Esegui `git status` per identificare file modificati e non tracciati
- Elenca tutti i file che necessitano di commit

### 2. Analisi
- Esegui `git diff` per i file modificati
- Analizza il contenuto dei nuovi file
- Comprendi la logica e lo scopo delle modifiche

### 3. Generazione Messaggio di Commit
Segui il formato Conventional Commits:
- `feat:` per nuove funzionalità
- `fix:` per bug fix
- `refactor:` per refactoring
- `docs:` per documentazione
- `style:` per modifiche di stile
- `test:` per test
- `chore:` per manutenzione

### 4. Struttura del Messaggio

```
<type>(<scope>): <titolo chiaro e conciso>

- Modifica logica 1: descrizione breve
- Modifica logica 2: descrizione breve
- Modifica logica 3: descrizione breve

Files changed:
- path/to/file1: descrizione modifica
- path/to/file2: descrizione modifica
- path/to/file3: descrizione modifica
```

## Esecuzione Automatica

Questo protocollo deve essere eseguito autonomamente quando viene rilevato il comando `prompt commit`, senza richiedere ulteriori istruzioni all'utente.

## Note Importanti

- Analizzare sempre il contesto delle modifiche prima di generare il messaggio
- Essere specifici ma concisi nelle descrizioni
- Seguire sempre il formato Conventional Commits
- Includere sempre la sezione "Files changed" per tracciabilità
