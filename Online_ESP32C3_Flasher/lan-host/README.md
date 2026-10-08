# Lokal PS4-host

Adress: **http://192.168.32.88:8088**

Anslut PS4 till samma vanliga hemnätverk som datorn och öppna adressen i
PS4-webbläsaren. Spara gärna ett bokmärke. Automatisk IP och DNS kan behållas.
Användarhandboken kräver den separata DNS-installationen nedan. Android kan visa
”unsupported”; själva jailbreaket kräver en kompatibel PS4.

Hosten använder samma 15 oförändrade tillgångar för 13.52 som ESP32-bygget.
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

## Användarhandboken (förberett, kräver installation)

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
har validerats. Installation på port 53/80 och fysiskt PS4-test återstår.
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

Fyra integrationstester har passerat, inklusive samtliga 15 tillgångars
hashar, komprimering, routning och sparad telemetri. Den körande tjänsten har
också kontrollerats via datorns LAN-adress. Detta ersätter inte ett test från
en fysisk PS4 över hemnätverket.

Kör tester från denna katalog:

```sh
python3 -m unittest discover -s tests -v
```
