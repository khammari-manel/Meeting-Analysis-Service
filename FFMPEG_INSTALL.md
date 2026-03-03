# ffmpeg Installation für Whisper (Deutsch)

Lokales Whisper benötigt ffmpeg für Audio-Dekodierung.

## ⚡ Schnellste Methode: Chocolatey (mit Admin)

1. **PowerShell als Administrator öffnen** (Rechtsklick → "Als Administrator ausführen")
2. Befehl ausführen:
```powershell
choco install ffmpeg -y
```
3. PowerShell neu starten und testen:
```powershell
ffmpeg -version
```

## 🔄 Alternative 1: winget (mit Admin)

1. **PowerShell als Administrator öffnen**
2. Befehl ausführen:
```powershell
winget install ffmpeg
```
3. PowerShell neu starten

## 📦 Alternative 2: Manueller Download (ohne Admin möglich)

1. Gehe zu: https://github.com/BtbN/FFmpeg-Builds/releases
2. Download: **ffmpeg-master-latest-win64-gpl.zip** (~100MB)
3. Entpacke nach: `C:\ffmpeg\`
4. Füge zu PATH hinzu:
   - Windows-Suche: "Umgebungsvariablen"
   - Unter "Benutzervariablen" → PATH → Bearbeiten → Neu
   - Hinzufügen: `C:\ffmpeg\bin`
5. PowerShell neu starten und testen:
```powershell
ffmpeg -version
```

## ✅ Nach Installation

1. PowerShell NEU STARTEN (wichtig!)
2. Teste Whisper-Transkription im Browser
3. Erste Transkription: 1-2 Min (lädt Whisper Base-Modell, 140MB)
4. Danach: ~30-60 Sek pro Audio-Minute

## 🎤 Dann testen

- Upload Audio-Datei (MP3, WAV, M4A, max 25MB)
- Klick "Transkribieren & Analysieren"
- Warte auf Transkription (erste Mal länger)
- Ergebnis erscheint mit Action Items
