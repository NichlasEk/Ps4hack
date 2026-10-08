# Lokal PS4-host

Adress: **http://192.168.32.88:8088**

Anslut PS4 till samma vanliga hemnätverk som datorn och öppna adressen i
PS4-webbläsaren. Spara gärna ett bokmärke. Automatisk IP och DNS kan behållas.
Användarhandboken kräver den separata DNS-installationen nedan. Android kan visa
”unsupported”; själva jailbreaket kräver en kompatibel PS4.

Hosten väljer sida efter PS4:ans firmware: **9.60** använder CSSFontFace/Lapse,
och **13.02, 13.04, 13.50, 13.52** använder den befintliga 13.xx-sidan.
Övriga versioner får en informationssida. En PS4 med fel firmware nekas
åtkomst till den andra versionens filer, även via en direktlänk.

På 9.60-sidan: välj **Lapse** och tryck **Jeilbrek**. Inget PPPwn-steg eller
firmwarebyte behövs för den här vägen. Fysiskt genomförande på 9.60 återstår
att verifiera. 12.xx-konsolens BD-upplägg berörs inte.

Hosten använder samma 15 oförändrade tillgångar för 13.52 som ESP32-bygget,
samt 30 tillgångar ur samma upstream-binär för 9.60. `extract_960.py` verifierar
binärens SHA-256 och hela cachemanifestets filuppsättning. Skript och patchar
har matchats byte för byte mot originalets Arduino-headerfiler. Originalets
versionsuppslag väljer `950.bin` även för 9.60, vilket har kontrollerats genom
att köra enbart konstantuppslaget i Node. GoldHEN-payloaden är originalets
293120 byte och matchar byte för byte den som medföljer 13.xx-paketet.
De återskapas och kontrolleras från den medföljande upstream-binären vid start.
Git behövs inte för drift, men behåll även katalogen `../esp32-1352/` och
upstream-binären i `../goldhen24b1812/bins/` vid flytt eller säkerhetskopiering.

## Automatisk start

Användartjänsten `ps4-lan-host.service` är installerad i
`~/.config/systemd/user/` och aktiverad. Användarens linger är aktiverat,
så tjänsten kan starta vid uppbootning utan inloggning. Datorn måste vara på.

```sh
systemctl --user status ps4-lan-host.service
systemctl --user restart ps4-lan-host.service
systemctl --user stop ps4-lan-host.service
journalctl --user -u ps4-lan-host.service -n 50
```

Tjänsten lyssnar på IPv4-adressen `192.168.32.88`, port `8088`.
Om datorns adress ändras behöver tjänstens bind-adress uppdateras.
Inga router-, brandväggs- eller DNS-inställningar har ändrats.

## Användarhandboken

Kör i en lokal terminal:

```sh
sudo sh /home/nichlas/Ps4hack/Online_ESP32C3_Flasher/lan-host/install-guide.sh
```

Det installerar separata systemtjänster för DNS på `192.168.32.88:53` och
HTTP på `192.168.32.88:80`, med automatisk start. Befintlig host på 8088
fortsätter användas bakom HTTP-vidarebefordringen. `dnsmasq` måste finnas.
Endast `manuals.playstation.net` omdirigeras; övriga DNS-frågor skickas till
routern `192.168.32.1`. Det är inte ett filter för systemuppdateringar.

Efter lyckad installation: konfigurera PS4:s vanliga nätverksanslutning med
automatisk IP, manuell DNS och **192.168.32.88 som både primär och sekundär
DNS**. Behåll automatisk MTU och ingen proxy. Öppna sedan
**Inställningar → Användarhandbok/Användbar information → Användarhandbok**.
DNS-inställningen påverkar bara PS4; datorn måste vara på även för dess
vanliga namnuppslagning. Återställ automatisk DNS för att ångra på konsolen.

DNS har provkörts utan administratörsrättigheter på testport 1053:
handbokens IPv4-adress omdirigeras, IPv6-svar undertrycks för samma domän,
och andra domäner slås upp via routern. Konfiguration och systemd-enheter
har validerats. Systemtjänsterna är nu aktiva på denna dator. Versionsval och
hämtning av båda startsidorna genom port 80 har verifierats med simulerade
PS4-användaragenter. Fysiskt PS4-test av 9.60 återstår.
HTTP-proxyn gör att HTTP-loggen ser datorns IP som klient; användaragent
och jailbreaktelemetri bevaras.

Avinstallera startkopplingen med:

```sh
sudo systemctl disable --now ps4-guide-dns.service ps4-guide-http.socket
sudo systemctl stop ps4-guide-http.service
```

## Loggar och kontroll

`logs/` innehåller dagliga JSONL-filer för HTTP-anrop, serverhändelser och
jailbreakets `/t`-telemetri. Loggarna sparas mellan tjänstens omstarter.
Tidsstämplarna är i UTC. Lokala kontrollanrop har användaragenten
`PS4LANHost-LocalValidation/1` och telemetritaggen `HOST-SELFTEST`.

Sex integrationstester har passerat, inklusive samtliga 45 tillgångars
hashar, komprimering, versionsval, felversion, cache och sparad telemetri.
9.60-originalet visar sin körlogg på skärmen och skickar inte `/t`-telemetri;
servern sparar dess HTTP-anrop. Den körande tjänsten har
också kontrollerats via datorns LAN-adress. Detta ersätter inte ett test från
en fysisk PS4 över hemnätverket.

Kör tester från denna katalog:

```sh
python3 -m unittest discover -s tests -v
```
